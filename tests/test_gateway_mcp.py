import copy
import sys
import tempfile
from pathlib import Path

import pytest

from test_gateway import request_and_policy
from xrefkit.mcp.gateway import (
    gateway_contract,
    initialize_gateway_workflow,
    prepare_gateway,
    route_gateway,
    route_gateway_work_items,
)


def remote_pair(pair):
    assessment, policy = copy.deepcopy(pair)
    for source in assessment["sources"]:
        source["path"] = "client-only://active-profile/" + source["id"]
    return assessment, policy


def test_remote_paths_are_never_opened(request_and_policy):
    assessment, policy = remote_pair(request_and_policy)
    result = route_gateway(assessment, policy, assessment["sources"])
    assert result["status"] == "ready"
    assert result["source_verification"] == "client_reported_snapshot"
    assert result["dispatch_status"] == "subagent_dispatch_required"
    assert result["subagent_dispatches"][0]["parent_execution"] == "prohibited"
    assert route_gateway(assessment, policy, [])["status"] == "needs_assessment"
    changed = copy.deepcopy(assessment["sources"])
    changed[-1]["sha256"] = "0" * 64
    assert route_gateway(assessment, policy, changed)["status"] == "needs_assessment"
    assessment["instruction"] = "A new scope without refreshed evidence"
    assert route_gateway(assessment, policy, assessment["sources"])["status"] == "needs_assessment"


def test_contract_and_prepare_preserve_unassessed_state(request_and_policy):
    assessment, _ = remote_pair(request_and_policy)
    request = {k: v for k, v in assessment.items() if k not in {"unresolved", "steps"}}
    result = prepare_gateway(request)
    assert result["assessment"]["unresolved"] is None
    assert result["assessment"]["steps"] == []
    assert gateway_contract()["requires_run_binding"] is False
    assert "schemas" not in gateway_contract()
    assert set(gateway_contract(include_schemas=True)["schemas"]) == {
        "request", "assessment", "policy", "feedback", "source", "dispatch_plan",
        "authorization", "workflow_state", "work_item_result", "work_item_dispatch",
        "skill_adapter_request", "skill_adapter_policy", "skill_gateway_work_item"}


def test_work_item_state_routes_only_pending_nodes_over_wrapper(request_and_policy):
    assessment, policy = remote_pair(request_and_policy)
    state = initialize_gateway_workflow(assessment)["workflow_state"]
    routed = route_gateway_work_items(assessment, policy, state, assessment["sources"])
    assert routed["status"] == "ready"
    assert routed["workflow_state"]["items"][0]["status"] == "in_progress"
    assert routed["workflow_state"]["items"][1]["status"] == "pending"


def test_upgrade_proposal_is_returned_over_mcp_boundary(request_and_policy):
    assessment, policy = remote_pair(request_and_policy)
    policy["parent_cost_tier"] = 1
    result = route_gateway(assessment, policy, assessment["sources"])
    assert result["status"] == "conversation_upgrade_required"
    assert result["conversation_upgrade"]["required_minimum_tier"] == 3
    assert result["conversation_upgrade"]["proposal_only"] is True


def test_gateway_over_real_mcp_stdio_before_run_binding(request_and_policy, tmp_path):
    anyio = pytest.importorskip("anyio")
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    root = Path(__file__).resolve().parents[1]
    assessment, policy = remote_pair(request_and_policy)
    request = {k: v for k, v in assessment.items() if k not in {"unresolved", "steps"}}

    async def scenario(errlog):
        parameters = StdioServerParameters(command=sys.executable, cwd=str(root), args=[
            "-m", "xrefkit.mcp.server", "--repo", str(root),
            "--audit-log", str(tmp_path / "audit.jsonl")])
        async with stdio_client(parameters, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                names = {tool.name for tool in (await session.list_tools()).tools}
                assert {"prepare_instruction_gateway", "route_instruction_gateway",
                        "adapt_skill_work_item_for_gateway",
                        "get_instruction_gateway_contract", "evaluate_instruction_feedback",
                        "initialize_instruction_workflow", "route_instruction_work_items",
                        "record_instruction_work_item_result"} <= names
                rejected = await session.call_tool("get_instruction_gateway_contract", {})
                assert rejected.isError
                assert "XREFKIT_STARTUP_REQUIRED" in rejected.content[0].text
                startup = await session.call_tool("get_startup_context", {})
                assert not startup.isError
                assert startup.structuredContent["instruction_gateway"]["entry_tool"] == "prepare_instruction_gateway"
                assert "gateway.route_incoming_instruction" in {
                    obligation["id"] for obligation in startup.structuredContent["client_obligations"]}
                contracts = await session.call_tool("list_tool_contracts", {})
                assert not contracts.isError
                assert "xref.route_instruction_gateway" in {
                    item["tool_id"] for item in contracts.structuredContent["result"]}
                assert "xref.route_instruction_work_items" in {
                    item["tool_id"] for item in contracts.structuredContent["result"]}
                assert "xref.adapt_skill_work_item_for_gateway" in {
                    item["tool_id"] for item in contracts.structuredContent["result"]}
                contract = await session.call_tool("get_instruction_gateway_contract", {})
                assert not contract.isError
                assert "schemas" in contract.structuredContent
                adapter_policy = copy.deepcopy(policy)
                adapter_policy["subagent_execution_kinds"] = [
                    "analysis", "implementation", "operation"
                ]
                adapter_policy["skill_adapter"] = {
                    "version": 1,
                    "capability_map": {
                        "software_development": {
                            "required_capabilities": ["incremental_scope"],
                            "evaluation_ref": "fixture-skill-capability",
                        }
                    },
                    "model_tier_map": {
                        "standard": {
                            "minimum_cost_tier": 1,
                            "required_capabilities": [],
                            "evaluation_ref": "fixture-skill-tier",
                        }
                    },
                }
                refs = [{"source_id": "skill", "locator": "meta"}]
                adapted = await session.call_tool("adapt_skill_work_item_for_gateway", {
                    "request": {
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
                            "id": "review",
                            "kind": "model",
                            "execution_kind": "analysis",
                            "task": "Review source",
                            "scope": "fixture",
                            "evidence": refs,
                            "metrics": {
                                axis: {"value": 1, "basis": "measured", "evidence": refs}
                                for axis in ("constraints", "branch_depth", "dependency_depth",
                                             "cross_source_links", "scope_changes", "integration_links")
                            },
                        },
                    },
                    "policy": adapter_policy,
                })
                assert not adapted.isError
                assert adapted.structuredContent["status"] == "ready"
                assert adapted.structuredContent["step"]["execution_mode"] == "subagent_preferred"
                prepared = await session.call_tool("prepare_instruction_gateway", {"request": request})
                assert not prepared.isError
                assert prepared.structuredContent["status"] == "needs_assessment"
                routed = await session.call_tool("route_instruction_gateway", {
                    "assessment": assessment, "policy": policy, "current_sources": assessment["sources"]})
                assert not routed.isError
                assert routed.structuredContent["decisions"][1]["model"] == "capable"
                assert routed.structuredContent["subagent_dispatches"][0]["selected_model"] == "capable"
                assert routed.structuredContent["subagent_dispatches"][0]["parent_execution"] == "prohibited"
                assert routed.structuredContent["source_verification"] == "client_reported_snapshot"
                initialized = await session.call_tool("initialize_instruction_workflow", {
                    "assessment": assessment})
                assert not initialized.isError
                item_route = await session.call_tool("route_instruction_work_items", {
                    "assessment": assessment,
                    "policy": policy,
                    "workflow_state": initialized.structuredContent["workflow_state"],
                    "current_sources": assessment["sources"],
                })
                assert not item_route.isError
                assert item_route.structuredContent["workflow_state"]["items"][0]["status"] == "in_progress"
                count_item = item_route.structuredContent["workflow_state"]["items"][0]
                recorded = await session.call_tool("record_instruction_work_item_result", {
                    "assessment": assessment,
                    "workflow_state": item_route.structuredContent["workflow_state"],
                    "result": {
                        "version": 1,
                        "request_id": assessment["request_id"],
                        "assessment_revision": assessment["revision"],
                        "step_id": count_item["step_id"],
                        "node_id": count_item["node_id"],
                        "route_id": count_item["assignment"]["route_id"],
                        "route_revision": count_item["assignment"]["route_revision"],
                        "outcome": "succeeded",
                        "route_evidence": "tool/count-1",
                        "evidence": [{"ref": "tool/count-1", "summary": "count completed"}],
                    },
                })
                assert not recorded.isError
                next_route = await session.call_tool("route_instruction_work_items", {
                    "assessment": assessment,
                    "policy": policy,
                    "workflow_state": recorded.structuredContent["workflow_state"],
                    "current_sources": assessment["sources"],
                })
                assert not next_route.isError
                assert next_route.structuredContent["subagent_dispatches"][0]["selected_model"] == "capable"
                upgrade_policy = copy.deepcopy(policy)
                upgrade_policy["parent_cost_tier"] = 1
                upgrade = await session.call_tool("route_instruction_gateway", {
                    "assessment": assessment, "policy": upgrade_policy,
                    "current_sources": assessment["sources"]})
                assert not upgrade.isError
                assert upgrade.structuredContent["status"] == "conversation_upgrade_required"
                assert upgrade.structuredContent["conversation_upgrade"]["required_minimum_tier"] == 3
                feedback = await session.call_tool("evaluate_instruction_feedback", {"feedback": {
                    "version": 1, "cost_unit": "USD", "attempts": [{
                        "id": "a", "goal_id": "g", "scope_revision": 0, "model": "capable",
                        "route_ref": "route-1", "reason": "initial"}]}})
                assert not feedback.isError
                assert feedback.structuredContent["first_acceptance_rate"] is None

    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
        anyio.run(scenario, errlog)
