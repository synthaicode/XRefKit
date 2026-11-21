"""Resolve the current work record carried by an Issue, using existing stores."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from typing import Callable, Literal

from .issue_projection import (
    AtomicIssueWriter,
    DecisionRequest,
    IssueArchive,
    IssueSnapshot,
    PMState,
    ProjectionConflict,
    ProjectionError,
    ProjectionInput,
    ProjectedView,
    Readback,
    RecordPointer,
    ResolveRecord,
    UpdatePlan,
    VIEW_START,
    WriteReceipt,
    _Verified,
    _archived,
    _digest,
    _load,
    _render_verified,
    _require,
    _resolve,
    _text,
    _view_bounds,
    apply_update,
    prepare_create,
    prepare_update,
)


_MARKER = b"<!-- pm-work-record:"
_BLOCK = re.compile(rb"^" + re.escape(_MARKER) + rb"v1\r?\n([^\r\n]+)\r?\n-->(?=\r?$)", re.MULTILINE)
_LABELS = {
    "design": "Technical design",
    "contract": "Contract",
    "investigation": "Investigation",
    "verification": "Verification record",
}
ArtifactKind = Literal["design", "contract", "investigation", "verification"]
ResolveManagement = Callable[[Literal["project", "pm"], str], RecordPointer]


@dataclass(frozen=True)
class ArtifactReference:
    kind: ArtifactKind
    record: RecordPointer


@dataclass(frozen=True)
class ArtifactBinding:
    """Scope confirmed by the existing artifact owner or its trusted adapter."""

    issue_id: str
    kind: ArtifactKind
    scope: str
    xid: str | None = None
    status: Literal["current", "proposed", "verified"] = "current"


@dataclass(frozen=True)
class RecordedDecision:
    """The existing Decision record, including who made it and for what scope."""

    issue_id: str
    scope: str
    outcome: Literal["approved", "held", "rejected"]
    authority: str


@dataclass(frozen=True)
class IssueWorkRecord:
    issue_id: str
    purpose: str
    requirements: tuple[str, ...]
    acceptance: tuple[str, ...]
    dependencies: tuple[str, ...]
    project_locator: str
    pm_locator: str
    artifacts: tuple[ArtifactReference, ...]
    unknowns: tuple[str, ...] = ()
    stop_conditions: tuple[str, ...] = ()
    decisions: tuple[RecordPointer, ...] = ()
    decision_request: RecordPointer | None = None
    history: tuple[RecordPointer, ...] = ()


@dataclass(frozen=True)
class WorkHandoff:
    work: IssueWorkRecord
    inputs: ProjectionInput
    _verified: _Verified
    decisions: tuple[Readback, ...]
    history_links: tuple[str, ...]

    @property
    def execution(self) -> PMState:
        return self._verified.pm

    @property
    def decision_request(self) -> DecisionRequest | None:
        return self._verified.decision

    @property
    def artifacts(self) -> tuple[Readback, ...]:
        return self._verified.evidence


def _validate(work: IssueWorkRecord) -> None:
    for key in ("issue_id", "purpose", "project_locator", "pm_locator"):
        _text(getattr(work, key), key)
    for key in ("requirements", "acceptance", "dependencies", "unknowns", "stop_conditions"):
        values = getattr(work, key)
        _require(isinstance(values, tuple), f"{key}: tuple required")
        _require(key not in ("requirements", "acceptance") or bool(values), f"{key}: required")
        for value in values:
            _text(value, key)
    for field in ("artifacts", "decisions", "history"):
        _require(isinstance(getattr(work, field), tuple), f"{field}: tuple required")
    for artifact in work.artifacts:
        _require(isinstance(artifact, ArtifactReference) and artifact.kind in _LABELS, "invalid artifact kind")
    groups = {
        "technical": tuple(artifact.record for artifact in work.artifacts),
        "decision": work.decisions + ((work.decision_request,) if work.decision_request is not None else ()),
        "archive": work.history,
    }
    for role, records in groups.items():
        _require(all(isinstance(record, RecordPointer) and record.role == role for record in records),
                 f"{role}: invalid work record reference")
    references = [record for records in groups.values() for record in records]
    locators = [work.project_locator, work.pm_locator, *(record.locator for record in references)]
    _require(len(set(locators)) == len(locators),
             "work reference locators must be distinct")
    _require(not {record.sha256 for record in work.history}.intersection(
        record.sha256 for role in ("technical", "decision") for record in groups[role]
    ), "history cannot be an active record")


def _work_match(body: bytes) -> re.Match[bytes] | None:
    if _MARKER not in body:
        return None
    match = _BLOCK.search(body)
    bounds = _view_bounds(body)
    _require(match is not None and body.count(_MARKER) == 1 and bounds is not None
             and bounds[0] == 0 and bounds[1] < match.start()
             and not body[bounds[1]:match.start()].strip(b"\r\n"),
             "Issue must have one supported work record outside its opening Human View")
    return match


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
    value = dict(pairs)
    if len(value) != len(pairs):
        raise ValueError("duplicate work record keys")
    return value


def read_work_record(snapshot: IssueSnapshot) -> IssueWorkRecord:
    """Read exact requirements and references directly from the current Issue."""
    match = _work_match(snapshot.body)
    _require(match is not None, "current Issue work record is absent; locate the owning record or stop")
    try:
        data = json.loads(match[1], object_pairs_hook=_unique_keys)
        for key in ("requirements", "acceptance", "dependencies", "unknowns", "stop_conditions",
                    "artifacts", "decisions", "history"):
            if not isinstance(data[key], list):
                raise ValueError(f"{key} must be a list")
            data[key] = tuple(data[key])
        data["artifacts"] = tuple(
            ArtifactReference(**(item | {"record": RecordPointer(**item["record"])}))
            for item in data["artifacts"]
        )
        for key in ("decisions", "history"):
            data[key] = tuple(RecordPointer(**pointer) for pointer in data[key])
        if data["decision_request"] is not None:
            data["decision_request"] = RecordPointer(**data["decision_request"])
        work = IssueWorkRecord(**data)
        _validate(work)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ProjectionError("invalid current Issue work record") from exc
    _require(work.issue_id == snapshot.issue_id, "current work record belongs to a different Issue")
    return work


def work_record_sha256(snapshot: IssueSnapshot) -> str:
    match = _work_match(snapshot.body)
    _require(match is not None, "current Issue work record is absent")
    return _digest(match[0])


def embed_work_record(body: bytes, work: IssueWorkRecord) -> bytes:
    """Stage an explicitly supplied work record without changing surrounding bytes."""
    _validate(work)
    match = _work_match(body)
    bounds = _view_bounds(body)
    _require(bounds is not None and bounds[0] == 0, "Human View must begin the Issue")
    eol = b"\r\n" if body[len(VIEW_START):].startswith(b"\r\n") else b"\n"
    payload = json.dumps(asdict(work), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    payload = payload.replace("-", r"\u002d").replace("<", r"\u003c").replace(">", r"\u003e")
    block = eol.join((_MARKER + b"v1", payload.encode("ascii"), b"-->"))
    if match is not None:
        return body[:match.start()] + block + body[match.end():]
    return body[:bounds[1]] + eol * 2 + block + body[bounds[1]:]


def _resolve_handoff(
    work: IssueWorkRecord,
    project: RecordPointer,
    pm: RecordPointer,
    resolve_current: ResolveRecord,
    resolve_history: ResolveRecord | None = None,
) -> WorkHandoff:
    _require(isinstance(project, RecordPointer) and isinstance(pm, RecordPointer)
             and (project.locator, pm.locator) == (work.project_locator, work.pm_locator),
             "management records do not match the current Issue references")
    inputs = ProjectionInput(project, pm, tuple(item.record for item in work.artifacts), work.decision_request)
    verified = _load(inputs, resolve_current, (work.purpose, work.acceptance))
    _require(verified.pm.issue_id == work.issue_id, "Issue and current execution are for different work")
    for item, artifact in zip(work.artifacts, verified.evidence, strict=True):
        binding = artifact.value
        _require(isinstance(binding, ArtifactBinding)
                 and (binding.issue_id, binding.kind) == (work.issue_id, item.kind)
                 and binding.status in ("current", "proposed", "verified"),
                 "current technical artifact is missing its Work Item or purpose binding")
        _text(binding.scope, "artifact scope")
    decisions = tuple(_resolve(pointer, "decision", resolve_current) for pointer in work.decisions)
    for record in decisions:
        decision = record.value
        _require(isinstance(decision, RecordedDecision) and decision.issue_id == work.issue_id
                 and decision.outcome in ("approved", "held", "rejected"),
                 "current Decision record is missing its Work Item or outcome")
        _text(decision.authority, "recorded decision authority")
        _text(decision.scope, "recorded decision scope")
    history_links = []
    if resolve_history is not None:
        for pointer in work.history:
            saved = _resolve(pointer, "archive", resolve_history)
            _require(isinstance(saved.value, IssueArchive) and saved.value.issue_id == work.issue_id,
                     "Issue history belongs to different work")
            history_links.append(saved.link)
    risks = tuple(dict.fromkeys((*verified.pm.risks, *work.unknowns)))
    verified = replace(verified, pm=replace(verified.pm, risks=risks))
    return WorkHandoff(work, inputs, verified, decisions, tuple(history_links))


def resolve_work_handoff(
    snapshot: IssueSnapshot,
    *,
    resolve_management: ResolveManagement,
    resolve_current: ResolveRecord,
) -> WorkHandoff:
    """Resolve current design, decisions, and evidence from the Issue's references.

    The host reads the current Issue and supplies role-specific authoritative
    reads. The live adapter resolves the owner's currently designated revision,
    even when a historical requested revision would still be retrievable.
    History is neither read nor used to supply handoff inputs.
    """
    work = read_work_record(snapshot)
    try:
        project = resolve_management("project", work.project_locator)
        pm = resolve_management("pm", work.pm_locator)
    except (KeyError, OSError, ValueError) as exc:
        raise ProjectionError("current management reference could not be resolved") from exc
    return _resolve_handoff(work, project, pm, resolve_current)


def _render(handoff: WorkHandoff, previous: WorkHandoff | None = None) -> ProjectedView:
    work = handoff.work
    changes = ()
    if previous is not None:
        fields = (
            ("requirements", "requirements"), ("dependencies", "dependencies"),
            ("artifacts", "technical artifacts"), ("decisions", "recorded decisions"),
            ("stop_conditions", "stop conditions"),
        )
        changes = tuple(label for key, label in fields if getattr(work, key) != getattr(previous.work, key))
    labels = tuple(
        _LABELS[item.kind] + (" (proposed)" if readback.value.status == "proposed" else "")
        for item, readback in zip(work.artifacts, handoff.artifacts, strict=True)
    )
    return _render_verified(
        handoff.inputs, handoff._verified,
        previous.inputs if previous else None, previous._verified if previous else None,
        reference_labels=labels,
        history_links=handoff.history_links,
        extra_changes=changes,
    )


def prepare_current_create(
    work: IssueWorkRecord,
    project: RecordPointer,
    pm: RecordPointer,
    *,
    resolve_current: ResolveRecord,
    resolve_history: ResolveRecord,
) -> UpdatePlan:
    """Prepare creation from existing saved records and a reserved Issue identity."""
    _validate(work)
    view = _render(_resolve_handoff(work, project, pm, resolve_current, resolve_history))
    plan = prepare_create(view)
    return replace(plan, replacement=embed_work_record(plan.replacement, work), current_pm=pm)


def prepare_current_update(
    snapshot: IssueSnapshot,
    project: RecordPointer,
    pm: RecordPointer,
    *,
    resolve_current: ResolveRecord,
    resolve_history: ResolveRecord,
    prior_delivery: RecordPointer | None = None,
    edit_history: RecordPointer | None = None,
    candidate: IssueWorkRecord | None = None,
    expected_work_record_sha256: str | None = None,
    previous: WorkHandoff | None = None,
) -> UpdatePlan:
    """Stage approved work or refresh the current view after record readback.

    The host verifies human authorization for explicit work-record changes.
    Keep old aliases and manual Issue text outside the two managed regions.
    """
    existing = read_work_record(snapshot) if _work_match(snapshot.body) is not None else None
    _require(existing is not None or candidate is not None, "current Issue work record is absent")
    work = candidate if candidate is not None else existing
    _validate(work)
    _require(work.issue_id == snapshot.issue_id, "candidate belongs to a different Issue")
    handoff = _resolve_handoff(work, project, pm, resolve_current, resolve_history)
    view = _render(handoff, previous)
    plan = prepare_update(snapshot, view, resolve=resolve_history,
                          prior_delivery=prior_delivery, edit_history=edit_history)
    replacement = plan.replacement
    if work != existing:
        _require(existing is None or expected_work_record_sha256 == work_record_sha256(snapshot),
                 "current Issue work record differs from the expected revision; reconcile before replacing it")
        replacement = embed_work_record(replacement, work)
    if plan.replacement == snapshot.body and replacement != snapshot.body:
        _archived(snapshot, edit_history, resolve_history, role="issue_history")
    return replace(plan, replacement=replacement, archive=edit_history, current_pm=pm)


def apply_current_update(
    plan: UpdatePlan,
    writer: AtomicIssueWriter,
    *,
    resolve_current: ResolveRecord,
    resolve_history: ResolveRecord,
) -> WriteReceipt:
    """Recheck saved records before sending and after receiving a write receipt."""
    _recheck_plan(plan, resolve_current, resolve_history)
    receipt = apply_update(plan, writer)
    try:
        _recheck_plan(plan, resolve_current, resolve_history)
    except ProjectionError as exc:
        raise ProjectionError("Issue write confirmed but current records changed; reconcile before retrying") from exc
    return receipt


def _recheck_plan(plan: UpdatePlan, resolve_current: ResolveRecord, resolve_history: ResolveRecord) -> None:
    _require(plan.current_pm is not None, "prepared current PM source is required")
    snapshot = IssueSnapshot(plan.issue_id, plan.issue_revision or "reserved", plan.replacement)
    _resolve_handoff(read_work_record(snapshot), plan.project, plan.current_pm, resolve_current, resolve_history)
    if plan.changed and plan.issue_revision is not None:
        _require(plan.archive is not None, "exact previous Issue history is required")
        saved = _resolve(plan.archive, "issue_history", resolve_history)
        _require(isinstance(saved.value, IssueArchive)
                 and (saved.value.issue_id, saved.value.issue_revision, plan.archive.sha256)
                 == (plan.issue_id, plan.issue_revision, plan.issue_sha256),
                 "previous Issue history no longer matches the prepared update")


def reconcile_current_update(
    plan: UpdatePlan,
    observed: IssueSnapshot | None,
    *,
    resolve_current: ResolveRecord,
    resolve_history: ResolveRecord,
) -> Literal["applied", "retry"]:
    """Classify exact readback after an uncertain write, without writing again.

    The host supplies authoritative Issue readback; None means confirmed absence.
    """
    _recheck_plan(plan, resolve_current, resolve_history)
    if observed is None and plan.issue_revision is None:
        return "retry"
    if observed is not None and observed.issue_id == plan.issue_id:
        _text(observed.revision, "observed Issue revision")
        if observed.body == plan.replacement:
            return "applied"
        if (observed.revision, _digest(observed.body)) == (plan.issue_revision, plan.issue_sha256):
            return "retry"
    raise ProjectionConflict("Issue diverged from both prepared revisions; re-read before preparing another update")
