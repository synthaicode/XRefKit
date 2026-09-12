import copy
import sys
import tempfile
from pathlib import Path

import pytest

from test_gateway import request_and_policy
from xrefkit.mcp.gateway import gateway_contract, prepare_gateway, route_gateway


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
    assert result["dispatch_status"] == "not_dispatched"
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
        "request", "assessment", "policy", "feedback", "source"}


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
                        "get_instruction_gateway_contract", "evaluate_instruction_feedback"} <= names
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
                contract = await session.call_tool("get_instruction_gateway_contract", {})
                assert not contract.isError
                assert "schemas" in contract.structuredContent
                prepared = await session.call_tool("prepare_instruction_gateway", {"request": request})
                assert not prepared.isError
                assert prepared.structuredContent["status"] == "needs_assessment"
                routed = await session.call_tool("route_instruction_gateway", {
                    "assessment": assessment, "policy": policy, "current_sources": assessment["sources"]})
                assert not routed.isError
                assert routed.structuredContent["decisions"][1]["model"] == "capable"
                assert routed.structuredContent["source_verification"] == "client_reported_snapshot"
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
