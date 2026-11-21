"""Evaluate pinned synthetic I/O records without dispatch or workflow projection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, replace
from collections.abc import Mapping
from hashlib import sha256
import json
from typing import Literal

from .contracts import AssignmentRef, ExecutionEvent, ExecutionRequest, ExecutionResult, assess_model_result
from .offline_dispatch import ToolCorrelation, ToolDecision
from .offline_responses import AdapterResult, TextItem, UsageObservation


Outcome = Literal["pass", "fail", "unresolved", "omitted", "not_applicable"]
NextCheck = Literal["report_only", "verify_evidence", "verify_effect", "reconcile",
                    "request_independent_review", "record_reevaluation_link"]


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _identifier_digest(value: str) -> str:
    return _digest(json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode())


@dataclass(frozen=True)
class RevisionLinks:
    request_revision: str
    result_revision: str
    tool_receipt_revision: str
    criteria_revision: str
    criteria_sha256: str
    evidence_revision: str
    correlation: tuple[str, str, str]


@dataclass(frozen=True)
class ReviewAuthority:
    reviewer_id: str
    context: str


@dataclass(frozen=True)
class ReplayAuthorization:
    """Trusted receipt link from an authorized #204 replay with exact return scope."""

    original: ToolCorrelation
    current: ToolCorrelation
    return_scope_sha256: str


@dataclass(frozen=True)
class EvaluationPolicy:
    """The trusted side supplies this scope and the applicable criteria before evaluation."""

    assignment: AssignmentRef
    links: RevisionLinks
    api_request_sha256: str
    api_observation_sha256: str
    tool_observation_sha256: str
    output_sha256: str
    trace_pins: tuple[str, str, str]
    rubric_utf8: bytes = field(repr=False)
    approved_rules_sha256: str
    provider_reservation_ref: str
    effect_observation_pins: tuple[str, ...]
    interaction_pin: str | None
    reviewer_record_pins: tuple[str, ...]
    expected_model: str | None
    expected_postcondition: str | None
    output_byte_limit: int
    producer: str
    producer_context: str
    reviewers: tuple[ReviewAuthority, ...]
    trusted_readback_origins: frozenset[str]
    usage_required_fields: frozenset[str] = frozenset()
    interaction_required: bool = False
    semantic_required: bool = True
    permitted_interaction_origin: str = "synthetic-registry"
    rubric_successor: tuple[str, str] | None = None
    prior_evaluation_ref: str | None = None
    replay_authorization: ReplayAuthorization | None = None
    tool_authorization_digests: tuple[str, str, str] | None = None
    evaluation_ref: str = "evaluation-205-r1"
    previous_evaluation_pin: str | None = None


@dataclass(frozen=True)
class EffectObservation:
    ref: str
    origin: str
    authorized: bool
    current: bool
    operation_id: str
    revision: str
    observed: str


@dataclass(frozen=True)
class InteractionReference:
    ref: str
    revision: str
    attempt_id: str
    access: str
    status: str
    origin: str


@dataclass(frozen=True)
class SemanticReview:
    id: str
    role: str
    authorized: bool
    context: str
    author_context: str
    links: RevisionLinks
    output_sha256: str
    verdict: str
    basis_refs: tuple[str, ...]
    rationale: str = field(repr=False)
    basis_pins: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReevaluationLink:
    prior_evaluation_ref: str
    previous_criteria_revision: str
    new_criteria_revision: str
    new_criteria_sha256: str
    new_evaluation_ref: str


@dataclass(frozen=True)
class EvaluationInputs:
    request: ExecutionRequest
    events: tuple[ExecutionEvent, ...]
    result: ExecutionResult | dict[str, object]
    links: RevisionLinks
    api: AdapterResult
    tool: ToolDecision
    output_utf8: bytes = field(repr=False)
    tool_return_utf8: bytes = field(repr=False)
    recorded_tool_effect: Literal["none", "observed", "unknown"] | None = None
    tool_return_scope_sha256: str | None = None
    postconditions: tuple[EffectObservation, ...] = ()
    interaction: InteractionReference | Mapping[str, object] | None = None
    reviews: tuple[SemanticReview, ...] = ()
    reevaluation: ReevaluationLink | None = None


@dataclass(frozen=True)
class Criterion:
    id: str
    outcome: Outcome
    reason: str
    next_check: NextCheck = "report_only"
    evidence_refs: tuple[str, ...] = ()
    evidence_owner: str | None = None
    comparison_sha256: tuple[str, str] | None = None
    provenance: str | None = None


@dataclass(frozen=True)
class Evaluation:
    criteria_revision: str
    criteria_sha256: str
    criteria: tuple[Criterion, ...]
    aggregate: Literal["criteria_met", "criteria_failed", "criteria_unresolved"]
    next_proposal: NextCheck
    v1_assessment: Literal["refused", "held", "review_required"]
    api_outcome: str
    tool_outcome: str
    tool_effect: Literal["none", "observed", "unknown", "unverified"]
    entry_observed: bool
    usage: UsageObservation
    retained_reviewers: tuple[str, ...]
    review_state: Literal["reviewed", "pending", "not_applicable"]
    output_sha256: str
    approved_policy_sha256: str
    source_findings: tuple[Criterion, ...]
    evaluation_ref: str = "evaluation-205-r1"
    reevaluation_from: str | None = None
    approved_rubric_successor: tuple[str, str] | None = None
    handoff_targets: tuple[str, str] = ("#206", "#209")
    allow_repeat: Literal[False] = False
    human_acceptance: None = None


_EVIDENCE_OWNERS = {
    "identity": "trace_owner", "model": "trace_owner", "structure": "evaluation_checker",
    "outcome": "adapter_or_dispatch_owner", "effect": "readback_owner", "usage": "adapter_owner",
    "interaction": "interaction_owner", "semantic": "independent_reviewer", "aggregate": "controller",
}


def _criterion(name: str, outcome: Outcome, reason: str, *refs: str,
               next_check: NextCheck = "report_only") -> Criterion:
    owner = _EVIDENCE_OWNERS[name] if outcome == "unresolved" else None
    return Criterion(name, outcome, reason, next_check, tuple(_identifier_digest(ref) for ref in refs), owner)


def _unknown(name: str, reason: str, *refs: str, next_check: NextCheck = "verify_evidence") -> Criterion:
    return _criterion(name, "unresolved", reason, *refs, next_check=next_check)


def _record_digest(record: object) -> str:
    return _digest(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def api_observation_digest(api: AdapterResult) -> str:
    """Seal the normalized, local adapter observation without exporting its contents."""
    return _record_digest(asdict(api))


def tool_observation_digest(tool: ToolDecision, effect: str | None) -> str:
    """Seal the local Tool decision and any separately recorded synthetic effect observation."""
    return _record_digest({"tool": asdict(tool), "effect": effect})


def trace_pins(request: ExecutionRequest, events: tuple[ExecutionEvent, ...],
               result: ExecutionResult) -> tuple[str, str, str]:
    return (
        _record_digest(request.model_dump(mode="json")),
        _record_digest([event.model_dump(mode="json") for event in events]),
        _record_digest(result.model_dump(mode="json")),
    )


def _policy_record(policy: EvaluationPolicy) -> dict[str, object]:
    record = asdict(policy)
    record["assignment"] = policy.assignment.model_dump(mode="json")
    record["rubric_utf8"] = _digest(policy.rubric_utf8)
    record["usage_required_fields"] = sorted(policy.usage_required_fields)
    record["trusted_readback_origins"] = sorted(policy.trusted_readback_origins)
    return record


def effective_rules_digest(policy: EvaluationPolicy) -> str:
    keys = ("expected_model", "expected_postcondition", "output_byte_limit", "usage_required_fields",
            "interaction_required", "semantic_required", "reviewers", "trusted_readback_origins",
            "producer", "producer_context", "permitted_interaction_origin", "rubric_successor", "prior_evaluation_ref")
    record = _policy_record(policy)
    return _record_digest({"rubric": record["rubric_utf8"], **{key: record[key] for key in keys}})


def evaluation_policy_digest(policy: EvaluationPolicy) -> str:
    return _record_digest(_policy_record(policy))


def _policy_valid(policy: EvaluationPolicy) -> bool:
    if _digest(policy.rubric_utf8) != policy.links.criteria_sha256:
        return False
    if effective_rules_digest(policy) != policy.approved_rules_sha256:
        return False
    try:
        rubric = json.loads(policy.rubric_utf8)
    except ValueError:
        return False
    return (
        isinstance(rubric, dict) and rubric.get("revision") == policy.links.criteria_revision
        and (policy.expected_postcondition is None or rubric.get("expected_postcondition") == policy.expected_postcondition)
    )


def evidence_digest(record: EffectObservation | InteractionReference | SemanticReview) -> str:
    return _record_digest(asdict(record))


def project_interaction(record: Mapping[str, object]) -> InteractionReference | None:
    """Read solely the permitted reference metadata from a protected interaction record."""
    permitted = tuple(record.get(field.name) for field in fields(InteractionReference))
    if not all(isinstance(value, str) for value in permitted):
        return None
    return InteractionReference(*permitted)


def _trace(policy: EvaluationPolicy, inputs: EvaluationInputs) -> tuple[Criterion, str]:
    name = "identity"
    request, result = inputs.request, inputs.result
    observed = (result.attempt_id, result.operation_id, result.call_id)
    if request.assignment != policy.assignment or result.assignment != policy.assignment:
        return _unknown(name, "assignment_not_current"), "held"
    if request.cancelled:
        return _unknown(name, "request_cancelled"), "held"
    if request.criteria_sha256 != policy.links.criteria_sha256:
        return _unknown(name, "criteria_digest_mismatch"), "held"
    if inputs.links != policy.links:
        return _unknown(name, "source_revision_mismatch"), "held"
    if observed != policy.links.correlation:
        return _unknown(name, "result_uncorrelated"), "held"
    if any(event.assignment != policy.assignment for event in inputs.events):
        return _unknown(name, "event_assignment_uncorrelated"), "held"
    if trace_pins(request, inputs.events, result) != policy.trace_pins:
        return _unknown(name, "trace_content_unpinned"), "held"
    try:
        assessment = assess_model_result(request, inputs.events, result)
    except ValueError:
        return _criterion(name, "fail", "trace_order_invalid"), "held"

    return _criterion(name, "pass", "trace_correlated", result.evidence_ref), assessment


def _api_check(policy: EvaluationPolicy, inputs: EvaluationInputs) -> Criterion:
    name = "identity"
    attempt_id, _, _ = policy.links.correlation
    diag = inputs.api.diagnostics
    if diag.attempt_id != attempt_id:
        return _unknown(name, "attempt_uncorrelated")
    if (diag.run_id, diag.work_item_id, diag.binding_sha256, diag.reservation_ref, diag.request_sha256) != (
        policy.assignment.run_id, policy.assignment.work_item_id, policy.assignment.binding_sha256,
        policy.provider_reservation_ref, policy.api_request_sha256,
    ):
        return _unknown(name, "api_evidence_uncorrelated")
    if api_observation_digest(inputs.api) != policy.api_observation_sha256:
        return _unknown(name, "api_observation_digest_mismatch")
    if inputs.api.disposition == "completed":
        text_items = tuple(item.text for item in inputs.api.items
                           if isinstance(item, TextItem) and item.kind == "text")
        try:
            if not text_items or "".join(text_items).encode("utf-8") != inputs.output_utf8:
                return _unknown(name, "api_output_unlinked")
        except UnicodeError:
            return _unknown(name, "api_output_unlinked")
    return _criterion(name, "pass", "api_observation_verified")


def _tool_check(policy: EvaluationPolicy, inputs: EvaluationInputs) -> Criterion:
    name = "identity"
    current_attempt, operation, current_call = policy.links.correlation
    if tool_observation_digest(inputs.tool, inputs.recorded_tool_effect) != policy.tool_observation_sha256:
        return _unknown(name, "tool_observation_digest_mismatch")
    receipt, evidence = inputs.tool.receipt, inputs.tool.evidence
    replay = policy.replay_authorization if inputs.tool.outcome == "replay" else None
    if inputs.tool.outcome == "replay" and (
        replay is None or receipt is None or evidence is None
        or inputs.tool.reason != "receipt_reuse_authorized"
        or inputs.tool_return_scope_sha256 != replay.return_scope_sha256
        or receipt.correlation != replay.original or evidence.correlation != replay.current
    ):
        return _unknown(name, "tool_replay_authorization_unverified")
    for item in (receipt, evidence):
        if item is None:
            continue
        link = item.correlation
        expected_fields = (
            ("operation", link.operation_digest, operation),
            ("run", link.run_digest, policy.assignment.run_id),
            ("work", link.work_digest, policy.assignment.work_item_id),
            ("route", link.route_digest, policy.assignment.route_id),
        )
        if replay is None or item is evidence:
            expected_fields += (("call", link.call_digest, current_call),
                                ("attempt", link.attempt_digest, current_attempt))
            if (link.policy_digest, link.grant_digest, link.reservation_digest) != policy.tool_authorization_digests:
                return _unknown(name, "tool_authorization_uncorrelated")
        for label, actual, expected in expected_fields:
            if actual != _identifier_digest(expected):
                return _unknown(name, f"{label}_uncorrelated")
        if inputs.recorded_tool_effect is not None and item.effect != inputs.recorded_tool_effect:
            return _unknown(name, "tool_effect_conflict", next_check="reconcile")
    if receipt is not None:
        if receipt.binding_generation != policy.assignment.owner_generation:
            return _unknown(name, "tool_generation_uncorrelated")
        if receipt.result_digest is not None and receipt.result_digest != _digest(inputs.tool_return_utf8):
            return _unknown(name, "tool_result_digest_mismatch")
        if evidence is not None and ((inputs.tool.outcome != "replay" and receipt.correlation != evidence.correlation)
                                     or receipt.action_digest != evidence.action_digest
                                     or receipt.effect != evidence.effect):
            return _unknown(name, "tool_attempt_receipt_conflict", next_check="reconcile")
        if inputs.tool.outcome in ("executed", "replay"):
            if receipt.effect != "observed" or receipt.outcome != "completed":
                return _unknown(name, "tool_receipt_outcome_unverified")
            if receipt.result_digest is None:
                return _unknown(name, "tool_result_digest_missing")
            try:
                returned = json.loads(inputs.tool_return_utf8.decode("utf-8"), object_pairs_hook=_object)
            except (ValueError, RecursionError):
                return _unknown(name, "tool_value_unverified")
            if (not isinstance(returned, dict) or returned.keys() != {"value"}
                    or inputs.tool.value is None or returned["value"] != inputs.tool.value):
                return _unknown(name, "tool_value_unverified")
    elif inputs.tool.outcome in ("executed", "replay"):
        return _unknown(name, "tool_receipt_missing")
    if evidence is None and receipt is None:
        return _unknown(name, "tool_attempt_evidence_missing")
    return _criterion(name, "pass", "tool_observation_verified")


def _model(policy: EvaluationPolicy, inputs: EvaluationInputs) -> Criterion:
    name = "model"
    if policy.expected_model is None:
        return _criterion(name, "not_applicable", "model_not_declared")
    if inputs.request.selected_model is None:
        return _unknown(name, "expected_model_missing")
    if inputs.request.selected_model != policy.expected_model:
        return _unknown(name, "model_request_not_current")
    observed = inputs.result.observed_model
    if observed is None or inputs.api.diagnostics.observed_model is None:
        return _unknown(name, "observed_model_missing")
    if observed != inputs.api.diagnostics.observed_model:
        return _unknown(name, "observed_model_conflict", next_check="reconcile")
    if observed != policy.expected_model:
        return _criterion(name, "fail", "observed_model_mismatch")
    return _criterion(name, "pass", "observed_model_matched")


class _DuplicateField(ValueError):
    pass


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateField(key)
        result[key] = value
    return result


def _structure(policy: EvaluationPolicy, inputs: EvaluationInputs) -> Criterion:
    name = "structure"
    if len(inputs.output_utf8) > policy.output_byte_limit:
        return _criterion(name, "fail", "byte_limit_exceeded")
    try:
        value = json.loads(inputs.output_utf8.decode("utf-8"), object_pairs_hook=_object)
    except _DuplicateField:
        return _criterion(name, "fail", "duplicate_field")
    except (ValueError, RecursionError):
        return _criterion(name, "fail", "invalid_json")
    if (not isinstance(value, dict) or value.keys() != {"objective"}
            or not isinstance(value["objective"], str) or not value["objective"].strip()):
        return _criterion(name, "fail", "schema_mismatch")
    return _criterion(name, "pass", "schema_matched")


def _outcome(inputs: EvaluationInputs, *, trace_valid: bool, api_valid: bool, tool_valid: bool) -> Criterion:
    name = "outcome"
    if api_valid and inputs.api.disposition in ("refusal", "incomplete", "provider_failed", "no_submit"):
        return _criterion(name, "fail", f"api_{inputs.api.disposition}")
    if tool_valid and inputs.tool.outcome == "deny":
        return _criterion(name, "fail", "tool_denied")
    if tool_valid and inputs.tool.outcome == "stop":
        return _criterion(name, "fail", "tool_cancelled" if inputs.tool.reason == "cancelled" else "tool_stopped")
    if not api_valid or inputs.api.disposition != "completed":
        return _unknown(name, "api_outcome_unresolved")
    if not trace_valid or inputs.result.outcome != "allowed" or not inputs.result.transport_completed:
        return _unknown(name, "transport_outcome_unresolved")
    if not tool_valid or inputs.tool.outcome not in ("executed", "replay"):
        return _unknown(name, "tool_outcome_unresolved")
    return _criterion(name, "pass", "typed_outcomes_matched")


def _effect(policy: EvaluationPolicy, inputs: EvaluationInputs, *, tool_valid: bool) -> Criterion:
    name = "effect"
    receipt = inputs.tool.receipt
    recorded_effect = (inputs.tool.evidence.effect if inputs.tool.evidence is not None else
                       inputs.recorded_tool_effect)
    if tool_valid and ((receipt is not None and receipt.effect == "unknown") or recorded_effect == "unknown"):
        return _unknown(name, "possible_effect_unreconciled", next_check="reconcile")
    if policy.expected_postcondition is None:
        return _criterion(name, "not_applicable", "postcondition_not_declared")
    proof = inputs.postconditions
    refs = tuple(item.ref for item in proof)
    if not proof:
        return _unknown(name, "postcondition_missing", next_check="verify_effect")
    if any(not item.authorized or item.origin not in policy.trusted_readback_origins for item in proof):
        return _unknown(name, "postcondition_not_authorized", *refs)
    if any(not item.current or item.revision != policy.links.evidence_revision for item in proof):
        return _unknown(name, "postcondition_stale", *refs)
    if any(item.operation_id != policy.links.correlation[1] for item in proof):
        return _unknown(name, "postcondition_uncorrelated", *refs)
    if tuple(evidence_digest(item) for item in proof) != policy.effect_observation_pins:
        return _unknown(name, "postcondition_snapshot_unpinned", *refs)
    values = {item.observed for item in proof}
    if len(values) != 1:
        return _unknown(name, "postcondition_conflict", *refs, next_check="reconcile")
    if values != {policy.expected_postcondition}:
        return _criterion(name, "fail", "postcondition_mismatch", *refs)
    return _criterion(name, "pass", "postcondition_matched", *refs)


_USAGE_FIELDS = frozenset(field.name for field in fields(UsageObservation))


def _usage(policy: EvaluationPolicy, usage: UsageObservation) -> Criterion:
    name = "usage"
    required = policy.usage_required_fields
    if not required:
        return _criterion(name, "omitted", "usage_not_required_by_fixture")
    if not required <= _USAGE_FIELDS:
        return _unknown(name, "usage_criterion_invalid")
    if any(type(value) is not int or value < 0 for field in _USAGE_FIELDS
           if (value := getattr(usage, field)) is not None):
        return _unknown(name, "usage_observation_invalid")
    known = {field for field in _USAGE_FIELDS if getattr(usage, field) is not None}
    if required <= known:
        return _criterion(name, "pass", "required_usage_reported")
    return _unknown(name, "required_usage_partial" if known else "required_usage_missing")


def _interaction(policy: EvaluationPolicy, inputs: EvaluationInputs) -> Criterion:
    name = "interaction"
    if not policy.interaction_required:
        return _criterion(name, "not_applicable", "interaction_not_declared")
    source = inputs.interaction
    if source is None or not source.ref:
        return _unknown(name, "interaction_reference_missing")
    if evidence_digest(source) != policy.interaction_pin:
        return _unknown(name, "interaction_snapshot_unpinned", source.ref)
    if source.revision != policy.links.evidence_revision:
        return _unknown(name, "interaction_reference_stale", source.ref)
    if source.attempt_id != policy.links.correlation[0] or source.origin != policy.permitted_interaction_origin:
        return _unknown(name, "interaction_reference_uncorrelated", source.ref)
    if source.access != "allowed":
        return _unknown(name, "interaction_access_blocked", source.ref)
    if source.status != "complete":
        return _unknown(name, "interaction_reference_insufficient", source.ref)
    return _criterion(name, "pass", "interaction_reference_sufficient", source.ref)


def _review_check(policy: EvaluationPolicy, inputs: EvaluationInputs, review: SemanticReview,
                  output_sha256: str, available: dict[str, str]) -> Criterion | None:
    name = "semantic"
    if (not review.authorized or review.role != "independent_semantic_fixture"
            or review.id == policy.producer or review.context == policy.producer_context
            or review.author_context != policy.producer_context
            or ReviewAuthority(review.id, review.context) not in policy.reviewers
            or not review.rationale.strip()):
        return _unknown(name, "reviewer_not_independent", review.id, next_check="request_independent_review")
    links, pinned = review.links, policy.links
    if (links.criteria_revision, links.criteria_sha256) != (pinned.criteria_revision, pinned.criteria_sha256):
        return _compared(_unknown(name, "review_rubric_mismatch", review.id,
                                  next_check="request_independent_review"), "independent_fixture_review",
                         (pinned.criteria_revision, pinned.criteria_sha256),
                         (links.criteria_revision, links.criteria_sha256))
    if (links.request_revision != pinned.request_revision or links.result_revision != pinned.result_revision
            or links.tool_receipt_revision != pinned.tool_receipt_revision
            or links.correlation != pinned.correlation or review.output_sha256 != output_sha256):
        return _compared(_unknown(name, "review_result_mismatch", review.id,
                                  next_check="request_independent_review"), "independent_fixture_review",
                         (pinned.request_revision, pinned.result_revision, pinned.tool_receipt_revision,
                          pinned.correlation, output_sha256),
                         (links.request_revision, links.result_revision, links.tool_receipt_revision,
                          links.correlation, review.output_sha256))
    if links.evidence_revision != pinned.evidence_revision:
        return _compared(_unknown(name, "review_evidence_mismatch", review.id,
                                  next_check="request_independent_review"), "independent_fixture_review",
                         pinned.evidence_revision, links.evidence_revision)
    if not review.basis_refs or not set(review.basis_refs) <= available.keys():
        return _compared(_unknown(name, "review_basis_unavailable", review.id, *review.basis_refs),
                         "independent_fixture_review", review.basis_refs,
                         tuple(ref for ref in review.basis_refs if ref in available))
    if tuple(available[ref] for ref in review.basis_refs) != review.basis_pins:
        return _compared(_unknown(name, "review_basis_changed", review.id, *review.basis_refs),
                         "independent_fixture_review",
                         tuple(available[ref] for ref in review.basis_refs), review.basis_pins)
    if evidence_digest(review) not in policy.reviewer_record_pins:
        return _compared(_unknown(name, "review_record_unpinned", review.id), "independent_fixture_review",
                         policy.reviewer_record_pins, (evidence_digest(review),))
    if review.verdict not in ("pass", "fail"):
        return _unknown(name, "review_verdict_unresolved", review.id, next_check="request_independent_review")
    return None


def _semantic(policy: EvaluationPolicy, inputs: EvaluationInputs, output_sha256: str,
              interaction: Criterion) -> Criterion:
    name = "semantic"
    if not policy.semantic_required:
        return _criterion(name, "not_applicable", "semantic_review_not_declared")
    if not inputs.reviews:
        return _unknown(name, "review_unavailable", next_check="request_independent_review")
    available = {inputs.result.evidence_ref: policy.trace_pins[2]}
    available.update((item.ref, evidence_digest(item)) for item in inputs.postconditions
                     if item.authorized and item.current and item.origin in policy.trusted_readback_origins
                     and item.revision == policy.links.evidence_revision
                     and item.operation_id == inputs.result.operation_id
                     and evidence_digest(item) in policy.effect_observation_pins)
    if interaction.outcome == "pass" and inputs.interaction is not None:
        available[inputs.interaction.ref] = evidence_digest(inputs.interaction)
    for review in inputs.reviews:
        failure = _review_check(policy, inputs, review, output_sha256, available)
        if failure is not None:
            return failure
    refs = tuple(review.id for review in inputs.reviews) + tuple(
        ref for review in inputs.reviews for ref in review.basis_refs
    )
    verdicts = {review.verdict for review in inputs.reviews}
    if len(verdicts) > 1:
        return _unknown(name, "independent_review_conflict", *refs, next_check="reconcile")
    if verdicts == {"fail"}:
        return _criterion(name, "fail", "review_objective_mismatch", *refs)
    return _criterion(name, "pass", "independent_review_matched", *refs)


def _aggregate(policy: EvaluationPolicy, inputs: EvaluationInputs, checks: tuple[Criterion, ...]) -> Criterion:
    name = "aggregate"
    revision, digest = policy.links.criteria_revision, policy.links.criteria_sha256
    if inputs.reevaluation is not None:
        link = inputs.reevaluation
        if (link.prior_evaluation_ref == policy.prior_evaluation_ref
                and link.previous_criteria_revision == revision
                and (link.new_criteria_revision, link.new_criteria_sha256) == policy.rubric_successor
                and link.new_evaluation_ref and link.new_evaluation_ref != link.prior_evaluation_ref
                and inputs.links == policy.links):
            return _unknown(name, "existing_evaluation_pinned", link.prior_evaluation_ref,
                            link.new_evaluation_ref, next_check="record_reevaluation_link")
        return _unknown(name, "criteria_change_unlinked")
    if (inputs.links.criteria_revision, inputs.links.criteria_sha256) != (revision, digest):
        return _unknown(name, "criteria_change_unlinked")
    if any(check.outcome == "fail" for check in checks):
        proposal = "reconcile" if any(item.next_check == "reconcile" for item in checks) else "report_only"
        return _criterion(name, "fail", "mandatory_criterion_failed", next_check=proposal)
    pending = tuple(check for check in checks if check.outcome == "unresolved")
    if pending:
        for proposal in ("reconcile", "verify_effect", "verify_evidence", "request_independent_review"):
            if any(check.next_check == proposal for check in pending):
                reason = ("required_review_pending" if all(check.id == "semantic" for check in pending)
                          else "required_evidence_unresolved")
                return _unknown(name, reason, next_check=proposal)
    return _criterion(name, "pass", "all_applicable_criteria_met")


def _compared(check: Criterion, provenance: str, expected: object, observed: object) -> Criterion:
    return replace(check, provenance=provenance, comparison_sha256=(
        _record_digest(expected), _record_digest(observed),
    ))


def _source_evidence(
    policy: EvaluationPolicy, inputs: EvaluationInputs, checks: tuple[Criterion, Criterion, Criterion],
) -> tuple[Criterion, Criterion, Criterion]:
    request, result = inputs.request, inputs.result
    diag = inputs.api.diagnostics
    expected_scope = (policy.assignment.run_id, policy.assignment.work_item_id, policy.assignment.binding_sha256,
                      policy.links.correlation[0], policy.provider_reservation_ref, policy.api_request_sha256)
    observed_scope = (diag.run_id, diag.work_item_id, diag.binding_sha256, diag.attempt_id,
                      diag.reservation_ref, diag.request_sha256)
    attempt, operation, call = policy.links.correlation
    current_tool = None
    if policy.tool_authorization_digests is not None:
        current_tool = ToolCorrelation(
            *(_identifier_digest(ref) for ref in (
                policy.assignment.run_id, policy.assignment.work_item_id, policy.assignment.route_id,
                operation, attempt, call,
            )),
            *policy.tool_authorization_digests,
        )
    receipt, attempt_evidence = inputs.tool.receipt, inputs.tool.evidence
    replay = policy.replay_authorization if inputs.tool.outcome == "replay" else None
    expected_receipt = replay.original if replay is not None else current_tool
    expected_attempt = replay.current if replay is not None else current_tool
    expected_tool = (
        asdict(expected_receipt) if receipt is not None and expected_receipt is not None else None,
        asdict(expected_attempt) if attempt_evidence is not None and expected_attempt is not None else None,
        policy.tool_observation_sha256, replay.return_scope_sha256 if replay is not None else None,
    )
    observed_tool = (asdict(receipt.correlation) if receipt is not None else None,
                     asdict(attempt_evidence.correlation) if attempt_evidence is not None else None,
                     tool_observation_digest(inputs.tool, inputs.recorded_tool_effect), inputs.tool_return_scope_sha256)
    api_payload_digest = None
    if inputs.api.disposition == "completed":
        try:
            parts = tuple(item.text for item in inputs.api.items if isinstance(item, TextItem) and item.kind == "text")
            if parts:
                api_payload_digest = _digest("".join(parts).encode("utf-8"))
        except UnicodeError:
            pass
    expected_api_payload = policy.output_sha256 if inputs.api.disposition == "completed" else None
    observed_trace = (
        _record_digest(request.model_dump(mode="json")),
        _record_digest([event.model_dump(mode="json") for event in inputs.events]),
        _record_digest(result.model_dump(mode="json") if isinstance(result, ExecutionResult) else result),
    )
    return (
        _compared(replace(checks[0], id="v1_identity"), "pinned_v1",
                  (policy.trace_pins, policy.assignment.model_dump(mode="json"), asdict(policy.links)),
                  (observed_trace, request.assignment.model_dump(mode="json"), asdict(inputs.links))),
        _compared(replace(checks[1], id="api_identity"), "normalized_api",
                  (expected_scope, policy.api_observation_sha256, policy.output_sha256, expected_api_payload),
                  (observed_scope, api_observation_digest(inputs.api), _digest(inputs.output_utf8), api_payload_digest)),
        _compared(replace(checks[2], id="tool_identity"), "dispatch_observation", expected_tool, observed_tool),
    )


def _comparison_metadata(
    checks: tuple[Criterion, ...], policy: EvaluationPolicy, inputs: EvaluationInputs,
    sources: tuple[Criterion, ...], effect: str,
) -> tuple[Criterion, ...]:
    source_comparisons = tuple(item.comparison_sha256 for item in sources)
    observed_model = inputs.result.observed_model if isinstance(inputs.result, ExecutionResult) else None
    records = {
        "identity": ("pinned_v1_api_tool", tuple(pair[0] for pair in source_comparisons),
                     tuple(pair[1] for pair in source_comparisons)),
        "model": ("v1_and_normalized_api", (policy.expected_model, policy.expected_model),
                  (observed_model, inputs.api.diagnostics.observed_model)),
        "structure": ("normalized_output", ("objective_string", policy.output_byte_limit),
                      (len(inputs.output_utf8), _digest(inputs.output_utf8))),
        "outcome": ("v1_api_tool", ("completed", "executed_or_replay"),
                    (inputs.api.disposition, inputs.tool.outcome)),
        "effect": ("independent_postcondition", policy.expected_postcondition,
                   (effect, tuple(evidence_digest(item) for item in inputs.postconditions))),
        "usage": ("normalized_api", sorted(policy.usage_required_fields), asdict(inputs.api.usage)),
        "interaction": ("protected_reference_metadata", policy.interaction_pin,
                        evidence_digest(inputs.interaction) if inputs.interaction is not None else None),
        "semantic": ("independent_fixture_review", policy.reviewer_record_pins,
                     tuple(evidence_digest(item) for item in inputs.reviews)),
        "aggregate": ("mandatory_criteria", policy.approved_rules_sha256,
                      tuple((item.id, item.outcome, item.reason) for item in checks if item.id != "aggregate")),
    }
    return tuple(check if check.comparison_sha256 is not None else _compared(check, *records[check.id])
                 for check in checks)


def evaluate_io(policy: EvaluationPolicy, inputs: EvaluationInputs) -> Evaluation:
    """Assess recorded evidence, with successor rubrics accepted only through reevaluate_io."""
    return _evaluate_io(policy, inputs)


def _evaluate_io(
    policy: EvaluationPolicy, inputs: EvaluationInputs, *, linked_previous: str | None = None,
) -> Evaluation:
    output_sha256 = _digest(inputs.output_utf8)
    if isinstance(inputs.interaction, Mapping):
        inputs = replace(inputs, interaction=project_interaction(inputs.interaction))
    if isinstance(inputs.result, dict):
        try:
            parsed_result = ExecutionResult.model_validate(inputs.result)
        except ValueError:
            parsed_result = None
        if parsed_result is not None:
            inputs = replace(inputs, result=parsed_result)

    valid_policy = _policy_valid(policy)
    approved_predecessor = json.loads(policy.rubric_utf8).get("supersedes") if valid_policy else None
    linked = linked_previous is not None or (approved_predecessor is None and policy.previous_evaluation_pin is None)
    if not valid_policy or not linked:
        reason = "effective_rubric_unpinned" if not valid_policy else "reevaluation_link_required"
        trace, assessment = _unknown("identity", reason), "held"
        api = tool = trace
    else:
        if isinstance(inputs.result, dict):
            version = inputs.result.get("version")
            reason = ("unsupported_source_revision" if type(version) is not int or version != 1
                      else "result_schema_unverified")
            trace, assessment = _unknown("identity", reason), "held"
        else:
            trace, assessment = _trace(policy, inputs)
        api, tool = _api_check(policy, inputs), _tool_check(policy, inputs)
        if api.outcome == "pass" and output_sha256 != policy.output_sha256:
            api = _unknown("identity", "result_digest_mismatch")

    source_evidence = _source_evidence(policy, inputs, (trace, api, tool))
    identity = next((check for check in (trace, api, tool) if check.outcome != "pass"), trace)
    trace_valid, trusted_api, trusted_tool = (check.outcome == "pass" for check in (trace, api, tool))
    raw_tool = inputs.tool
    usage = inputs.api.usage if trusted_api else UsageObservation()
    effect = ((raw_tool.evidence.effect if raw_tool.evidence is not None else
               raw_tool.receipt.effect if raw_tool.receipt is not None else
               inputs.recorded_tool_effect or "unverified") if trusted_tool else "unverified")
    entry_observed = trusted_tool and raw_tool.receipt is not None and raw_tool.receipt.effect == "observed"
    if valid_policy and linked:
        interaction = _interaction(policy, inputs)
        semantic = (_semantic(policy, inputs, output_sha256, interaction)
                    if trace_valid and trusted_api and trusted_tool else
                    _unknown("semantic", "review_subject_unverified"))
        checks = (
            identity,
            _model(policy, inputs) if trace_valid and trusted_api else _unknown("model", "model_subject_unverified"),
            _structure(policy, inputs) if trusted_api and inputs.api.disposition == "completed"
            else _unknown("structure", "normalized_output_unverified"),
            _outcome(inputs, trace_valid=trace_valid, api_valid=trusted_api, tool_valid=trusted_tool),
            _effect(policy, inputs, tool_valid=trusted_tool),
            _usage(policy, usage) if trusted_api else _unknown("usage", "api_observation_unverified"),
            interaction,
            semantic,
        )
    else:
        semantic = _unknown("semantic", "upstream_identity_unverified")
        checks = (identity, semantic)
    # Include every identity subcheck so a hidden gap cannot turn into a positive aggregate or conceal reconciliation.
    aggregate = _aggregate(policy, inputs, checks + source_evidence)
    return Evaluation(
        policy.links.criteria_revision, policy.links.criteria_sha256,
        _comparison_metadata(checks + (aggregate,), policy, inputs, source_evidence, effect),
        {"pass": "criteria_met", "fail": "criteria_failed", "unresolved": "criteria_unresolved"}[aggregate.outcome],
        aggregate.next_check, assessment,
        inputs.api.disposition if trusted_api else "unverified",
        raw_tool.outcome if trusted_tool else "unverified",
        effect, entry_observed, usage,
        tuple(_identifier_digest(review.id) for review in inputs.reviews)
        if trace_valid and trusted_api and trusted_tool else (),
        {"unresolved": "pending", "not_applicable": "not_applicable"}.get(semantic.outcome, "reviewed"),
        output_sha256, evaluation_policy_digest(policy), source_evidence, policy.evaluation_ref,
        reevaluation_from=linked_previous, approved_rubric_successor=policy.rubric_successor,
    )


def evaluation_digest(evaluation: Evaluation) -> str:
    return _record_digest(asdict(evaluation))


def reevaluate_io(previous: Evaluation, link: ReevaluationLink, policy: EvaluationPolicy,
                  inputs: EvaluationInputs) -> Evaluation:
    """Evaluate a separately approved successor without rewriting the earlier result."""
    if (
        previous.evaluation_ref != link.prior_evaluation_ref
        or previous.criteria_revision != link.previous_criteria_revision
        or previous.approved_rubric_successor != (link.new_criteria_revision, link.new_criteria_sha256)
        or policy.previous_evaluation_pin != evaluation_digest(previous)
        or policy.prior_evaluation_ref != link.prior_evaluation_ref
        or policy.evaluation_ref != link.new_evaluation_ref
        or policy.evaluation_ref == previous.evaluation_ref
        or not _policy_valid(policy)
        or policy.links.criteria_revision != link.new_criteria_revision
        or policy.links.criteria_sha256 != link.new_criteria_sha256
        or json.loads(policy.rubric_utf8).get("supersedes") != previous.criteria_revision
        or inputs.reevaluation is not None
    ):
        raise ValueError("reevaluation is not linked to the pinned evaluation and approved successor")
    return _evaluate_io(policy, inputs, linked_previous=previous.evaluation_ref)
