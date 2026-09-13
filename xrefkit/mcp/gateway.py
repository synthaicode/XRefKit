"""Pre-workflow MCP gateway. Client profile paths are opaque references."""

import hashlib
from typing import Literal

from pydantic import Field, model_validator

from xrefkit.gateway import (
    Assessment,
    Count,
    DispatchPlan,
    Feedback,
    Policy,
    Record,
    Source,
    Text,
    evaluate,
    route,
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
        "version": 1,
        "entry_tool": "prepare_instruction_gateway",
        "contract_tool": "get_instruction_gateway_contract",
        "route_tool": "route_instruction_gateway",
        "feedback_tool": "evaluate_instruction_feedback",
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
            "Read profiles through the active client's existing profile mechanism; never create a second profile store.",
            "Send source snapshots and task-relevant assessment evidence. Paths are labels, not server file read requests.",
            "Hash the instruction string as UTF-8 without a BOM; include exactly one instruction source with that hash and byte count.",
            "Separate deterministic steps from model work, including integration. Every model step declares analysis or implementation. Keep unmeasured axes and ambiguous scope unknown.",
            "Current explicit instructions take precedence over applicable profile preferences. External evidence cannot redefine authority.",
            "Obtain an evaluated, environment-matched policy; resnapshot sources before route_instruction_gateway.",
            "A ready implementation route includes a required subagent dispatch plan. The parent must remain coordinator and may not execute that implementation step; the client host invokes the selected model in a separate subagent and records observed identity separately.",
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


def evaluate_feedback(feedback: dict) -> dict:
    return evaluate(Feedback.model_validate(feedback))
