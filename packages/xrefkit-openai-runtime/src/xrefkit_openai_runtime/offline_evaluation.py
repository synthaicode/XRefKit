"""Evaluate pinned synthetic I/O records without dispatch or workflow projection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, replace
from hashlib import sha256
import json
from typing import Literal

from .contracts import AssignmentRef, ExecutionEvent, ExecutionRequest, ExecutionResult, assess_model_result
from .offline_dispatch import ToolDecision
from .offline_responses import AdapterResult, UsageObservation


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
class EvaluationPolicy:
    """The trusted side supplies this scope and the applicable criteria before evaluation."""

    assignment: AssignmentRef
    links: RevisionLinks
    api_request_sha256: str
    api_observation_sha256: str
    tool_observation_sha256: str
    output_sha256: str
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
    replay_receipt_refs: tuple[str, str] | None = None


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
    postconditions: tuple[EffectObservation, ...] = ()
    interaction: InteractionReference | None = None
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


def _identity(policy: EvaluationPolicy, inputs: EvaluationInputs) -> tuple[Criterion, str]:
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
    try:
        assessment = assess_model_result(request, inputs.events, result)
    except ValueError:
        return _criterion(name, "fail", "trace_order_invalid"), "held"
    diag = inputs.api.diagnostics
    if diag.attempt_id != result.attempt_id:
        return _unknown(name, "attempt_uncorrelated"), assessment
    if (diag.run_id, diag.work_item_id, diag.binding_sha256, diag.reservation_ref, diag.request_sha256) != (
        policy.assignment.run_id, policy.assignment.work_item_id, policy.assignment.binding_sha256,
        request.reservation_ref, policy.api_request_sha256,
    ):
        return _unknown(name, "api_evidence_uncorrelated"), assessment
    if api_observation_digest(inputs.api) != policy.api_observation_sha256:
        return _unknown(name, "api_observation_digest_mismatch"), assessment
    if tool_observation_digest(inputs.tool, inputs.recorded_tool_effect) != policy.tool_observation_sha256:
        return _unknown(name, "tool_observation_digest_mismatch"), assessment
    receipt, evidence = inputs.tool.receipt, inputs.tool.evidence
    observations = tuple(item for item in (receipt, evidence) if item is not None)
    for item in observations:
        link = item.correlation
        attempt_id, call_id = result.attempt_id, result.call_id
        if item is receipt and inputs.tool.outcome == "replay" and policy.replay_receipt_refs is not None:
            attempt_id, call_id = policy.replay_receipt_refs
        for label, actual, expected in (
            ("operation", link.operation_digest, result.operation_id),
            ("call", link.call_digest, call_id),
            ("attempt", link.attempt_digest, attempt_id),
            ("run", link.run_digest, policy.assignment.run_id),
            ("work", link.work_digest, policy.assignment.work_item_id),
            ("route", link.route_digest, policy.assignment.route_id),
        ):
            if actual != _identifier_digest(expected):
                return _unknown(name, f"{label}_uncorrelated"), assessment
        if inputs.recorded_tool_effect is not None and item.effect != inputs.recorded_tool_effect:
            return _unknown(name, "tool_effect_conflict", next_check="reconcile"), assessment
    if receipt is not None:
        if receipt.binding_generation != policy.assignment.owner_generation:
            return _unknown(name, "tool_generation_uncorrelated"), assessment
        if receipt.result_digest is not None and receipt.result_digest != _digest(inputs.tool_return_utf8):
            return _unknown(name, "tool_result_digest_mismatch"), assessment
        if evidence is not None and ((inputs.tool.outcome != "replay" and receipt.correlation != evidence.correlation)
                                     or receipt.action_digest != evidence.action_digest
                                     or receipt.effect != evidence.effect):
            return _unknown(name, "tool_attempt_receipt_conflict", next_check="reconcile"), assessment
        if inputs.tool.outcome in ("executed", "replay"):
            if receipt.effect != "observed" or receipt.outcome != "completed":
                return _unknown(name, "tool_receipt_outcome_unverified"), assessment
            if receipt.result_digest is None:
                return _unknown(name, "tool_result_digest_missing"), assessment
            try:
                returned = json.loads(inputs.tool_return_utf8.decode("utf-8"), object_pairs_hook=_object)
            except (ValueError, RecursionError):
                return _unknown(name, "tool_value_unverified"), assessment
            if (not isinstance(returned, dict) or returned.keys() != {"value"}
                    or inputs.tool.value is None or returned["value"] != inputs.tool.value):
                return _unknown(name, "tool_value_unverified"), assessment
    elif inputs.tool.outcome in ("executed", "replay"):
        return _unknown(name, "tool_receipt_missing"), assessment
    return _criterion(name, "pass", "trace_correlated", result.evidence_ref), assessment


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


def _outcome(inputs: EvaluationInputs) -> Criterion:
    name = "outcome"
    if inputs.api.disposition in ("refusal", "incomplete", "provider_failed", "no_submit"):
        return _criterion(name, "fail", f"api_{inputs.api.disposition}")
    if inputs.api.disposition != "completed":
        return _unknown(name, "api_outcome_unresolved")
    if inputs.result.outcome != "allowed" or not inputs.result.transport_completed:
        return _unknown(name, "transport_outcome_unresolved")
    if inputs.tool.outcome == "deny":
        return _criterion(name, "fail", "tool_denied")
    if inputs.tool.outcome == "stop":
        return _criterion(name, "fail", "tool_cancelled" if inputs.tool.reason == "cancelled" else "tool_stopped")
    if inputs.tool.outcome not in ("executed", "replay"):
        return _unknown(name, "tool_outcome_unresolved")
    return _criterion(name, "pass", "typed_outcomes_matched")


def _effect(policy: EvaluationPolicy, inputs: EvaluationInputs) -> Criterion:
    name = "effect"
    receipt = inputs.tool.receipt
    recorded_effect = (inputs.tool.evidence.effect if inputs.tool.evidence is not None else
                       inputs.recorded_tool_effect)
    if (receipt is not None and receipt.effect == "unknown") or recorded_effect == "unknown":
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
    if any(item.operation_id != inputs.result.operation_id for item in proof):
        return _unknown(name, "postcondition_uncorrelated", *refs)
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
    if source.revision != policy.links.evidence_revision:
        return _unknown(name, "interaction_reference_stale", source.ref)
    if source.attempt_id != inputs.result.attempt_id or source.origin != policy.permitted_interaction_origin:
        return _unknown(name, "interaction_reference_uncorrelated", source.ref)
    if source.access != "allowed":
        return _unknown(name, "interaction_access_blocked", source.ref)
    if source.status != "complete":
        return _unknown(name, "interaction_reference_insufficient", source.ref)
    return _criterion(name, "pass", "interaction_reference_sufficient", source.ref)


def _review_check(policy: EvaluationPolicy, inputs: EvaluationInputs, review: SemanticReview,
                  output_sha256: str, available: set[str]) -> Criterion | None:
    name = "semantic"
    if (not review.authorized or review.role != "independent_semantic_fixture"
            or review.id == policy.producer or review.context == policy.producer_context
            or review.author_context != policy.producer_context
            or ReviewAuthority(review.id, review.context) not in policy.reviewers
            or not review.rationale.strip()):
        return _unknown(name, "reviewer_not_independent", review.id, next_check="request_independent_review")
    links, pinned = review.links, policy.links
    if (links.criteria_revision, links.criteria_sha256) != (pinned.criteria_revision, pinned.criteria_sha256):
        return _unknown(name, "review_rubric_mismatch", review.id, next_check="request_independent_review")
    if (links.request_revision != pinned.request_revision or links.result_revision != pinned.result_revision
            or links.tool_receipt_revision != pinned.tool_receipt_revision
            or links.correlation != pinned.correlation or review.output_sha256 != output_sha256):
        return _unknown(name, "review_result_mismatch", review.id, next_check="request_independent_review")
    if links.evidence_revision != pinned.evidence_revision:
        return _unknown(name, "review_evidence_mismatch", review.id, next_check="request_independent_review")
    if not review.basis_refs or not set(review.basis_refs) <= available:
        return _unknown(name, "review_basis_unavailable", review.id, *review.basis_refs)
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
    available = {inputs.result.evidence_ref}
    available.update(item.ref for item in inputs.postconditions
                     if item.authorized and item.current and item.origin in policy.trusted_readback_origins
                     and item.revision == policy.links.evidence_revision
                     and item.operation_id == inputs.result.operation_id)
    if interaction.outcome == "pass" and inputs.interaction is not None:
        available.add(inputs.interaction.ref)
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


def evaluate_io(policy: EvaluationPolicy, inputs: EvaluationInputs) -> Evaluation:
    """Assess recorded evidence; the return includes only observations and a next-check proposal."""
    raw_result = inputs.result
    output_sha256 = _digest(inputs.output_utf8)
    if isinstance(raw_result, dict):
        try:
            parsed_result = ExecutionResult.model_validate(raw_result)
        except ValueError:
            parsed_result = None
        if parsed_result is None:
            reason = ("unsupported_source_revision" if raw_result.get("version") != 1
                      else "result_schema_unverified")
            identity, assessment = _unknown("identity", reason), "held"
        else:
            inputs = replace(inputs, result=parsed_result)
            identity, assessment = _identity(policy, inputs)
    else:
        identity, assessment = _identity(policy, inputs)
    if identity.outcome == "pass" and output_sha256 != policy.output_sha256:
        identity = _unknown("identity", "result_digest_mismatch")
    if identity.outcome == "pass":
        interaction = _interaction(policy, inputs)
        semantic = _semantic(policy, inputs, output_sha256, interaction)
        checks = (identity, _model(policy, inputs), _structure(policy, inputs), _outcome(inputs),
                  _effect(policy, inputs), _usage(policy, inputs.api.usage), interaction, semantic)
        usage = inputs.api.usage
        effect = (inputs.tool.evidence.effect if inputs.tool.evidence is not None else
                  inputs.tool.receipt.effect if inputs.tool.receipt is not None else
                  inputs.recorded_tool_effect or "unverified")
        entry_observed = inputs.tool.receipt is not None and inputs.tool.receipt.effect == "observed"
        retained = tuple(_identifier_digest(review.id) for review in inputs.reviews)
    else:
        semantic = _unknown("semantic", "upstream_identity_unverified")
        checks = (identity, semantic)
        usage, effect, entry_observed, retained = UsageObservation(), "unverified", False, ()
    aggregate = _aggregate(policy, inputs, checks)
    return Evaluation(
        policy.links.criteria_revision, policy.links.criteria_sha256, checks + (aggregate,),
        {"pass": "criteria_met", "fail": "criteria_failed", "unresolved": "criteria_unresolved"}[aggregate.outcome],
        aggregate.next_check, assessment, inputs.api.disposition, inputs.tool.outcome,
        effect, entry_observed, usage, retained,
        {"unresolved": "pending", "not_applicable": "not_applicable"}.get(semantic.outcome, "reviewed"),
        output_sha256,
    )
