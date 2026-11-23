"""Versioned data at the executor boundary. These contracts perform no I/O."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Identifier = Annotated[str, Field(min_length=1)]
Revision = Annotated[int, Field(ge=0)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class ContractRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, revalidate_instances="always")


class VersionedRecord(ContractRecord):
    version: Literal[1]

    @field_validator("version", mode="before")
    @classmethod
    def require_integer_version(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("version must be an integer")
        return value


class AssignmentRef(ContractRecord):
    flow_id: Identifier
    run_id: Identifier
    parent_run_id: Identifier | None = None
    root_run_id: Identifier
    work_item_id: Identifier
    node_id: Identifier
    route_id: Identifier
    route_revision: Revision
    binding_sha256: Digest
    owner_generation: Revision
    execution_id: Identifier


class BudgetLimits(ContractRecord):
    max_attempts: Annotated[int, Field(gt=0)]
    max_input_tokens: Revision
    max_output_tokens: Revision
    deadline_ms: Annotated[int, Field(gt=0)]


class ExecutionRequest(VersionedRecord):
    assignment: AssignmentRef
    criteria_sha256: Digest
    authorization_ref: Identifier
    reservation_ref: Identifier
    budget: BudgetLimits
    cancelled: bool
    selected_model: Identifier | None = None


class ExecutionEvent(VersionedRecord):
    assignment: AssignmentRef
    sequence: Annotated[int, Field(gt=0)]
    attempt_id: Identifier
    operation_id: Identifier
    call_id: Identifier
    kind: Literal["admitted", "dispatched", "receipt", "held"]


class ExecutionResult(VersionedRecord):
    assignment: AssignmentRef
    attempt_id: Identifier
    operation_id: Identifier
    call_id: Identifier
    outcome: Literal["allowed", "refused", "held"]
    transport_completed: bool
    observed_model: Identifier | None = None
    evidence_ref: Identifier

    @model_validator(mode="after")
    def refused_action_has_no_transport(self) -> ExecutionResult:
        if self.outcome == "refused" and self.transport_completed:
            raise ValueError("a refused action cannot have transport completion")
        return self


def validate_trace(
    request: ExecutionRequest, events: Sequence[ExecutionEvent], result: ExecutionResult,
) -> None:
    """Check a complete execution trace before the host considers its result."""
    if result.assignment != request.assignment:
        raise ValueError("result assignment does not match the request")
    attempts: dict[str, tuple[str, str]] = {}
    stages: dict[str, str] = {}
    predecessors = {
        "admitted": (None,),
        "dispatched": ("admitted",),
        "receipt": ("dispatched", "held"),
        "held": ("dispatched",),
    }
    for sequence, event in enumerate(events, 1):
        if event.assignment != request.assignment or event.sequence != sequence:
            raise ValueError("event assignment or sequence does not match the request")
        correlation = (event.operation_id, event.call_id)
        if attempts.setdefault(event.attempt_id, correlation) != correlation:
            raise ValueError("attempt cannot change its operation or call")
        if stages.get(event.attempt_id) not in predecessors[event.kind]:
            raise ValueError("event does not match the preceding call state")
        stages[event.attempt_id] = event.kind

    correlation = attempts.get(result.attempt_id)
    if correlation is not None and correlation != (result.operation_id, result.call_id):
        raise ValueError("result operation or call does not match the attempt")
    stage = stages.get(result.attempt_id)
    if result.transport_completed != (stage == "receipt"):
        raise ValueError("transport completion must match a correlated receipt")
    if result.outcome == "refused" and stage not in (None, "admitted"):
        raise ValueError("refused result cannot follow a dispatch")
    if result.outcome == "allowed" and stage in (None, "held"):
        raise ValueError("allowed result requires a correlated admission without a hold")


def assess_model_result(
    request: ExecutionRequest, events: Sequence[ExecutionEvent], result: ExecutionResult,
) -> Literal["refused", "held", "review_required"]:
    """Apply the model-conformance check without projecting workflow success."""
    if result.assignment != request.assignment or request.cancelled:
        return "held"
    validate_trace(request, events, result)
    if result.outcome != "allowed":
        return result.outcome
    if (
        not result.transport_completed
        or request.selected_model is None
        or result.observed_model is None
        or result.observed_model != request.selected_model
    ):
        return "held"
    return "review_required"
