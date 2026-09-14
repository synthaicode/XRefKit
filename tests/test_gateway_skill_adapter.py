import copy
import hashlib
import json

import pytest

from test_gateway import request_and_policy
from xrefkit.cli import main
from xrefkit.gateway import (
    AXES,
    Assessment,
    Policy,
    SkillAdapterRequest,
    WorkflowState,
    adapt_skill_work_item,
    initialize_workflow,
    route,
    route_work_items,
)


def _adapter_request(assessment: dict) -> dict:
    refs = [{"source_id": "skill", "locator": "meta"}]
    return {
        "version": 1,
        "environment": assessment["environment"],
        "skill": {
            "source_id": "skill",
            "skill_id": "python_review",
            "maturity": "trial",
            "capability": "software_development",
            "execution_mode": "subagent_preferred",
            "model_tier": "standard",
        },
        "work_item": {
            "id": "review-one-module",
            "kind": "model",
            "execution_kind": "analysis",
            "task": "Review one Python module",
            "scope": "module.py",
            "evidence": refs,
            "metrics": {
                axis: {"value": 1, "basis": "measured", "evidence": refs}
                for axis in AXES
            },
        },
    }


def _adapter_policy(policy: dict) -> dict:
    configured = copy.deepcopy(policy)
    configured["subagent_execution_kinds"] = ["analysis", "implementation", "operation"]
    configured["skill_adapter"] = {
        "version": 1,
        "capability_map": {
            "software_development": {
                "required_capabilities": ["software_review"],
                "evaluation_ref": "host-eval/capability/software-review",
            }
        },
        "model_tier_map": {
            "standard": {
                "minimum_cost_tier": 2,
                "required_capabilities": ["standard_quality"],
                "evaluation_ref": "host-eval/tier/standard",
            }
        },
    }
    configured["candidates"][0]["capabilities"].extend(
        ["software_review", "standard_quality"]
    )
    configured["candidates"][1]["capabilities"].extend(
        ["software_review", "standard_quality"]
    )
    return configured


def test_adapter_maps_one_concrete_work_item_and_analysis_dispatches(request_and_policy):
    assessment, raw_policy = request_and_policy
    request = _adapter_request(assessment)
    policy = Policy.model_validate(_adapter_policy(raw_policy))

    adapted = adapt_skill_work_item(SkillAdapterRequest.model_validate(request), policy)

    assert adapted["status"] == "ready"
    assert adapted["adapter_version"] == 1
    assert adapted["step"]["capabilities"] == ["software_review", "standard_quality"]
    assert adapted["step"]["minimum_cost_tier"] == 2
    assert adapted["step"]["execution_mode"] == "subagent_preferred"
    assessment["steps"] = [adapted["step"]]
    routed = route(Assessment.model_validate(assessment), policy)
    assert routed["status"] == "ready"
    assert routed["decisions"][0]["model"] == "capable"
    assert routed["subagent_dispatches"][0]["agent_role"] == "analysis_subagent"

    parsed = Assessment.model_validate(assessment)
    state = WorkflowState.model_validate(initialize_workflow(parsed)["workflow_state"])
    work_route = route_work_items(parsed, policy, state)
    assert work_route["subagent_dispatches"][0]["work_item_id"] == "review-one-module"
    assert work_route["subagent_dispatches"][0]["agent_role"] == "analysis_subagent"


def test_adapter_keeps_unknown_measurement_and_missing_mapping_nonready(request_and_policy):
    assessment, raw_policy = request_and_policy
    request = _adapter_request(assessment)
    request["work_item"]["metrics"]["constraints"].update(value=None, basis="unknown")
    policy_data = _adapter_policy(raw_policy)
    del policy_data["skill_adapter"]["capability_map"]["software_development"]

    result = adapt_skill_work_item(
        SkillAdapterRequest.model_validate(request), Policy.model_validate(policy_data)
    )

    assert result["status"] == "needs_assessment"
    assert "unknown complexity: constraints" in result["issues"]
    assert any("no capability mapping" in issue for issue in result["issues"])
    assert result["step"] is None


@pytest.mark.parametrize(
    "cause",
    [
        "environment_mismatch",
        "missing_adapter",
        "missing_capability_mapping",
        "missing_tier_mapping",
        "unknown_tier_minimum",
        "unknown_measurement",
        "required_analysis_unsupported",
    ],
)
def test_nonready_model_adapter_result_never_exposes_a_step(request_and_policy, cause):
    assessment, raw_policy = request_and_policy
    request = _adapter_request(assessment)
    policy_data = _adapter_policy(raw_policy)

    if cause == "environment_mismatch":
        request["environment"] = "vscode:other"
    elif cause == "missing_adapter":
        policy_data["skill_adapter"] = None
    elif cause == "missing_capability_mapping":
        del policy_data["skill_adapter"]["capability_map"]["software_development"]
    elif cause == "missing_tier_mapping":
        del policy_data["skill_adapter"]["model_tier_map"]["standard"]
    elif cause == "unknown_tier_minimum":
        policy_data["skill_adapter"]["model_tier_map"]["standard"]["minimum_cost_tier"] = None
    elif cause == "unknown_measurement":
        request["work_item"]["metrics"]["constraints"].update(value=None, basis="unknown")
    elif cause == "required_analysis_unsupported":
        request["skill"]["execution_mode"] = "subagent_required"
        policy_data["subagent_execution_kinds"] = ["implementation", "operation"]

    result = adapt_skill_work_item(
        SkillAdapterRequest.model_validate(request), Policy.model_validate(policy_data)
    )

    assert result["status"] == "needs_assessment"
    assert result["step"] is None


def test_environment_mismatched_deterministic_adapter_result_never_exposes_a_step(request_and_policy):
    assessment, raw_policy = request_and_policy
    request = _adapter_request(assessment)
    request["environment"] = "vscode:other"
    request["work_item"] = {
        "id": "run-check",
        "kind": "deterministic",
        "task": "Run deterministic check",
        "scope": "one run log",
        "evidence": [{"source_id": "skill", "locator": "meta"}],
        "tool_ref": "python -m xrefkit skill verify --log run.md",
    }

    result = adapt_skill_work_item(
        SkillAdapterRequest.model_validate(request), Policy.model_validate(_adapter_policy(raw_policy))
    )

    assert result["status"] == "needs_assessment"
    assert result["step"] is None


def test_required_analysis_stops_when_host_policy_cannot_dispatch(request_and_policy):
    assessment, raw_policy = request_and_policy
    request = _adapter_request(assessment)
    request["skill"]["execution_mode"] = "subagent_required"
    policy_data = _adapter_policy(raw_policy)
    policy_data["subagent_execution_kinds"] = ["implementation", "operation"]

    result = adapt_skill_work_item(
        SkillAdapterRequest.model_validate(request), Policy.model_validate(policy_data)
    )

    assert result["status"] == "needs_assessment"
    assert result["issues"] == [
        "host policy does not support required analysis subagent dispatch"
    ]


def test_deterministic_skill_work_item_needs_no_model_mapping(request_and_policy):
    assessment, raw_policy = request_and_policy
    request = _adapter_request(assessment)
    request["work_item"] = {
        "id": "run-check",
        "kind": "deterministic",
        "task": "Run deterministic check",
        "scope": "one run log",
        "evidence": [{"source_id": "skill", "locator": "meta"}],
        "tool_ref": "python -m xrefkit skill verify --log run.md",
    }

    result = adapt_skill_work_item(
        SkillAdapterRequest.model_validate(request), Policy.model_validate(raw_policy)
    )

    assert result["status"] == "ready"
    assert result["step"]["kind"] == "deterministic"
    assert result["mapping_evidence"] == []


def test_default_adapter_fields_accept_pre_adapter_workflow_hashes(request_and_policy):
    raw_assessment, raw_policy = request_and_policy
    assessment = Assessment.model_validate(raw_assessment)
    assessment_payload = assessment.model_dump()
    for step in assessment_payload["steps"]:
        step.pop("execution_mode")
        step.pop("minimum_cost_tier")
    assessment_hash = hashlib.sha256(json.dumps(
        assessment_payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()
    items = []
    for step in assessment.steps:
        definition = step.model_dump(exclude={"authorization"})
        definition.pop("execution_mode")
        definition.pop("minimum_cost_tier")
        definition_hash = hashlib.sha256(json.dumps(
            definition, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
        items.append({
            "step_id": step.id,
            "node_id": step.node_id or step.id,
            "definition_sha256": definition_hash,
            "status": "pending",
            "authorization": step.authorization.model_dump() if step.authorization else None,
        })
    legacy_state = WorkflowState.model_validate({
        "version": 1,
        "request_id": assessment.request_id,
        "assessment_revision": assessment.revision,
        "assessment_sha256": assessment_hash,
        "environment": assessment.environment,
        "items": items,
    })

    routed = route_work_items(assessment, Policy.model_validate(raw_policy), legacy_state)

    assert routed["status"] == "ready"


def test_local_default_analysis_preserves_existing_parent_execution(request_and_policy):
    assessment, raw_policy = request_and_policy
    request = _adapter_request(assessment)
    request["skill"]["execution_mode"] = "local_default"
    policy = Policy.model_validate(_adapter_policy(raw_policy))
    adapted = adapt_skill_work_item(SkillAdapterRequest.model_validate(request), policy)
    assessment["steps"] = [adapted["step"]]

    routed = route(Assessment.model_validate(assessment), policy)

    assert routed["status"] == "ready"
    assert routed["subagent_dispatches"] == []


def test_skill_adapter_cli_and_schema(request_and_policy, tmp_path, capsys):
    assessment, raw_policy = request_and_policy
    request_path = tmp_path / "adapter-request.json"
    policy_path = tmp_path / "policy.json"
    request_path.write_text(json.dumps(_adapter_request(assessment)), encoding="utf-8")
    policy_path.write_text(json.dumps(_adapter_policy(raw_policy)), encoding="utf-8")

    assert main(["gateway", "schema", "skill_adapter_request"]) == 0
    assert json.loads(capsys.readouterr().out)["additionalProperties"] is False
    assert main([
        "gateway", "skill-adapt", "--request", str(request_path),
        "--policy", str(policy_path),
    ]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "ready"
    assert result["step"]["id"] == "review-one-module"
