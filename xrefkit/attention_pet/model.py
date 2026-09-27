"""Versioned, evidence-bearing boundary shared by all display adapters."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Item(Contract):
    id: str = Field(min_length=1, max_length=100)
    kind: Literal["goal", "constraint", "decision", "question", "exception", "history", "conflict"]
    text: str = Field(min_length=1, max_length=2000)
    source: str = Field(min_length=1, max_length=300)
    status: Literal["active", "done", "archived"] = "active"
    depth: int = Field(default=0, ge=0, le=20)
    fixed: bool = False


class Edge(Contract):
    source: str
    target: str
    evidence: str = Field(min_length=1, max_length=500)


class Observation(Contract):
    id: str = Field(min_length=1, max_length=100)
    kind: Literal["validated", "repeated_error", "correction_ignored", "misread_explanation", "decision_contradiction", "intent_drift", "no_improvement", "repeated_failure"]
    evidence: str = Field(min_length=1, max_length=2000)
    context: str = Field(min_length=1, max_length=100)


class WorkingSet(Contract):
    schemaVersion: Literal[1] = 1
    taskId: str = Field(min_length=1, max_length=100)
    contextId: str = Field(min_length=1, max_length=100)
    observedAt: float = Field(ge=0, allow_inf_nan=False)
    coverage: Literal["partial", "reviewed"] = "partial"
    items: list[Item] = Field(max_length=500)
    dependencies: list[Edge] = Field(default_factory=list, max_length=2000)
    observations: list[Observation] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def references_are_valid(self):
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate item id")
        pairs = [(e.source, e.target) for e in self.dependencies]
        if len(pairs) != len(set(pairs)):
            raise ValueError("duplicate dependency")
        for source, target in pairs:
            if source not in ids or target not in ids or source == target:
                raise ValueError("dependency must connect two existing distinct items")
        obs = [o.id for o in self.observations]
        if len(obs) != len(set(obs)):
            raise ValueError("duplicate observation id")
        return self


class Turn(Contract):
    id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=10000)
    items: list[Item] = Field(default_factory=list, max_length=500)
    dependencies: list[Edge] = Field(default_factory=list, max_length=2000)
    observations: list[Observation] = Field(default_factory=list, max_length=500)


class Conversation(Contract):
    taskId: str
    contextId: str
    observedAt: float = Field(ge=0, allow_inf_nan=False)
    coverage: Literal["partial", "reviewed"] = "partial"
    turns: list[Turn] = Field(min_length=1, max_length=200)


class Cause(Contract):
    type: str
    severity: float = Field(ge=0, le=1)
    points: float = Field(ge=0, le=100)


class FeatureChange(Contract):
    feature: str
    delta: int


class Capability(Contract):
    reasoning: float = Field(ge=0, le=100)
    constraint_tracking: float = Field(ge=0, le=100)
    evidence_handling: float = Field(ge=0, le=100)


class Behavior(Contract):
    exploration: float = Field(ge=0, le=1)
    dependency_expansion: float = Field(ge=0, le=1)
    constraint_discovery: float = Field(ge=0, le=1)
    uncertainty_discovery: float = Field(ge=0, le=1)
    alternative_generation: float = Field(ge=0, le=1)
    compression: float = Field(ge=0, le=1)


class ModelProfile(Contract):
    id: str
    label: str
    capability: Capability
    behavior: Behavior
    relative_inference_cost: float = Field(gt=0, allow_inf_nan=False)
    calibration: Literal["uncalibrated"] = "uncalibrated"


class ReasoningDepth(Contract):
    id: str
    capability_modifier: float = Field(ge=-100, le=100)
    exploration_modifier: float = Field(ge=0, allow_inf_nan=False)
    cost_modifier: float = Field(gt=0, allow_inf_nan=False)


class FitCandidate(Contract):
    model: str
    reasoning: str
    expansion: float = Field(ge=0, le=30)
    effectiveRal: float = Field(ge=0, le=130)
    capability: Capability
    requiredCapability: Capability
    shortfalls: list[str]
    meetsRequirements: bool
    relativeInferenceCost: float = Field(gt=0, allow_inf_nan=False)


class Presentation(Contract):
    petState: Literal["Unknown", "Strained", "Balanced", "Relaxed", "Review"]
    headline: str
    summary: str
    shortMessage: str
    detailReason: str
    actionHint: str
    scopeNote: str
    confidenceNote: str
    modelFitLabel: str
    costFitLabel: str
    coverageLabel: str
    confidenceLabel: str
    modelGuide: str
    modelGuideShort: str
    modelGuideDetail: str
    modelGuideStatus: Literal["Unknown", "Available", "NoLowerCandidate", "HoldForReview", "Underpowered"]


class FitEvaluation(Contract):
    version: Literal["fit-experiment-v1"] = "fit-experiment-v1"
    calibration: Literal["uncalibrated"] = "uncalibrated"
    modelFit: Literal["Underpowered", "Sufficient", "Unknown"]
    costFit: Literal["RetryRisk", "NoLowerCostCandidate", "LowerCostCandidateAvailable", "ReviewNeeded", "Unknown"]
    coverage: Literal["partial", "reviewed"] | None = None
    evaluationConfidence: Literal["Unknown", "Low", "Medium", "High"] = "Unknown"
    presentation: Presentation
    baseRal: int | None = Field(default=None, ge=0, le=100)
    selected: FitCandidate | None = None
    profile: ModelProfile | None = None
    depth: ReasoningDepth | None = None
    alternatives: list[FitCandidate] = Field(default_factory=list)
    lowerCostCandidates: list[FitCandidate] = Field(default_factory=list)
    inferenceCostIndex: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    reasons: list[str]
    # No measured prices, failure probabilities, retry or correction estimates.
    expectedTotalCost: None = None
    inferenceCost: None = None
    retryCost: None = None
    correctionCost: None = None
    failureRiskCost: None = None


class AttentionState(Contract):
    schemaVersion: Literal[1]
    evaluatorVersion: Literal["heuristic-v1"]
    measurement: Literal["task-structure-based estimated load"]
    weights: dict[str, float]
    taskId: str
    contextId: str
    observedAt: float
    coverage: Literal["partial", "reviewed"]
    ral: int = Field(ge=0, le=100)
    deltaRal: int | None
    deltaSeconds: float | None
    trajectoryStability: int | None = Field(ge=0, le=100)
    trajectoryEvidence: list[Observation]
    state: Literal["NORMAL", "HIGH LOAD", "WRONG TRAJECTORY", "CRITICAL", "UNKNOWN"]
    loadBand: Literal["stable", "loaded", "strained", "high_pressure", "unstable"]
    expression: Literal["stable", "loaded", "strained", "high_pressure", "unstable", "wrong_trajectory", "unknown"]
    trend: Literal["rapid_rise", "rising", "falling", "steady", "unknown"]
    windowDeltaRal: int | None
    features: dict[str, int]
    changes: list[FeatureChange]
    causes: list[Cause]
    recommendedActions: list[Literal["fix", "summarize", "split", "externalize", "archive", "resolve", "rebase", "restart"]]


def extract(conversation: Conversation) -> WorkingSet:
    """Reduce explicit turn annotations; never pretend to infer free text semantics.

    Items are upserts by stable ID, so status/decision updates replace earlier
    versions. Evidence must refer to an actual supplied turn. Unannotated turns
    make coverage partial. Producers own annotation quality, not this reducer.
    """
    items, edges, observations = {}, {}, {}
    turn_ids = [t.id for t in conversation.turns]
    if len(turn_ids) != len(set(turn_ids)):
        raise ValueError("duplicate turn id")
    for turn in conversation.turns:
        for item in turn.items:
            if item.source not in turn_ids:
                raise ValueError("item source is not a supplied turn")
            items[item.id] = item
        for edge in turn.dependencies:
            edges[edge.source, edge.target] = edge
        for obs in turn.observations:
            observations[obs.id] = obs
    return WorkingSet(
        taskId=conversation.taskId, contextId=conversation.contextId,
        observedAt=conversation.observedAt,
        coverage=(conversation.coverage if all(t.items or t.observations for t in conversation.turns) else "partial"),
        items=list(items.values()), dependencies=list(edges.values()),
        observations=list(observations.values()),
    )
