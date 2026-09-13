"""Evidence-bearing pre-workflow routing; no model or business-tool execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1)]
Count = Annotated[int, Field(ge=0)]
Amount = Annotated[float, Field(ge=0, allow_inf_nan=False)]
AXES = {"constraints", "branch_depth", "dependency_depth", "cross_source_links",
        "scope_changes", "integration_links"}


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Source(Record):
    id: Text
    kind: Literal["instruction", "skill", "profile", "data"]
    path: Text
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    bytes: Count


class Evidence(Record):
    source_id: Text
    locator: Text


class AuthorizationRecord(Record):
    action: Text
    scope: Text
    status: Literal["required", "authorized"]
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def authorized_evidence(self):
        if self.status == "authorized" and not self.evidence:
            raise ValueError("authorized external actions require authorization evidence")
        return self


class RemovedStep(Record):
    step_id: Text
    node_id: Text
    definition_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    prior_status: Literal["pending", "done", "blocked", "escalated"]
    reason: Text
    evidence: list[Evidence] = Field(min_length=1)
    authorization: AuthorizationRecord | None = None


class ScopeChange(Record):
    previous_revision: Count
    affected_steps: list[Text] = Field(default_factory=list)
    removed_steps: list[RemovedStep] = Field(default_factory=list)
    reason: Text
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def changed_work_exists(self):
        if not self.affected_steps and not self.removed_steps:
            raise ValueError("scope change requires affected_steps or removed_steps")
        if len(set(self.affected_steps)) != len(self.affected_steps):
            raise ValueError("scope change contains duplicate affected step IDs")
        if len({item.step_id for item in self.removed_steps}) != len(self.removed_steps):
            raise ValueError("scope change contains duplicate removed step tombstones")
        return self


class Measurement(Record):
    value: Count | None
    basis: Literal["measured", "estimated", "unknown"]
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent(self):
        if (self.value is None) != (self.basis == "unknown"):
            raise ValueError("unknown measurements require null; known measurements require a value")
        return self


class Step(Record):
    id: Text
    kind: Literal["deterministic", "model"]
    execution_kind: Literal["analysis", "implementation", "operation"] | None = None
    task: Text
    scope: Text
    evidence: list[Evidence] = Field(min_length=1)
    depends_on: list[Text] = Field(default_factory=list)
    capabilities: list[Text] = Field(default_factory=list)
    metrics: dict[str, Measurement] = Field(default_factory=dict)
    tool_ref: Text | None = None
    node_id: Text | None = None
    authorization: AuthorizationRecord | None = None

    @model_validator(mode="after")
    def execution_boundary(self):
        if self.kind == "deterministic":
            if self.execution_kind is not None or not self.tool_ref or self.capabilities or self.metrics:
                raise ValueError("deterministic steps require tool_ref and no model requirements")
        elif (
            self.execution_kind is None
            or self.tool_ref
            or not self.capabilities
            or set(self.metrics) != AXES
        ):
            raise ValueError(
                "model steps require execution_kind, capabilities and every complexity axis, with no tool_ref"
            )
        return self


class Assessment(Record):
    version: Literal[1]
    request_id: Text
    revision: Count
    environment: Text
    instruction: Text
    sources: list[Source] = Field(min_length=2)
    # null means not assessed; [] means explicitly assessed with no open issues.
    unresolved: list[Text] | None
    steps: list[Step] = Field(min_length=1)
    scope_change: ScopeChange | None = None

    @model_validator(mode="after")
    def references(self):
        source_ids = {s.id for s in self.sources}
        if len(source_ids) != len(self.sources):
            raise ValueError("duplicate source IDs")
        kinds = {s.kind for s in self.sources}
        if not {"instruction", "skill"} <= kinds:
            raise ValueError("instruction and skill sources are required")
        seen: set[str] = set()
        node_ids: set[str] = set()
        for step in self.steps:
            if step.id in seen or not set(step.depends_on) <= seen:
                raise ValueError("steps must have unique IDs and dependencies in execution order")
            seen.add(step.id)
            node_id = step.node_id or step.id
            if node_id in node_ids:
                raise ValueError("steps must have unique node IDs")
            node_ids.add(node_id)
            refs = step.evidence + [e for m in step.metrics.values() for e in m.evidence]
            if step.authorization is not None:
                refs += step.authorization.evidence
            if any(e.source_id not in source_ids for e in refs):
                raise ValueError("evidence references an unknown source")
        if self.scope_change is not None:
            if self.scope_change.previous_revision >= self.revision:
                raise ValueError("scope change must refer to an earlier assessment revision")
            if not set(self.scope_change.affected_steps) <= seen:
                raise ValueError("scope change references an unknown step")
            removed_ids = {item.step_id for item in self.scope_change.removed_steps}
            if removed_ids & seen:
                raise ValueError("removed step tombstones cannot reference current steps")
            scope_refs = self.scope_change.evidence + [
                evidence
                for removed in self.scope_change.removed_steps
                for evidence in (
                    removed.evidence
                    + (removed.authorization.evidence if removed.authorization else [])
                )
            ]
            if any(e.source_id not in source_ids for e in scope_refs):
                raise ValueError("scope change evidence references an unknown source")
        return self


class Candidate(Record):
    id: Text
    cost_tier: Count
    priority: Count
    capabilities: list[Text]
    limits: dict[str, Count]
    evaluation_ref: Text
    max_input_bytes: Count

    @model_validator(mode="after")
    def axes(self):
        if set(self.limits) != AXES:
            raise ValueError("candidate limits must cover every complexity axis")
        return self


class Policy(Record):
    version: Text
    environment: Text
    host: Literal["generic", "vscode_copilot"]
    parent_model_id: Text | None = None
    parent_cost_tier: Count | None = None
    selection_strategy: Literal["priority", "lowest_cost_eligible"] = "priority"
    candidates: list[Candidate] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_host(self):
        if self.host == "vscode_copilot" and (
            self.parent_model_id is None or self.parent_cost_tier is None
        ):
            raise ValueError("Copilot policy requires parent_model_id and parent_cost_tier")
        if len({c.id for c in self.candidates}) != len(self.candidates):
            raise ValueError("duplicate model IDs")
        return self


class DispatchPlan(Record):
    step_id: Text
    parent_model: Text
    selected_model: Text
    agent_role: Literal["implementation_subagent", "operational_subagent"]
    rationale: Text
    parent_execution: Literal["prohibited"]
    dispatch_owner: Literal["client_host"]


class OutcomeEvidence(Record):
    ref: Text
    summary: Text


class RerouteMeasurement(Record):
    value: Count | None
    basis: Literal["measured", "estimated", "unknown"]
    evidence: list[OutcomeEvidence] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent(self):
        if (self.value is None) != (self.basis == "unknown"):
            raise ValueError("unknown reroute measurements require null; known measurements require a value")
        return self


class FailureReport(Record):
    id: Text
    category: Literal["tool", "ci", "security", "dependency", "other"]
    disposition: Literal["deterministic_retry", "model_reroute"]
    known_transient: bool
    classification_evidence: list[OutcomeEvidence] = Field(min_length=1)
    retry_tool_ref: Text | None = None
    revised_scope: Text | None = None
    recovery_execution_kind: Literal["analysis", "implementation"] | None = None
    required_capabilities: list[Text] = Field(default_factory=list)
    metrics: dict[str, RerouteMeasurement] = Field(default_factory=dict)
    minimum_cost_tier: Count | None = None

    @model_validator(mode="after")
    def complete_classification(self):
        if self.disposition == "deterministic_retry":
            if not self.known_transient or not self.retry_tool_ref:
                raise ValueError("deterministic retry requires known_transient=true and retry_tool_ref")
            if (self.revised_scope is not None or self.recovery_execution_kind is not None
                    or self.required_capabilities or self.metrics or self.minimum_cost_tier is not None):
                raise ValueError("deterministic retry cannot carry model reroute requirements")
        elif (
            self.known_transient
            or self.retry_tool_ref is not None
            or self.revised_scope is None
            or self.recovery_execution_kind is None
            or not self.required_capabilities
            or set(self.metrics) != AXES
            or self.minimum_cost_tier is None
        ):
            raise ValueError(
                "model reroute requires unexpected failure evidence, revised scope, execution kind, "
                "capabilities, every complexity axis, and minimum_cost_tier"
            )
        return self


class ActiveAssignment(Record):
    route_id: Text
    route_revision: Count
    kind: Literal["deterministic", "model"]
    task: Text
    scope: Text
    execution_kind: Literal["analysis", "implementation", "operation"] | None = None
    tool_ref: Text | None = None
    selected_model: Text | None = None
    selected_cost_tier: Count | None = None
    evaluation_ref: Text | None = None
    policy_version: Text
    selection_strategy: Literal["priority", "lowest_cost_eligible"]
    authorization: AuthorizationRecord | None = None

    @model_validator(mode="after")
    def assignment_boundary(self):
        if self.kind == "deterministic":
            if (
                not self.tool_ref
                or self.execution_kind is not None
                or self.selected_model is not None
                or self.selected_cost_tier is not None
                or self.evaluation_ref is not None
            ):
                raise ValueError("deterministic assignment requires only a tool reference")
        elif (
            self.tool_ref is not None
            or self.execution_kind is None
            or self.selected_model is None
            or self.selected_cost_tier is None
            or self.evaluation_ref is None
        ):
            raise ValueError("model assignment requires model, tier, evaluation, and execution kind")
        return self


class RouteObservation(Record):
    route_id: Text
    route_revision: Count
    selected_model: Text | None
    observed_model: Text | None
    selected_cost_tier: Count | None
    evaluation_ref: Text | None
    route_evidence: Text
    outcome: Literal["succeeded", "failed", "blocked", "escalated"]
    evidence: list[OutcomeEvidence] = Field(min_length=1)


class WorkItemState(Record):
    step_id: Text
    node_id: Text
    definition_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    status: Literal["pending", "in_progress", "done", "blocked", "escalated"]
    route_revision: Count = 0
    authorization: AuthorizationRecord | None = None
    assignment: ActiveAssignment | None = None
    reroute_requirement: FailureReport | None = None
    observations: list[RouteObservation] = Field(default_factory=list)
    failure_history: list[FailureReport] = Field(default_factory=list)
    completion_evidence: list[OutcomeEvidence] = Field(default_factory=list)
    resolution_evidence: list[OutcomeEvidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def state_boundary(self):
        if (self.status == "in_progress") != (self.assignment is not None):
            raise ValueError("only in-progress work items may have an active assignment")
        if self.status == "done" and not self.completion_evidence:
            raise ValueError("completed work items require completion evidence")
        if self.reroute_requirement is not None and self.status not in {"pending", "in_progress"}:
            raise ValueError("reroute requirements belong only to pending or in-progress work")
        return self


class RetiredWorkItem(Record):
    removed_in_revision: Count
    tombstone: RemovedStep
    item: WorkItemState

    @model_validator(mode="after")
    def matches_tombstone(self):
        if (
            self.item.step_id != self.tombstone.step_id
            or self.item.node_id != self.tombstone.node_id
            or self.item.definition_sha256 != self.tombstone.definition_sha256
            or self.item.status != self.tombstone.prior_status
            or self.item.authorization != self.tombstone.authorization
        ):
            raise ValueError("retired work item does not match its tombstone")
        return self


class WorkflowState(Record):
    version: Literal[1]
    request_id: Text
    assessment_revision: Count
    assessment_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    environment: Text
    items: list[WorkItemState] = Field(min_length=1)
    retired_items: list[RetiredWorkItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_items(self):
        if len({item.step_id for item in self.items}) != len(self.items):
            raise ValueError("workflow state contains duplicate work item IDs")
        if len({item.node_id for item in self.items}) != len(self.items):
            raise ValueError("workflow state contains duplicate node IDs")
        retired_ids = [item.item.step_id for item in self.retired_items]
        if len(set(retired_ids)) != len(retired_ids):
            raise ValueError("workflow state contains duplicate retired work item IDs")
        if set(retired_ids) & {item.step_id for item in self.items}:
            raise ValueError("active and retired work item IDs cannot overlap")
        if sum(item.status == "in_progress" for item in self.items) > 1:
            raise ValueError("stateless workflow state permits at most one active assignment")
        return self


class WorkItemResult(Record):
    version: Literal[1]
    request_id: Text
    assessment_revision: Count
    step_id: Text
    node_id: Text
    route_id: Text
    route_revision: Count
    outcome: Literal["succeeded", "failed", "blocked", "escalated"]
    observed_model: Text | None = None
    route_evidence: Text
    evidence: list[OutcomeEvidence] = Field(min_length=1)
    failure: FailureReport | None = None
    resolves_failure_id: Text | None = None
    resolution_evidence: list[OutcomeEvidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def result_boundary(self):
        if (self.outcome == "failed") != (self.failure is not None):
            raise ValueError("failed results require one failure report and other outcomes prohibit it")
        if self.resolves_failure_id is not None:
            if self.outcome != "succeeded" or not self.resolution_evidence:
                raise ValueError("failure resolution requires a succeeded result and resolution evidence")
        elif self.resolution_evidence:
            raise ValueError("resolution evidence requires resolves_failure_id")
        return self


class WorkItemDispatchPlan(Record):
    work_item_id: Text
    node_id: Text
    route_id: Text
    route_revision: Count
    parent_model: Text
    selected_model: Text
    selected_cost_tier: Count
    agent_role: Literal["implementation_subagent", "operational_subagent"]
    task: Text
    scope: Text
    rationale: Text
    parent_execution: Literal["prohibited"]
    dispatch_owner: Literal["client_host"]
    authorization: AuthorizationRecord | None
    dispatch_ready: bool


def snapshot(path: Path, kind: str, source_id: str) -> dict:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return {"id": source_id, "kind": kind, "path": str(path.resolve()),
            "sha256": digest.hexdigest(), "bytes": size}


def route(assessment: Assessment, policy: Policy, *, current_sources: list[Source] | None = None) -> dict:
    """Filter by capability, per-axis limits and host tier; never invent scores."""
    issues = list(assessment.unresolved or [])
    if assessment.environment != policy.environment:
        issues.append("assessment and model policy belong to different environments")
    if assessment.unresolved is None:
        issues.append("scope and instruction conflicts have not been assessed")
    if not policy.parent_model_id:
        if any(step.execution_kind == "implementation" for step in assessment.steps):
            issues.append("parent_model_id is required before implementation subagent dispatch")
        elif any(step.execution_kind == "operation" for step in assessment.steps):
            issues.append("parent_model_id is required before operational subagent dispatch")
    if current_sources is not None:
        # Remote MCP source paths belong to the client, never the server.
        expected = {s.id: s.model_dump() for s in assessment.sources}
        current = {s.id: s.model_dump() for s in current_sources}
        if len(current) != len(current_sources) or current != expected:
            issues.append("client source snapshot changed; reassess this revision")
        instruction_bytes = assessment.instruction.encode("utf-8")
        instruction_sources = [s for s in assessment.sources if s.kind == "instruction"]
        if len(instruction_sources) != 1 or any(
            s.sha256 != hashlib.sha256(instruction_bytes).hexdigest()
            or s.bytes != len(instruction_bytes) for s in instruction_sources
        ):
            issues.append("instruction does not match its canonical UTF-8 client snapshot")
    else:
        for source in assessment.sources:
            actual = snapshot(Path(source.path), source.kind, source.id)
            if actual["sha256"] != source.sha256 or actual["bytes"] != source.bytes:
                issues.append(f"source changed: {source.id}; reassess this revision")
            if source.kind == "instruction" and Path(source.path).read_text(encoding="utf-8-sig") != assessment.instruction:
                issues.append(f"instruction does not match source: {source.id}")
    decisions = []
    dispatches: list[DispatchPlan] = []
    upgrade_options: dict[str, list[Candidate]] = {}
    model_step_without_route = False
    authorization_required_steps: list[str] = []
    selection_key = ((lambda candidate: (candidate.cost_tier, candidate.priority, candidate.id))
                     if policy.selection_strategy == "lowest_cost_eligible"
                     else (lambda candidate: (candidate.priority, candidate.id)))
    for step in assessment.steps:
        if step.kind == "deterministic":
            decision = {"step_id": step.id, "kind": step.kind, "tool_ref": step.tool_ref}
            if step.authorization is not None:
                decision["authorization"] = step.authorization.model_dump()
                decision["execution_authorized"] = step.authorization.status == "authorized"
                if step.authorization.status == "required":
                    authorization_required_steps.append(step.id)
            decisions.append(decision)
            continue
        unknown = [axis for axis, metric in step.metrics.items() if metric.value is None]
        rejected = {}
        eligible = []
        blocked_only_by_parent = []
        for candidate in policy.candidates:
            intrinsic_reasons = []
            if sum(s.bytes for s in assessment.sources) > candidate.max_input_bytes:
                intrinsic_reasons.append("exceeds evaluated input byte limit")
            missing = sorted(set(step.capabilities) - set(candidate.capabilities))
            if missing:
                intrinsic_reasons.append("missing capabilities: " + ", ".join(missing))
            if unknown:
                intrinsic_reasons.append("unknown complexity: " + ", ".join(sorted(unknown)))
            for axis, metric in step.metrics.items():
                if metric.value is not None and metric.value > candidate.limits[axis]:
                    intrinsic_reasons.append(f"exceeds {axis}")
            parent_blocked = (
                not intrinsic_reasons
                and policy.host == "vscode_copilot"
                and candidate.cost_tier > policy.parent_cost_tier
            )
            reasons = list(intrinsic_reasons)
            if parent_blocked:
                reasons.append("exceeds Copilot parent cost tier")
                blocked_only_by_parent.append(candidate)
            if reasons:
                rejected[candidate.id] = reasons
            else:
                eligible.append(candidate)
        chosen = min(eligible, key=selection_key) if eligible and not issues else None
        if not eligible:
            if blocked_only_by_parent:
                upgrade_options[step.id] = blocked_only_by_parent
            else:
                model_step_without_route = True
        decision = {"step_id": step.id, "kind": step.kind,
                    "model": chosen.id if chosen else None,
                    "evaluation_ref": chosen.evaluation_ref if chosen else None,
                    "rejected": rejected}
        if step.authorization is not None:
            decision["authorization"] = step.authorization.model_dump()
            decision["execution_authorized"] = step.authorization.status == "authorized"
            if step.authorization.status == "required":
                authorization_required_steps.append(step.id)
        decisions.append(decision)
        if (chosen is not None and step.execution_kind in {"implementation", "operation"}
                and (step.authorization is None or step.authorization.status == "authorized")):
            role = ("implementation_subagent" if step.execution_kind == "implementation"
                    else "operational_subagent")
            dispatches.append(DispatchPlan(
                step_id=step.id,
                parent_model=policy.parent_model_id,
                selected_model=chosen.id,
                agent_role=role,
                rationale=(
                    f"The step is classified as {step.execution_kind} and the evaluated policy selected "
                    f"{chosen.id}; the parent remains the gateway/coordinator."
                ),
                parent_execution="prohibited",
                dispatch_owner="client_host",
            ))
    upgrade = None
    if not issues and not model_step_without_route and upgrade_options:
        required_tier = max(min(c.cost_tier for c in candidates)
                            for candidates in upgrade_options.values())
        workers = []
        for step_id, candidates in upgrade_options.items():
            callable_at_tier = [c for c in candidates if c.cost_tier <= required_tier]
            selected = min(callable_at_tier, key=selection_key)
            workers.append({"step_id": step_id, "model": selected.id,
                            "cost_tier": selected.cost_tier,
                            "evaluation_ref": selected.evaluation_ref})
        upgrade = {
            "proposal_only": True,
            "action": "user_selects_conversation_model",
            "current_conversation_model": policy.parent_model_id,
            "current_cost_tier": policy.parent_cost_tier,
            "required_minimum_tier": required_tier,
            "affected_steps": sorted(upgrade_options),
            "workers_callable_after_upgrade": workers,
            "reason": "evaluated workers satisfy task requirements but exceed the current conversation cost tier",
            "resume": {"request_id": assessment.request_id,
                       "revision": assessment.revision,
                       "tool": "route_instruction_gateway",
                       "rule": "select a conversation model at or above required_minimum_tier, refresh source snapshots, update the environment policy, and rerun routing"},
        }
    if issues or model_step_without_route:
        status = "needs_assessment"
    elif upgrade is not None:
        status = "conversation_upgrade_required"
    elif authorization_required_steps:
        status = "authorization_required"
    else:
        status = "ready"
    return {"schema_version": 1, "status": status,
            "request_id": assessment.request_id, "revision": assessment.revision,
            "environment": assessment.environment,
            "policy_version": policy.version, "issues": issues, "decisions": decisions,
            "assessment": assessment.model_dump(), "policy": policy.model_dump(),
            "dispatch_status": ("subagent_dispatch_required" if dispatches
                                else ("authorization_required" if authorization_required_steps
                                      else "not_dispatched")),
            "subagent_dispatches": [dispatch.model_dump() for dispatch in dispatches],
            "authorization_required_steps": authorization_required_steps,
            "conversation_upgrade": upgrade,
            "source_verification": "client_reported_snapshot" if current_sources is not None else "local_files",
            "workflow_rule": "Start the existing workflow/Skill envelope before executing any step; preserve all gates."}


def _stable_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _assessment_hash(assessment: Assessment) -> str:
    return _stable_hash(assessment.model_dump())


def _step_definition_hash(step: Step) -> str:
    # Authorization may be refreshed without redefining the work itself.
    definition = step.model_dump(exclude={"authorization"})
    return _stable_hash(definition)


def initialize_workflow(
    assessment: Assessment,
    *,
    previous_state: WorkflowState | None = None,
) -> dict:
    """Create or explicitly re-enter per-node workflow state without reopening work silently."""
    step_hashes = {step.id: _step_definition_hash(step) for step in assessment.steps}
    if previous_state is None:
        items = [WorkItemState(
            step_id=step.id,
            node_id=step.node_id or step.id,
            definition_sha256=step_hashes[step.id],
            status="pending",
            authorization=step.authorization,
        ) for step in assessment.steps]
        retired_items: list[RetiredWorkItem] = []
        mode = "initialized"
    else:
        if assessment.request_id != previous_state.request_id:
            raise ValueError("workflow re-entry must retain request_id")
        if assessment.environment != previous_state.environment:
            raise ValueError("workflow re-entry must retain environment")
        if assessment.revision <= previous_state.assessment_revision:
            raise ValueError("workflow re-entry requires a newer assessment revision")
        previous = {item.step_id: item for item in previous_state.items}
        current_ids = set(step_hashes)
        previous_ids = set(previous)
        changed = {
            step_id for step_id in current_ids & previous_ids
            if step_hashes[step_id] != previous[step_id].definition_sha256
        }
        structural = changed | (current_ids - previous_ids) | (previous_ids - current_ids)
        scope_change = assessment.scope_change
        affected = set(scope_change.affected_steps) if scope_change is not None else set()
        if structural and scope_change is None:
            raise ValueError("changed workflow definitions require explicit scope_change evidence")
        if scope_change is not None:
            if scope_change.previous_revision != previous_state.assessment_revision:
                raise ValueError("scope_change previous_revision does not match workflow state")
            if not changed <= affected or not (current_ids - previous_ids) <= affected:
                raise ValueError("every changed or added work item must be named by scope_change")
        if any(item.status == "in_progress" for item in previous_state.items):
            raise ValueError("workflow re-entry cannot replace an in-progress assignment")
        removed_ids = previous_ids - current_ids
        tombstones = ({removed.step_id: removed for removed in scope_change.removed_steps}
                      if scope_change is not None else {})
        if set(tombstones) != removed_ids:
            raise ValueError("removed work items require one exact scope_change tombstone each")
        retired_items = [item.model_copy(deep=True) for item in previous_state.retired_items]
        for step_id in sorted(removed_ids):
            prior = previous[step_id]
            tombstone = tombstones[step_id]
            if (
                tombstone.node_id != prior.node_id
                or tombstone.definition_sha256 != prior.definition_sha256
                or tombstone.prior_status != prior.status
                or tombstone.authorization != prior.authorization
            ):
                raise ValueError("removed work item tombstone does not match prior state")
            retired_items.append(RetiredWorkItem(
                removed_in_revision=assessment.revision,
                tombstone=tombstone,
                item=prior.model_copy(deep=True),
            ))
        items = []
        for step in assessment.steps:
            prior = previous.get(step.id)
            if prior is None:
                items.append(WorkItemState(
                    step_id=step.id,
                    node_id=step.node_id or step.id,
                    definition_sha256=step_hashes[step.id],
                    status="pending",
                    authorization=step.authorization,
                ))
                continue
            if step.id in affected:
                items.append(WorkItemState(
                    step_id=step.id,
                    node_id=step.node_id or step.id,
                    definition_sha256=step_hashes[step.id],
                    status="pending",
                    route_revision=prior.route_revision + 1,
                    authorization=step.authorization,
                    observations=prior.observations,
                    failure_history=prior.failure_history,
                    completion_evidence=prior.completion_evidence,
                    resolution_evidence=prior.resolution_evidence,
                ))
            else:
                if step_hashes[step.id] != prior.definition_sha256:
                    raise ValueError("changed work item is missing from scope_change")
                if (step.node_id or step.id) != prior.node_id:
                    raise ValueError("node identity changes require an affected scope_change entry")
                carried = prior.model_copy(deep=True)
                carried.authorization = step.authorization
                items.append(carried)
        mode = "reentered"
    state = WorkflowState(
        version=1,
        request_id=assessment.request_id,
        assessment_revision=assessment.revision,
        assessment_sha256=_assessment_hash(assessment),
        environment=assessment.environment,
        items=items,
        retired_items=retired_items,
    )
    return {
        "schema_version": 1,
        "status": mode,
        "workflow_state": state.model_dump(),
        "next_tool": "route_instruction_work_items",
        "reentry_rule": (
            "Completed nodes remain completed unless a newer assessment revision names them in "
            "scope_change with evidence."
        ),
    }


def _validate_workflow_state(assessment: Assessment, state: WorkflowState) -> None:
    if state.request_id != assessment.request_id:
        raise ValueError("workflow state request_id does not match assessment")
    if state.assessment_revision != assessment.revision:
        raise ValueError("workflow state assessment revision is stale")
    if state.environment != assessment.environment:
        raise ValueError("workflow state environment does not match assessment")
    if state.assessment_sha256 != _assessment_hash(assessment):
        raise ValueError("workflow state assessment snapshot is stale")
    expected = [(step.id, step.node_id or step.id, _step_definition_hash(step), step.authorization)
                for step in assessment.steps]
    actual = [(item.step_id, item.node_id, item.definition_sha256, item.authorization)
              for item in state.items]
    if expected != actual:
        raise ValueError("workflow state work items do not match assessment order and definitions")


def _source_issues(
    assessment: Assessment,
    policy: Policy,
    current_sources: list[Source] | None,
) -> list[str]:
    issues = list(assessment.unresolved or [])
    if assessment.unresolved is None:
        issues.append("scope and instruction conflicts have not been assessed")
    if assessment.environment != policy.environment:
        issues.append("assessment and model policy belong to different environments")
    if current_sources is not None:
        expected = {source.id: source.model_dump() for source in assessment.sources}
        current = {source.id: source.model_dump() for source in current_sources}
        if len(current) != len(current_sources) or current != expected:
            issues.append("client source snapshot changed; reassess this revision")
        data = assessment.instruction.encode("utf-8")
        instructions = [source for source in assessment.sources if source.kind == "instruction"]
        if len(instructions) != 1 or any(
            source.sha256 != hashlib.sha256(data).hexdigest() or source.bytes != len(data)
            for source in instructions
        ):
            issues.append("instruction does not match its canonical UTF-8 client snapshot")
    else:
        for source in assessment.sources:
            actual = snapshot(Path(source.path), source.kind, source.id)
            if actual["sha256"] != source.sha256 or actual["bytes"] != source.bytes:
                issues.append(f"source changed: {source.id}; reassess this revision")
            if source.kind == "instruction" and Path(source.path).read_text(
                encoding="utf-8-sig"
            ) != assessment.instruction:
                issues.append(f"instruction does not match source: {source.id}")
    return issues


def _route_id(
    assessment: Assessment,
    item: WorkItemState,
    policy: Policy,
    target: str,
) -> str:
    key = {
        "request_id": assessment.request_id,
        "assessment_revision": assessment.revision,
        "step_id": item.step_id,
        "node_id": item.node_id,
        "route_revision": item.route_revision,
        "policy_version": policy.version,
        "target": target,
    }
    return "route-" + _stable_hash(key)[:20]


def route_work_items(
    assessment: Assessment,
    policy: Policy,
    state: WorkflowState,
    *,
    current_sources: list[Source] | None = None,
) -> dict:
    """Route only ready pending nodes; every returned state is the next re-entry token."""
    _validate_workflow_state(assessment, state)
    issues = _source_issues(assessment, policy, current_sources)
    steps = {step.id: step for step in assessment.steps}
    items = {item.step_id: item for item in state.items}
    active_assignment_exists = any(item.status == "in_progress" for item in state.items)
    dependency_ready = [
        item for item in state.items
        if item.status == "pending"
        and all(items[dependency].status == "done" for dependency in steps[item.step_id].depends_on)
    ] if not active_assignment_exists else []
    # This API is stateless and returns whole-state replacements. Route one node
    # at a time so two results cannot race and erase each other's state.
    ready = dependency_ready[:1]
    if any(steps[item.step_id].execution_kind in {"implementation", "operation"}
           or (item.reroute_requirement is not None
               and item.reroute_requirement.disposition == "model_reroute"
               and item.reroute_requirement.recovery_execution_kind == "implementation")
           for item in ready) and not policy.parent_model_id:
        issues.append("parent_model_id is required before implementation or operational subagent dispatch")

    total_bytes = sum(source.bytes for source in assessment.sources)
    decisions: list[dict] = []
    proposals: list[tuple[WorkItemState, ActiveAssignment, Step, Candidate | None]] = []
    dispatch_proposals: list[tuple[WorkItemState, ActiveAssignment, Step, Candidate]] = []
    upgrade_options: dict[str, list[Candidate]] = {}
    model_without_route = False
    authorization_blocked = False
    selection_key = ((lambda candidate: (candidate.cost_tier, candidate.priority, candidate.id))
                     if policy.selection_strategy == "lowest_cost_eligible"
                     else (lambda candidate: (candidate.priority, candidate.id)))

    for item in state.items:
        step = steps[item.step_id]
        if item.status != "pending":
            decisions.append({"work_item_id": item.step_id, "node_id": item.node_id,
                              "state": item.status, "dispatch": "not_pending"})
            continue
        if item not in ready:
            wait_reason = (
                "waiting_active_result" if active_assignment_exists
                else ("waiting_serial_turn" if item in dependency_ready
                      else "waiting_dependencies")
            )
            decisions.append({"work_item_id": item.step_id, "node_id": item.node_id,
                              "state": "pending", "dispatch": wait_reason})
            continue
        requirement = item.reroute_requirement
        authorization = step.authorization
        authorized = authorization is None or authorization.status == "authorized"
        if requirement is not None and requirement.disposition == "deterministic_retry":
            tool_ref = requirement.retry_tool_ref
            assignment = ActiveAssignment(
                route_id=_route_id(assessment, item, policy, tool_ref),
                route_revision=item.route_revision,
                kind="deterministic",
                task=f"Retry {step.task} after classified transient failure {requirement.id}",
                scope=step.scope,
                tool_ref=tool_ref,
                policy_version=policy.version,
                selection_strategy=policy.selection_strategy,
                authorization=authorization,
            )
            decisions.append({"work_item_id": item.step_id, "node_id": item.node_id,
                              "kind": "deterministic", "tool_ref": tool_ref,
                              "failure_id": requirement.id,
                              "authorization": authorization.model_dump() if authorization else None,
                              "execution_authorized": authorized})
            if authorized:
                proposals.append((item, assignment, step, None))
            else:
                authorization_blocked = True
            continue
        if step.kind == "deterministic" and requirement is None:
            assignment = ActiveAssignment(
                route_id=_route_id(assessment, item, policy, step.tool_ref),
                route_revision=item.route_revision,
                kind="deterministic",
                task=step.task,
                scope=step.scope,
                tool_ref=step.tool_ref,
                policy_version=policy.version,
                selection_strategy=policy.selection_strategy,
                authorization=authorization,
            )
            decisions.append({"work_item_id": item.step_id, "node_id": item.node_id,
                              "kind": "deterministic", "tool_ref": step.tool_ref,
                              "authorization": authorization.model_dump() if authorization else None,
                              "execution_authorized": authorized})
            if authorized:
                proposals.append((item, assignment, step, None))
            else:
                authorization_blocked = True
            continue

        if requirement is not None:
            capabilities = requirement.required_capabilities
            metrics = requirement.metrics
            task = f"Diagnose and resolve {requirement.category} failure {requirement.id}"
            scope = requirement.revised_scope
            execution_kind = requirement.recovery_execution_kind
            minimum_tier = requirement.minimum_cost_tier
        else:
            capabilities = step.capabilities
            metrics = step.metrics
            task = step.task
            scope = step.scope
            execution_kind = step.execution_kind
            minimum_tier = None
        unknown = [axis for axis, metric in metrics.items() if metric.value is None]
        rejected: dict[str, list[str]] = {}
        eligible: list[Candidate] = []
        parent_blocked: list[Candidate] = []
        for candidate in policy.candidates:
            reasons: list[str] = []
            if total_bytes > candidate.max_input_bytes:
                reasons.append("exceeds evaluated input byte limit")
            missing = sorted(set(capabilities) - set(candidate.capabilities))
            if missing:
                reasons.append("missing capabilities: " + ", ".join(missing))
            if unknown:
                reasons.append("unknown complexity: " + ", ".join(sorted(unknown)))
            if minimum_tier is not None and candidate.cost_tier < minimum_tier:
                reasons.append("below failure escalation minimum cost tier")
            for axis, metric in metrics.items():
                if metric.value is not None and metric.value > candidate.limits[axis]:
                    reasons.append(f"exceeds {axis}")
            blocked_by_parent = (
                not reasons
                and policy.host == "vscode_copilot"
                and candidate.cost_tier > policy.parent_cost_tier
            )
            if blocked_by_parent:
                reasons.append("exceeds Copilot parent cost tier")
                parent_blocked.append(candidate)
            if reasons:
                rejected[candidate.id] = reasons
            else:
                eligible.append(candidate)
        chosen = min(eligible, key=selection_key) if eligible and not issues else None
        if not eligible:
            if parent_blocked:
                upgrade_options[item.step_id] = parent_blocked
            else:
                model_without_route = True
        decision = {
            "work_item_id": item.step_id,
            "node_id": item.node_id,
            "kind": "model",
            "model": chosen.id if chosen else None,
            "cost_tier": chosen.cost_tier if chosen else None,
            "evaluation_ref": chosen.evaluation_ref if chosen else None,
            "selection_strategy": policy.selection_strategy,
            "reroute_failure_id": requirement.id if requirement else None,
            "rejected": rejected,
            "authorization": authorization.model_dump() if authorization else None,
            "execution_authorized": authorized,
        }
        decisions.append(decision)
        if chosen is not None:
            assignment = ActiveAssignment(
                route_id=_route_id(assessment, item, policy, chosen.id),
                route_revision=item.route_revision,
                kind="model",
                task=task,
                scope=scope,
                execution_kind=execution_kind,
                selected_model=chosen.id,
                selected_cost_tier=chosen.cost_tier,
                evaluation_ref=chosen.evaluation_ref,
                policy_version=policy.version,
                selection_strategy=policy.selection_strategy,
                authorization=authorization,
            )
            if authorized:
                proposals.append((item, assignment, step, chosen))
                if execution_kind in {"implementation", "operation"}:
                    dispatch_proposals.append((item, assignment, step, chosen))
            else:
                authorization_blocked = True

    upgrade = None
    if not issues and not model_without_route and upgrade_options:
        required_tier = max(min(candidate.cost_tier for candidate in candidates)
                            for candidates in upgrade_options.values())
        workers = []
        for step_id, candidates in upgrade_options.items():
            callable_at_tier = [candidate for candidate in candidates
                                if candidate.cost_tier <= required_tier]
            selected = min(callable_at_tier, key=selection_key)
            workers.append({"work_item_id": step_id, "model": selected.id,
                            "cost_tier": selected.cost_tier,
                            "evaluation_ref": selected.evaluation_ref})
        upgrade = {
            "proposal_only": True,
            "action": "user_selects_conversation_model",
            "current_conversation_model": policy.parent_model_id,
            "current_cost_tier": policy.parent_cost_tier,
            "required_minimum_tier": required_tier,
            "affected_work_items": sorted(upgrade_options),
            "workers_callable_after_upgrade": workers,
            "reason": "evaluated workers satisfy pending work requirements but exceed the current conversation cost tier",
            "resume": {"request_id": assessment.request_id,
                       "revision": assessment.revision,
                       "tool": "route_instruction_work_items",
                       "rule": "refresh source snapshots and policy, then rerun the same pending workflow state"},
        }

    next_state = state.model_copy(deep=True)
    dispatches: list[WorkItemDispatchPlan] = []
    if issues or model_without_route:
        status = "needs_assessment"
    elif upgrade is not None:
        status = "conversation_upgrade_required"
    else:
        for original, assignment, _step, _candidate in proposals:
            target = next(item for item in next_state.items if item.step_id == original.step_id)
            target.status = "in_progress"
            target.assignment = assignment
        for original, assignment, step, candidate in dispatch_proposals:
            role = ("implementation_subagent" if assignment.execution_kind == "implementation"
                    else "operational_subagent")
            dispatches.append(WorkItemDispatchPlan(
                work_item_id=original.step_id,
                node_id=original.node_id,
                route_id=assignment.route_id,
                route_revision=assignment.route_revision,
                parent_model=policy.parent_model_id,
                selected_model=candidate.id,
                selected_cost_tier=candidate.cost_tier,
                agent_role=role,
                task=assignment.task,
                scope=assignment.scope,
                rationale=(
                    f"The pending {assignment.execution_kind} work item independently selected "
                    f"{candidate.id} using {policy.selection_strategy}; the parent remains the gateway/coordinator."
                ),
                parent_execution="prohibited",
                dispatch_owner="client_host",
                authorization=step.authorization,
                dispatch_ready=True,
            ))
        if proposals:
            status = "ready"
        elif authorization_blocked:
            status = "authorization_required"
        elif all(item.status == "done" for item in state.items):
            status = "workflow_complete"
        elif any(item.status in {"blocked", "escalated"} for item in state.items):
            status = "workflow_blocked"
        elif active_assignment_exists:
            status = "waiting_active_result"
        else:
            status = "waiting_dependencies"
    return {
        "schema_version": 1,
        "status": status,
        "request_id": assessment.request_id,
        "revision": assessment.revision,
        "environment": assessment.environment,
        "policy_version": policy.version,
        "selection_strategy": policy.selection_strategy,
        "issues": issues,
        "decisions": decisions,
        "workflow_state": next_state.model_dump(),
        "dispatch_status": ("subagent_dispatch_required" if dispatches
                            else ("authorization_required" if authorization_blocked
                                  else "not_dispatched")),
        "subagent_dispatches": [dispatch.model_dump() for dispatch in dispatches],
        "conversation_upgrade": upgrade,
        "source_verification": ("client_reported_snapshot" if current_sources is not None
                                else "local_files"),
        "workflow_rule": (
            "Persist the returned workflow_state for re-entry. Only pending nodes route; completed "
            "nodes require a newer evidenced scope revision to reopen."
        ),
    }


def record_work_item_result(
    assessment: Assessment,
    state: WorkflowState,
    result: WorkItemResult,
) -> dict:
    """Record observed execution and return the next generic routing state."""
    _validate_workflow_state(assessment, state)
    if result.request_id != assessment.request_id or result.assessment_revision != assessment.revision:
        raise ValueError("work item result belongs to a different request or assessment revision")
    matches = [item for item in state.items if item.step_id == result.step_id]
    if len(matches) != 1 or matches[0].node_id != result.node_id:
        raise ValueError("work item result references an unknown step or node")
    item = matches[0]
    if item.status == "done":
        raise ValueError(
            "completed work item cannot be redispatched or reopened without a newer assessment "
            "revision and explicit scope_change evidence"
        )
    if item.status != "in_progress" or item.assignment is None:
        raise ValueError("work item result requires an active in-progress assignment")
    assignment = item.assignment
    if result.route_id != assignment.route_id or result.route_revision != assignment.route_revision:
        raise ValueError("work item result route identity is stale")
    if assignment.kind == "model" and result.observed_model is None:
        raise ValueError("model work item results require observed_model")
    if assignment.kind == "deterministic" and result.observed_model is not None:
        raise ValueError("deterministic tool results must not record an observed model")
    if item.reroute_requirement is not None:
        if result.outcome == "succeeded" and (
            result.resolves_failure_id != item.reroute_requirement.id
            or not result.resolution_evidence
        ):
            raise ValueError("recovery success must identify and evidence the active failure resolution")
    elif result.resolves_failure_id is not None:
        raise ValueError("result cannot resolve a failure that is not active")

    next_state = state.model_copy(deep=True)
    target = next(candidate for candidate in next_state.items if candidate.step_id == item.step_id)
    target.observations.append(RouteObservation(
        route_id=result.route_id,
        route_revision=result.route_revision,
        selected_model=assignment.selected_model,
        observed_model=result.observed_model,
        selected_cost_tier=assignment.selected_cost_tier,
        evaluation_ref=assignment.evaluation_ref,
        route_evidence=result.route_evidence,
        outcome=result.outcome,
        evidence=result.evidence,
    ))
    target.assignment = None
    mismatch = assignment.kind == "model" and result.observed_model != assignment.selected_model
    if result.outcome == "failed":
        failure = result.failure
        step = next(step for step in assessment.steps if step.id == item.step_id)
        if failure.disposition == "model_reroute":
            current_capabilities = (
                set(item.reroute_requirement.required_capabilities)
                if item.reroute_requirement is not None
                and item.reroute_requirement.disposition == "model_reroute"
                else set(step.capabilities)
            )
            if not set(failure.required_capabilities) - current_capabilities:
                raise ValueError("model reroute requires at least one additional evidenced capability")
            current_tier = assignment.selected_cost_tier or 0
            if failure.minimum_cost_tier <= current_tier:
                raise ValueError("model reroute minimum_cost_tier must exceed the failed assignment tier")
            next_status = "reroute_required"
        else:
            next_status = "deterministic_retry_required"
        target.status = "pending"
        target.route_revision += 1
        target.reroute_requirement = failure
        target.failure_history.append(failure)
        return {
            "schema_version": 1,
            "status": next_status,
            "request_id": assessment.request_id,
            "revision": assessment.revision,
            "work_item_id": target.step_id,
            "node_id": target.node_id,
            "reroute_requirement": failure.model_dump(),
            "observed_model_mismatch": mismatch,
            "workflow_state": next_state.model_dump(),
            "next_tool": "route_instruction_work_items",
        }
    target.status = {"succeeded": "done", "blocked": "blocked",
                     "escalated": "escalated"}[result.outcome]
    target.completion_evidence.extend(result.evidence)
    if result.resolution_evidence:
        target.resolution_evidence.extend(result.resolution_evidence)
    target.reroute_requirement = None
    terminal_status = "recorded" if not mismatch else "recorded_with_model_mismatch"
    return {
        "schema_version": 1,
        "status": terminal_status,
        "request_id": assessment.request_id,
        "revision": assessment.revision,
        "work_item_id": target.step_id,
        "node_id": target.node_id,
        "work_item_status": target.status,
        "observed_model_mismatch": mismatch,
        "workflow_state": next_state.model_dump(),
        "next_tool": "route_instruction_work_items",
    }


class Attempt(Record):
    id: Text
    goal_id: Text
    scope_revision: Count
    model: Text
    route_ref: Text
    retry_of: Text | None = None
    reason: Literal["initial", "instruction_miss", "scope_error", "dissatisfaction",
                    "requirement_change", "unknown"]
    reason_evidence: Text | None = None
    accepted: bool | None = None
    acceptance_evidence: Text | None = None
    cost: Amount | None = None
    elapsed_seconds: Amount | None = None
    user_revision_seconds: Amount | None = None

    @model_validator(mode="after")
    def explicit_feedback(self):
        if (self.retry_of is None) != (self.reason == "initial"):
            raise ValueError("non-initial attempts must link retry_of")
        if self.reason not in {"initial", "unknown"} and not self.reason_evidence:
            raise ValueError("classified feedback requires reason_evidence")
        if self.accepted is not None and not self.acceptance_evidence:
            raise ValueError("acceptance/rejection requires explicit evidence")
        return self


class Feedback(Record):
    version: Literal[1]
    cost_unit: Text
    attempts: list[Attempt] = Field(min_length=1)


def evaluate(feedback: Feedback) -> dict:
    seen = {}
    for attempt in feedback.attempts:
        if attempt.id in seen:
            raise ValueError("duplicate attempt ID")
        if attempt.retry_of:
            parent = seen.get(attempt.retry_of)
            if parent is None or parent.goal_id != attempt.goal_id:
                raise ValueError("retry must refer to an earlier attempt for the same goal")
            changed = parent.scope_revision != attempt.scope_revision
            if attempt.reason == "requirement_change" and not changed:
                raise ValueError("requirement changes require a new scope_revision")
            if changed and attempt.reason not in {"requirement_change", "unknown"}:
                raise ValueError("quality retries must retain the evaluated scope revision")
        seen[attempt.id] = attempt
    initial = [a for a in feedback.attempts if a.reason in {"initial", "requirement_change"}]
    judged = [a for a in initial if a.accepted is not None]
    sums = {}
    for field in ("cost", "elapsed_seconds", "user_revision_seconds"):
        values = [getattr(a, field) for a in feedback.attempts]
        sums[field] = {"total": sum(values) if all(v is not None for v in values) else None,
                       "known_subtotal": sum(v for v in values if v is not None),
                       "missing_count": sum(v is None for v in values)}
    groups = {}
    for attempt in feedback.attempts:
        key = (attempt.goal_id, attempt.scope_revision)
        groups.setdefault(key, []).append(attempt)
    acceptance = []
    for (goal, revision), attempts in groups.items():
        accepted_index = next((i for i, a in enumerate(attempts) if a.accepted is True), None)
        prefix = attempts if accepted_index is None else attempts[:accepted_index + 1]
        totals = {}
        for field in ("cost", "elapsed_seconds", "user_revision_seconds"):
            values = [getattr(a, field) for a in prefix]
            totals[field] = sum(values) if all(v is not None for v in values) else None
        acceptance.append({"goal_id": goal, "scope_revision": revision,
                           "accepted": accepted_index is not None,
                           "attempts_observed": len(prefix),
                           "attempts_to_acceptance": len(prefix) if accepted_index is not None else None,
                           "usage_observed": totals})
    return {"cost_unit": feedback.cost_unit, "attempts": len(seen),
            "quality_retries": sum(a.reason in {"instruction_miss", "scope_error", "dissatisfaction"}
                                   for a in feedback.attempts),
            "requirement_changes": sum(a.reason == "requirement_change" for a in feedback.attempts),
            "unknown_retries": sum(a.reason == "unknown" for a in feedback.attempts),
            "first_acceptance_rate": sum(a.accepted is True for a in judged) / len(judged) if judged else None,
            "first_acceptance_denominator": len(judged),
            "unjudged_initial_attempts": len(initial) - len(judged), "usage": sums,
            "acceptance_by_scope": acceptance, "feedback": feedback.model_dump()}


def _load_workflow_state(path: Path) -> WorkflowState:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict) and "workflow_state" in value:
        value = value["workflow_state"]
    return WorkflowState.model_validate(value)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit gateway")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="Snapshot existing files for gateway assessment")
    prepare.add_argument("--request-id", required=True)
    prepare.add_argument("--environment", required=True,
                         help="Host/profile identity, e.g. vscode:work or codex:personal")
    prepare.add_argument("--profile-root", type=Path,
                         help="Existing profile directory supplied by the active host")
    prepare.add_argument("--instruction-file", type=Path, required=True)
    prepare.add_argument("--skill-file", type=Path, required=True)
    prepare.add_argument("--profile-file", type=Path, action="append", default=[])
    prepare.add_argument("--input-file", type=Path, action="append", default=[])
    prepare.add_argument("--revision", type=int, default=0)
    routing = sub.add_parser("route")
    routing.add_argument("--assessment", type=Path, required=True)
    routing.add_argument("--policy", type=Path, required=True)
    workflow_init = sub.add_parser("workflow-init")
    workflow_init.add_argument("--assessment", type=Path, required=True)
    workflow_init.add_argument("--previous-state", type=Path)
    workflow_route = sub.add_parser("workflow-route")
    workflow_route.add_argument("--assessment", type=Path, required=True)
    workflow_route.add_argument("--policy", type=Path, required=True)
    workflow_route.add_argument("--state", type=Path, required=True)
    workflow_result = sub.add_parser("workflow-result")
    workflow_result.add_argument("--assessment", type=Path, required=True)
    workflow_result.add_argument("--state", type=Path, required=True)
    workflow_result.add_argument("--result", type=Path, required=True)
    feedback = sub.add_parser("evaluate")
    feedback.add_argument("--feedback", type=Path, required=True)
    schema = sub.add_parser("schema", help="Print the strict JSON schema for gateway records")
    schema.add_argument("kind", choices=[
        "assessment", "policy", "feedback", "dispatch_plan", "authorization",
        "workflow_state", "work_item_result", "work_item_dispatch",
    ])
    for command in (prepare, routing, workflow_init, workflow_route, workflow_result, feedback):
        command.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            print(json.dumps({"assessment": Assessment, "policy": Policy,
                              "feedback": Feedback,
                              "dispatch_plan": DispatchPlan,
                              "authorization": AuthorizationRecord,
                              "workflow_state": WorkflowState,
                              "work_item_result": WorkItemResult,
                              "work_item_dispatch": WorkItemDispatchPlan,
                              }[args.kind].model_json_schema(), indent=2))
            return 0
        if args.command == "prepare":
            if args.revision < 0:
                raise ValueError("revision must be nonnegative")
            sources = [snapshot(args.instruction_file, "instruction", "instruction"),
                       snapshot(args.skill_file, "skill", "skill")]
            for kind, paths in (("profile", args.profile_file), ("data", args.input_file)):
                for i, path in enumerate(paths):
                    if kind == "profile" and args.profile_root is not None:
                        root = args.profile_root.resolve(strict=True)
                        if not root.is_dir():
                            raise ValueError("profile-root must be an existing directory")
                        path = (root / path).resolve(strict=True)
                        if not path.is_relative_to(root):
                            raise ValueError("profile file is outside the selected environment profile root")
                    sources.append(snapshot(path, kind, f"{kind}-{i}"))
            result = {"version": 1, "request_id": args.request_id, "revision": args.revision,
                      "environment": args.environment,
                      "instruction": args.instruction_file.read_text(encoding="utf-8-sig"),
                      "sources": sources, "unresolved": None, "steps": []}
        elif args.command == "route":
            result = route(Assessment.model_validate_json(args.assessment.read_bytes()),
                           Policy.model_validate_json(args.policy.read_bytes()))
        elif args.command == "workflow-init":
            previous = (_load_workflow_state(args.previous_state)
                        if args.previous_state else None)
            result = initialize_workflow(
                Assessment.model_validate_json(args.assessment.read_bytes()),
                previous_state=previous,
            )
        elif args.command == "workflow-route":
            result = route_work_items(
                Assessment.model_validate_json(args.assessment.read_bytes()),
                Policy.model_validate_json(args.policy.read_bytes()),
                _load_workflow_state(args.state),
            )
        elif args.command == "workflow-result":
            result = record_work_item_result(
                Assessment.model_validate_json(args.assessment.read_bytes()),
                _load_workflow_state(args.state),
                WorkItemResult.model_validate_json(args.result.read_bytes()),
            )
        else:
            result = evaluate(Feedback.model_validate_json(args.feedback.read_bytes()))
        payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.out:
            with args.out.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
        else:
            print(payload, end="")
        return 1 if result.get("status") in {
            "needs_assessment", "conversation_upgrade_required", "authorization_required",
            "workflow_blocked",
        } else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
