"""Schema for optional human evaluation at a completed-run boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


EvaluationDecision = Literal[
    "accepted",
    "accepted_with_conditions",
    "correction",
    "rejected_or_returned_to_human",
    "needs_clarification",
]
RelationshipClassification = Literal[
    "continuation",
    "correction",
    "scope_change",
    "new_work",
    "needs_clarification",
]
NextHandling = Literal["continue_next_step", "repair_previous_run", "human_takeover"]
Comparability = Literal["comparable", "gap", "not_assessed"]


class ScopedEvaluation(BaseModel):
    """Optional item/artifact-level finding within one preceding run."""

    model_config = ConfigDict(extra="forbid")

    target: str = Field(min_length=1)
    decision: EvaluationDecision
    note: str = Field(min_length=1)
    linked_targets: list[str] = Field(default_factory=list)

    @field_validator("target", "note", mode="before")
    @classmethod
    def _strip_scalar(cls, value: object) -> object:
        return str(value).strip()

    @field_validator("linked_targets", mode="before")
    @classmethod
    def _strip_links(cls, value: object) -> object:
        if value is None:
            return []
        return [str(item).strip() for item in value if str(item).strip()]


class HumanEvaluation(BaseModel):
    """Human-confirmed disposition; private model reasoning is out of scope."""

    model_config = ConfigDict(extra="forbid")

    preceding_run_id: str = Field(min_length=1)
    decision: EvaluationDecision
    classification: RelationshipClassification
    next_handling: NextHandling
    purpose_fit: str = Field(min_length=1)
    verified_basis: list[str] = Field(min_length=1)
    remaining_uncertainty: list[str] = Field(min_length=1)
    carry_forward: list[str] = Field(default_factory=list)
    linked_targets: list[str] = Field(default_factory=list)
    scoped_findings: list[ScopedEvaluation] = Field(default_factory=list)
    proposed_classification: RelationshipClassification | None = None
    classification_source: Literal["human_confirmed"] = "human_confirmed"
    reviewer: str | None = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    context_refs: list[str] = Field(default_factory=list)
    comparability: Comparability = "not_assessed"
    comparability_gaps: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _require_comparability_reason(self) -> "HumanEvaluation":
        if self.comparability == "gap" and not self.comparability_gaps:
            raise ValueError("comparability=gap requires at least one comparability gap")
        return self

    @field_validator("preceding_run_id", "purpose_fit", "reviewer", mode="before")
    @classmethod
    def _strip_scalar(cls, value: object) -> object:
        return None if value is None else str(value).strip()

    @field_validator(
        "verified_basis", "remaining_uncertainty", "carry_forward", "linked_targets", mode="before"
    )
    @classmethod
    def _strip_list(cls, value: object) -> object:
        if value is None:
            return []
        return [str(item).strip() for item in value if str(item).strip()]
