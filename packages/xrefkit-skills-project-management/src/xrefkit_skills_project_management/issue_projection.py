"""Project a bounded Issue view from verified, existing management records.

The caller supplies trusted readback and compare-and-swap adapters. Normalized
values describe existing records in memory and are never persisted by this module.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from typing import Callable, Literal, Protocol
from urllib.parse import urlsplit


VIEW_START = b"<!-- pm-human-view:start -->"
VIEW_END = b"<!-- pm-human-view:end -->"
MAX_VIEW_BYTES = 8192
_MARKDOWN_ENTITIES = {
    ord(char): f"&#{ord(char)};" for char in "\\`*_{}[]()<>#+-.!|~&:@/"
}


class ProjectionError(ValueError):
    """A required source, projection boundary, or write guarantee is missing."""


class ProjectionConflict(ProjectionError):
    """The authoritative Project or Issue changed before the update."""


@dataclass(frozen=True)
class RecordPointer:
    role: Literal[
        "project", "pm", "technical", "decision", "archive", "issue_history",
        "migration_authorization", "delivery",
    ]
    locator: str
    revision: str
    sha256: str


@dataclass(frozen=True)
class Readback:
    """A trusted adapter's exact bytes, reader link, and value decoded from those bytes."""

    locator: str
    revision: str
    content: bytes
    link: str
    value: object


ResolveRecord = Callable[[RecordPointer], Readback]


@dataclass(frozen=True)
class ProjectState:
    issue_id: str
    item_id: str
    status: str


@dataclass(frozen=True)
class ReviewResult:
    verdict: str
    scope: str
    gaps: tuple[str, ...] = ()


@dataclass(frozen=True)
class PMState:
    issue_id: str
    item_id: str
    project_revision: str
    status: str
    kind: Literal["blocked", "review", "progress"]
    state: str
    purpose: str
    acceptance: tuple[str, ...]
    owner: str
    next_action: str
    blockers: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    review: ReviewResult | None = None
    plan: str | None = None
    deadline: str | None = None
    required_evidence: tuple[str, ...] = ()
    decision_locator: str | None = None


@dataclass(frozen=True)
class DecisionOption:
    label: str
    impact: str


@dataclass(frozen=True)
class DecisionRequest:
    """An existing, explicitly recorded request for a human judgment."""

    issue_id: str
    pm_revision: str
    actionable: bool
    question: str
    owner: str
    enables: str
    excluded: str
    deferred: str
    why_now: str
    options: tuple[DecisionOption, ...]
    recommendation: str | None = None
    risks: tuple[str, ...] = ()
    available_while_blocked: bool = False


@dataclass(frozen=True)
class ProjectionInput:
    project: RecordPointer
    pm: RecordPointer
    evidence: tuple[RecordPointer, ...] = ()
    decision: RecordPointer | None = None


@dataclass(frozen=True)
class ProjectedView:
    body: bytes
    issue_id: str
    project: RecordPointer
    pm: RecordPointer
    sources: tuple[RecordPointer, ...]
    project_item_id: str
    project_status: str


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProjectionError(message)


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _text(value: str, field: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{field}: nonempty text required")
    return value


def _inline(value: str) -> str:
    # Entities keep record text inert, including GFM autolinks and mentions.
    text = " ".join(_text(value, "display text").split())
    _require(not any(ord(char) < 32 or ord(char) == 127 for char in text), "unsafe display control character")
    return text.translate(_MARKDOWN_ENTITIES)


def _url(value: str) -> str:
    _text(value, "record link")
    allowed = re.fullmatch(r"[\x21-\x7e]+", value) and not any(c in value for c in '<>\\')
    _require(bool(allowed), "record link contains unsafe characters")
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise ProjectionError("record link is malformed") from exc
    _require(
        parsed.scheme == "https" and bool(parsed.hostname) and parsed.username is None,
        "record link must be an HTTPS URL without credentials",
    )
    return value


def _resolve(pointer: RecordPointer, role: str, resolve: ResolveRecord) -> Readback:
    _require(isinstance(pointer, RecordPointer) and pointer.role == role, f"{role}: incorrect record role")
    _text(pointer.locator, "record locator")
    _text(pointer.revision, "record revision")
    _text(pointer.sha256, "record SHA-256")
    _require(bool(re.fullmatch(r"[a-f0-9]{64}", pointer.sha256)), "record SHA-256 is required")
    try:
        found = resolve(pointer)
    except (KeyError, OSError, ValueError) as exc:
        raise ProjectionError(f"{role}: record could not be resolved") from exc
    _require(
        isinstance(found, Readback) and found.locator == pointer.locator
        and found.revision == pointer.revision,
        f"{role}: readback identity or revision mismatch",
    )
    _require(
        isinstance(found.content, bytes) and _digest(found.content) == pointer.sha256,
        f"{role}: readback SHA-256 mismatch",
    )
    _url(found.link)
    return found


@dataclass(frozen=True)
class _Verified:
    pm: PMState
    decision: DecisionRequest | None
    links: tuple[tuple[str, str], ...]
    evidence: tuple[Readback, ...]


def _load(
    source: ProjectionInput,
    resolve: ResolveRecord,
    issue_scope: tuple[str, tuple[str, ...]] | None = None,
) -> _Verified:
    project = _resolve(source.project, "project", resolve)
    pm = _resolve(source.pm, "pm", resolve)
    _require(isinstance(project.value, ProjectState), "authoritative Project state missing")
    _require(isinstance(pm.value, PMState), "authoritative PM state missing")
    state = pm.value
    if issue_scope is not None:
        state = replace(state, purpose=issue_scope[0], acceptance=issue_scope[1])
    _text(project.value.issue_id, "Project Issue identity")
    _text(project.value.item_id, "Project item identity")
    _text(project.value.status, "Project status")
    _require(
        (state.issue_id, state.item_id, state.status, state.project_revision)
        == (project.value.issue_id, project.value.item_id, project.value.status, source.project.revision),
        "PM state does not match authoritative Project item, status, or revision",
    )
    _require(state.kind in ("blocked", "review", "progress"), "unmapped presentation kind")
    _require(state.kind != "blocked" or bool(state.blockers), "blocked view needs its blocker")
    _require(bool(state.acceptance), "Issue acceptance criteria are required")
    for items in (state.acceptance, state.blockers, state.risks, state.required_evidence):
        _require(isinstance(items, tuple), "record lists must be immutable tuples")
    _require(state.review is None or isinstance(state.review, ReviewResult), "invalid review result")
    _require(
        all(isinstance(record, RecordPointer) for record in source.evidence),
        "technical evidence pointers are required",
    )
    _require(
        set(state.required_evidence) <= {record.locator for record in source.evidence},
        "required technical evidence pointer is missing",
    )
    _require(
        state.decision_locator is None
        or (isinstance(source.decision, RecordPointer) and source.decision.locator == state.decision_locator),
        "linked human judgment request is missing",
    )
    records = (source.project, source.pm, *source.evidence)
    if source.decision is not None:
        _require(isinstance(source.decision, RecordPointer), "human judgment pointer is required")
        records += (source.decision,)
    _require(len({record.locator for record in records}) == len(records), "record roles require distinct locators")

    links = [("Project item", project.link), ("PM record", pm.link)]
    evidence_records = tuple(_resolve(pointer, "technical", resolve) for pointer in source.evidence)
    for index, evidence in enumerate(evidence_records, 1):
        links.append((f"Technical evidence {index}", evidence.link))

    decision = None
    if source.decision is not None:
        record = _resolve(source.decision, "decision", resolve)
        _require(isinstance(record.value, DecisionRequest), "explicit human judgment request missing")
        _require(
            record.value.issue_id == state.issue_id and record.value.pm_revision == source.pm.revision,
            "human judgment request does not apply to current work",
        )
        _require(type(record.value.actionable) is bool, "human judgment request needs an explicit applicability state")
        if record.value.actionable:
            decision = record.value
            _require(
                not state.blockers or decision.available_while_blocked is True,
                "decision request must explicitly apply while work is blocked",
            )
            _require(
                isinstance(decision.options, tuple) and bool(decision.options)
                and all(isinstance(item, DecisionOption) for item in decision.options),
                "actionable judgment needs recorded options and impacts",
            )
            labels = [_text(item.label, "decision option") for item in decision.options]
            _require(
                len(set(labels)) == len(labels) and (
                    decision.recommendation is None or decision.recommendation in labels
                ),
                "decision option labels must be unique and the recommendation must name a recorded option",
            )
            links.append(("Decision scope", record.link))
    return _Verified(state, decision, tuple(links), evidence_records)


def _changes(current: _Verified, previous: _Verified | None, extra_changes: tuple[str, ...]) -> str:
    if previous is None:
        return "Previous report basis is unknown."
    attributes = (
        ("status", "Project status"), ("kind", "work focus"), ("state", "current state"),
        ("blockers", "blockers"), ("risks", "risks and unknowns"), ("review", "review result"),
        ("owner", "owner"), ("next_action", "next action"), ("purpose", "purpose"),
        ("acceptance", "acceptance criteria"), ("plan", "plan"), ("deadline", "deadline"),
    )
    changed = [
        label for key, label in attributes if getattr(current.pm, key) != getattr(previous.pm, key)
    ]
    current_decision = replace(current.decision, pm_revision="") if current.decision else None
    previous_decision = replace(previous.decision, pm_revision="") if previous.decision else None
    if current_decision != previous_decision:
        changed.append("human decision")
    changed.extend(extra_changes)
    if not changed:
        return "No material change from the previous report."
    return "Changed since the previous report: " + ", ".join(changed) + "."


def render_view(
    current: ProjectionInput,
    resolve: ResolveRecord,
    *,
    previous: ProjectionInput | None = None,
) -> ProjectedView:
    """Render a creation draft or replaceable view from current authoritative records."""
    return _render_verified(
        current, _load(current, resolve), previous,
        _load(previous, resolve) if previous is not None else None,
    )


def _render_verified(
    current: ProjectionInput,
    verified: _Verified,
    previous: ProjectionInput | None = None,
    prior: _Verified | None = None,
    *,
    reference_labels: tuple[str, ...] = (),
    history_links: tuple[str, ...] = (),
    extra_changes: tuple[str, ...] = (),
) -> ProjectedView:
    state = verified.pm
    if prior is not None:
        _require(
            (prior.pm.issue_id, prior.pm.item_id) == (state.issue_id, state.item_id)
            and previous.project.locator == current.project.locator
            and previous.pm.locator == current.pm.locator,
            "previous report basis is for different work",
        )

    lines = [VIEW_START.decode(), f"**{_inline(state.state)}**", "", _changes(verified, prior, extra_changes), ""]
    lines += [f"**Purpose.** {_inline(state.purpose)}", "", "**Acceptance.**", ""]
    lines.extend(f"- {_inline(criterion)}" for criterion in state.acceptance)
    for label, items in (("Blockers", state.blockers), ("Risks and unknowns", state.risks)):
        if items:
            lines += ["", f"**{label}.** " + " / ".join(_inline(item) for item in items)]
    if state.review is not None:
        review = state.review
        lines += ["", f"**Review.** {_inline(review.verdict)}. Scope: {_inline(review.scope)}."]
        if review.gaps:
            lines.append("Remaining verification: " + " / ".join(_inline(gap) for gap in review.gaps))
    elif state.kind == "review":
        lines += ["", "**Review result pending.**"]
    if verified.decision is not None:
        decision = verified.decision
        lines += [
            "", "**Decision needed.** " + _inline(decision.question), "",
            "- Decision owner: " + _inline(decision.owner),
            "- Why now: " + _inline(decision.why_now),
            "- Enables: " + _inline(decision.enables),
            "- Outside scope: " + _inline(decision.excluded),
            "- If deferred: " + _inline(decision.deferred),
        ]
        if decision.risks:
            lines.append("- Decision risks: " + " / ".join(_inline(risk) for risk in decision.risks))
        lines.extend(f"- {_inline(option.label)}: {_inline(option.impact)}" for option in decision.options)
        if decision.recommendation is not None:
            lines.append("- Recommendation: " + _inline(decision.recommendation))
    if state.plan is not None:
        lines += ["", "**Plan.** " + _inline(state.plan)]
    if state.deadline is not None:
        lines += ["", "**Deadline.** " + _inline(state.deadline)]
    lines += ["", f"**Next.** {_inline(state.owner)} — {_inline(state.next_action)}.", ""]
    links = list(verified.links)
    if reference_labels:
        _require(len(reference_labels) == len(current.evidence), "technical link labels do not match records")
        for index, label in enumerate(reference_labels, 2):
            links[index] = (_inline(label), links[index][1])
    if prior is not None:
        links.append(("Previous PM record", prior.links[1][1]))
    links.extend(("Issue history snapshot", _url(link)) for link in history_links)
    lines += [" · ".join(f"[{label}](<{link}>)" for label, link in links), VIEW_END.decode()]
    sources = (current.project, current.pm, *current.evidence)
    if current.decision is not None:
        sources += (current.decision,)
    body = ("\n".join(lines) + "\n").encode("utf-8")
    _require(len(body) <= MAX_VIEW_BYTES, "Human View exceeds the display limit; split the work by decision")
    return ProjectedView(body, state.issue_id, current.project, current.pm, sources, state.item_id, state.status)


@dataclass(frozen=True)
class IssueSnapshot:
    issue_id: str
    revision: str
    body: bytes
    # A complete, authoritative rendered inventory. None means unavailable.
    fragments: tuple[str, ...] | None = None


@dataclass(frozen=True)
class IssueArchive:
    issue_id: str
    issue_revision: str
    fragments: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ManagedDelivery:
    """An existing receipt for the exact Human View bytes previously delivered."""

    issue_id: str
    managed_sha256: str


@dataclass(frozen=True)
class MigrationAuthorization:
    """Verified existing human authorization for one Issue revision and alias plan."""

    issue_id: str
    issue_revision: str
    body_sha256: str
    approved_by: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class LegacyMigration:
    authorization: RecordPointer
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class UpdatePlan:
    issue_id: str
    issue_revision: str | None
    issue_sha256: str | None
    project: RecordPointer
    project_item_id: str
    project_status: str
    replacement: bytes
    archive: RecordPointer | None
    prior_delivery: RecordPointer | None
    current_pm: RecordPointer | None = None

    @property
    def changed(self) -> bool:
        return _digest(self.replacement) != self.issue_sha256


@dataclass(frozen=True)
class WriteReceipt:
    issue_id: str
    issue_revision: str
    project_revision: str
    body_sha256: str
    changed: bool


class AtomicIssueWriter(Protocol):
    supports_atomic_issue_and_project_compare: Literal[True]

    def compare_and_swap(self, plan: UpdatePlan) -> WriteReceipt | None:
        """Compare Issue identity/revision/hash and the current Project snapshot atomically.

        The Project comparison covers locator, item, status, revision and hash.
        A null Issue revision and hash require authoritative absence for the
        supplied logical Issue identity, reserved by the host for creation.
        Write the replacement only under both fences. Return None on conflict.
        A byte-identical result can return changed=False after validating the
        Project fence and current Issue body, including retry after a lost receipt.
        Return a receipt for the authoritative readback, not an intended result.
        """
        ...


def _view_bounds(body: bytes) -> tuple[int, int] | None:
    if VIEW_START not in body and VIEW_END not in body:
        return None
    matches = [re.search(rb"^" + re.escape(marker) + rb"(?=\r?$)", body, re.MULTILINE)
               for marker in (VIEW_START, VIEW_END)]
    start, end = matches
    _require(
        start is not None and end is not None and start.end() < end.start()
        and body.count(VIEW_START) == body.count(VIEW_END) == 1,
        "Issue needs exactly one well-formed Human View marker pair",
    )
    return start.start(), end.end()


def managed_view_sha256(body: bytes) -> str:
    """Hash the unique marker-delimited bytes without the trailing line ending."""
    bounds = _view_bounds(body)
    _require(bounds is not None, "managed Human View markers are missing")
    return _digest(body[slice(*bounds)])


def _archived(
    snapshot: IssueSnapshot,
    archive: RecordPointer | None,
    resolve: ResolveRecord,
    *,
    role: str = "archive",
) -> Readback:
    _require(archive is not None, "archive of the exact prior Issue revision is required")
    found = _resolve(archive, role, resolve)
    _require(
        found.content == snapshot.body and isinstance(found.value, IssueArchive)
        and (found.value.issue_id, found.value.issue_revision) == (snapshot.issue_id, snapshot.revision),
        "archive does not match the complete prior Issue revision",
    )
    return found


def _legacy_replacement(
    snapshot: IssueSnapshot, view: ProjectedView, saved: Readback,
    migration: LegacyMigration, resolve: ResolveRecord,
    *, link_archive: bool,
) -> bytes:
    record = _resolve(migration.authorization, "migration_authorization", resolve)
    auth = record.value
    _require(
        isinstance(auth, MigrationAuthorization)
        and (auth.issue_id, auth.issue_revision, auth.body_sha256)
        == (snapshot.issue_id, snapshot.revision, _digest(snapshot.body)),
        "legacy migration requires explicit human authorization for this Issue revision and body",
    )
    _text(auth.approved_by, "migration approver")
    aliases = migration.aliases
    _require(
        snapshot.fragments is not None and saved.value.fragments is not None
        and len(aliases) == len(set(aliases))
        and all(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}", fragment) for fragment in aliases)
        and set(aliases) == set(snapshot.fragments) == set(auth.aliases)
        and set(aliases) <= set(saved.value.fragments)
        and (not link_archive or not urlsplit(saved.link).fragment),
        "complete old fragment aliases and matching archived targets must be verified",
    )
    lines = ["", f"[Prior Issue record](<{saved.link}>)"] if link_archive else []
    for alias in aliases:
        lines += ["", f'<a name="{alias}"></a>']
        if link_archive:
            lines.append(f"[Archived section](<{saved.link}#{alias}>)")
    if not lines:
        return view.body
    return view.body + ("\n".join(lines) + "\n").encode("utf-8")


def _validate_view(view: ProjectedView) -> None:
    _text(view.issue_id, "Issue identity")
    _require(_view_bounds(view.body) == (0, len(view.body) - 1), "invalid projected view")


def prepare_create(view: ProjectedView) -> UpdatePlan:
    """Stage creation for the host's authoritative, reserved logical Issue identity."""
    _validate_view(view)
    return UpdatePlan(
        view.issue_id, None, None, view.project, view.project_item_id, view.project_status,
        view.body, None, None,
    )


def prepare_update(
    snapshot: IssueSnapshot,
    view: ProjectedView,
    *,
    archive: RecordPointer | None = None,
    prior_delivery: RecordPointer | None = None,
    resolve: ResolveRecord,
    migration: LegacyMigration | None = None,
    edit_history: RecordPointer | None = None,
) -> UpdatePlan:
    """Stage an update without mutating Issue, Project, or evidence records."""
    _require(snapshot.issue_id == view.issue_id, "view is for a different Issue")
    _text(snapshot.issue_id, "Issue identity")
    _text(snapshot.revision, "Issue revision")
    _validate_view(view)
    bounds = _view_bounds(snapshot.body)
    if migration is not None:
        _require(archive is None or edit_history is None, "select one verified Issue history source")
        saved = _archived(snapshot, edit_history or archive, resolve,
                          role="issue_history" if edit_history is not None else "archive")
        replacement = _legacy_replacement(snapshot, view, saved, migration, resolve, link_archive=archive is not None)
    else:
        _require(bounds is not None, "unmanaged Issue requires a separately authorized legacy migration")
        start, end = bounds
        eol = b"\r\n" if snapshot.body[start + len(VIEW_START):].startswith(b"\r\n") else b"\n"
        new_block = view.body[:-1].replace(b"\n", eol)
        replacement = snapshot.body[:start] + new_block + snapshot.body[end:]
        if replacement != snapshot.body:
            _require(prior_delivery is not None, "trusted prior Human View delivery is required")
            prior = _resolve(prior_delivery, "delivery", resolve).value
            _require(
                isinstance(prior, ManagedDelivery) and prior.issue_id == snapshot.issue_id
                and prior.managed_sha256 == managed_view_sha256(snapshot.body),
                "existing Human View differs from the prior delivery; reconcile before replacing it",
            )
            if edit_history is not None:
                _archived(snapshot, edit_history, resolve, role="issue_history")
            else:
                _archived(snapshot, archive, resolve)
    return UpdatePlan(
        snapshot.issue_id, snapshot.revision, _digest(snapshot.body), view.project,
        view.project_item_id, view.project_status, replacement, edit_history or archive, prior_delivery,
    )


def apply_update(plan: UpdatePlan, writer: AtomicIssueWriter) -> WriteReceipt:
    _require(
        getattr(writer, "supports_atomic_issue_and_project_compare", False) is True
        and callable(getattr(writer, "compare_and_swap", None)),
        "writer cannot enforce atomic Issue and Project revision fences",
    )
    try:
        receipt = writer.compare_and_swap(plan)
    except Exception as exc:
        raise ProjectionError("write outcome is unknown; reconcile the authoritative records before retrying") from exc
    if receipt is None:
        raise ProjectionConflict("Issue or Project revision changed; re-read before preparing another update")
    _require(
        isinstance(receipt, WriteReceipt) and receipt.issue_id == plan.issue_id
        and bool(receipt.issue_revision) and receipt.project_revision == plan.project.revision
        and receipt.body_sha256 == _digest(plan.replacement)
        and type(receipt.changed) is bool
        and (not receipt.changed or (plan.changed and receipt.issue_revision != plan.issue_revision)),
        "write outcome is unverified; reconcile the authoritative records before retrying",
    )
    return receipt
