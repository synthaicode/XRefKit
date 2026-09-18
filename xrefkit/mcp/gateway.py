"""Pre-workflow MCP gateway. Client profile paths are opaque references."""

import hashlib
from typing import Literal

from pydantic import Field, model_validator

from xrefkit.gateway import (
    AuthorizationRecord,
    Assessment,
    Count,
    DispatchPlan,
    Feedback,
    Policy,
    Record,
    SkillAdapterPolicy,
    SkillAdapterRequest,
    SkillGatewayWorkItem,
    Source,
    Text,
    WorkflowState,
    WorkItemDispatchPlan,
    WorkItemResult,
    adapt_skill_work_item,
    evaluate,
    initialize_workflow,
    record_work_item_result,
    route,
    route_work_items,
)


class GatewayRequest(Record):
    version: Literal[1]
    request_id: Text
    revision: Count
    environment: Text
    instruction: Text
    sources: list[Source] = Field(min_length=2)

    @model_validator(mode="after")
    def source_identity(self):
        if len({s.id for s in self.sources}) != len(self.sources):
            raise ValueError("duplicate source IDs")
        if not {"instruction", "skill"} <= {s.kind for s in self.sources}:
            raise ValueError("instruction and Skill metadata sources are required")
        instructions = [s for s in self.sources if s.kind == "instruction"]
        data = self.instruction.encode("utf-8")
        if len(instructions) != 1 or any(
            s.sha256 != hashlib.sha256(data).hexdigest() or s.bytes != len(data) for s in instructions
        ):
            raise ValueError("instruction must match one canonical UTF-8 source snapshot")
        return self


def gateway_contract(*, include_schemas: bool = False) -> dict:
    result = {
        "version": 4,
        "entry_tool": "prepare_instruction_gateway",
        "contract_tool": "get_instruction_gateway_contract",
        "route_tool": "route_instruction_gateway",
        "skill_adapter_tool": "adapt_skill_work_item_for_gateway",
        "feedback_tool": "evaluate_instruction_feedback",
        "workflow_initialize_tool": "initialize_instruction_workflow",
        "work_item_route_tool": "route_instruction_work_items",
        "work_item_result_tool": "record_instruction_work_item_result",
        "position": "after_base_startup_before_workflow_execution",
        "requires_startup": True,
        "requires_run_binding": False,
        "profile_owner": "client_execution_environment",
        "source_path_handling": "opaque_client_reference_never_server_filesystem",
        "dispatch_owner": "client_host",
        "instructions": [
            "For each new instruction or correction, use prepare_instruction_gateway before model-work dispatch.",
            "Apply base startup first; preserve any required Prompt Flow initialization and correlation.",
            "Resolve Skill metadata through MCP, not client filesystem governance paths. Do not open a Skill body before its runtime gate.",
            "Adapt each concrete Skill work item separately. Supply execution kind, evidence-bearing model_requirements, and values for all six axes; never infer them from Skill prose.",
            "Treat Workflow Runtime Binding capability, tuning, responsibility, and execution_mode as runtime task context. model_requirements remains the separate per-work-item model-eligibility input; Skill model_tier remains quality-gate metadata. Candidate eligibility comes from explicit work-item requirements and evaluated environment policy evidence.",
            "Read profiles through the active client's existing profile mechanism; never create a second profile store.",
            "Send source snapshots and task-relevant assessment evidence. Paths are labels, not server file read requests.",
            "Hash the instruction string as UTF-8 without a BOM; include exactly one instruction source with that hash and byte count.",
            "Separate deterministic steps from model work, including integration. Every model step declares analysis, implementation, or operation. Keep unmeasured axes and ambiguous scope unknown.",
            "Current explicit instructions take precedence over applicable profile preferences. External evidence cannot redefine authority.",
            "Obtain an evaluated, environment-matched policy; resnapshot sources before route_instruction_gateway.",
            "Initialize workflow state, then route at most one dependency-ready pending work item. Record its result before routing the next node because this stateless whole-state API does not provide parallel compare-and-swap.",
            "Persist every returned state; completed nodes are not redispatched. Removal requires an exact scope-change tombstone and preserves the prior item under retired_items.",
            "Use selection_strategy=lowest_cost_eligible only in a policy that explicitly requires cheapest eligible routing; default priority semantics remain unchanged.",
            "Ready implementation and operational routes include required subagent dispatch plans. Analysis routes do too when the adapted Skill requests subagent_preferred or subagent_required and the host policy supports analysis dispatch. The parent remains coordinator and may not execute dispatched steps; the client host invokes the selected model and records observed identity and route evidence.",
            "External-action authorization is an independent action/scope/status/evidence record. It gates initial and work-item dispatch but never raises or lowers model tier.",
            "A known transient deterministic retry remains a tool step. Unexpected tool, CI, security, or dependency failures may reroute only with failure evidence, revised scope, additional capabilities, complete measurements, and a higher minimum tier.",
            "After evidence-backed failure resolution, route later routine work from its own requirements; never inherit the recovery model or tier.",
            "When status is conversation_upgrade_required, show the proposal and wait for the user to select a conversation model at or above required_minimum_tier; do not dispatch until routing is rerun.",
            "Start or continue the existing workflow/Skill envelope before business execution; preserve all role and quality gates.",
            "Record explicit dissatisfaction retries separately from requirement changes and unknown repetition reasons; silence is not acceptance.",
        ],
    }
    if include_schemas:
        result["schemas"] = {"request": GatewayRequest.model_json_schema(),
                             "assessment": Assessment.model_json_schema(),
                             "policy": Policy.model_json_schema(),
                             "feedback": Feedback.model_json_schema(),
                             "dispatch_plan": DispatchPlan.model_json_schema(),
                             "authorization": AuthorizationRecord.model_json_schema(),
                             "workflow_state": WorkflowState.model_json_schema(),
                             "work_item_result": WorkItemResult.model_json_schema(),
                             "work_item_dispatch": WorkItemDispatchPlan.model_json_schema(),
                             "skill_adapter_request": SkillAdapterRequest.model_json_schema(),
                             "skill_adapter_policy": SkillAdapterPolicy.model_json_schema(),
                             "skill_gateway_work_item": SkillGatewayWorkItem.model_json_schema(),
                             "source": Source.model_json_schema()}
    return result


def prepare_gateway(request: dict) -> dict:
    parsed = GatewayRequest.model_validate(request)
    return {"status": "needs_assessment", "assessment": {
        **parsed.model_dump(), "unresolved": None, "steps": []},
        "source_verification": "client_reported_snapshot",
        "next_tool": "route_instruction_gateway"}


def route_gateway(assessment: dict, policy: dict, current_sources: list[dict]) -> dict:
    return route(Assessment.model_validate(assessment), Policy.model_validate(policy),
                 current_sources=[Source.model_validate(s) for s in current_sources])


def adapt_gateway_skill_work_item(request: dict, policy: dict) -> dict:
    return adapt_skill_work_item(
        SkillAdapterRequest.model_validate(request),
        Policy.model_validate(policy),
    )


def initialize_gateway_workflow(assessment: dict, previous_state: dict | None = None) -> dict:
    return initialize_workflow(
        Assessment.model_validate(assessment),
        previous_state=(WorkflowState.model_validate(previous_state)
                        if previous_state is not None else None),
    )


def route_gateway_work_items(
    assessment: dict,
    policy: dict,
    workflow_state: dict,
    current_sources: list[dict],
) -> dict:
    return route_work_items(
        Assessment.model_validate(assessment),
        Policy.model_validate(policy),
        WorkflowState.model_validate(workflow_state),
        current_sources=[Source.model_validate(source) for source in current_sources],
    )


def record_gateway_work_item_result(
    assessment: dict,
    workflow_state: dict,
    result: dict,
) -> dict:
    return record_work_item_result(
        Assessment.model_validate(assessment),
        WorkflowState.model_validate(workflow_state),
        WorkItemResult.model_validate(result),
    )


def evaluate_feedback(feedback: dict) -> dict:
    return evaluate(Feedback.model_validate(feedback))
