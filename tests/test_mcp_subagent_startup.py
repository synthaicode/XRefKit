import asyncio
import hashlib
import json
import contextlib
import io
from pathlib import Path

import pytest

from xrefkit.mcp.subagent_startup import McpSubagentStartupError, read_mcp_subagent_startup
from xrefkit.__main__ import main


def _run_log(tmp_path):
    log = tmp_path / "run.md"
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        assert main(["workflow", "run", "--root", str(tmp_path), "--task", "adapter test", "--out", str(log), "--completion-condition", "checked", "--json"]) == 0
    run_id = json.loads(output.getvalue())["run_id"]
    with contextlib.redirect_stdout(io.StringIO()):
        assert main(["skill", "workitem", "--log", str(log), "--item", "WI-1", "--text", "adapter test", "--completion-criterion", "checked", "--status", "pending", "--role", "instruction:executor"]) == 0
    return log, run_id


def _binding(run_id, *, protocols=None, refs=None, skill=False):
    return {
        "schema_version": 1, "source_mode": "mcp", "repository_fingerprint": "repo-fp",
        "run_id": run_id, "work_item_id": "WI-1", "purpose": "adapter test",
        "capability": "testing", "tuning": "bounded", "responsibility": "verify",
        "scope_in": ["tests/test_mcp_subagent_startup.py"], "scope_out": ["publication"],
        "stop_conditions": ["contract failure"], "protocols": ["workflow"] if protocols is None else protocols,
        "knowledge_access": {"mode": "on_demand", "catalog_tool": "search_knowledge_catalog",
                              "resolve_tool": "get_document_by_xid"},
        "references": refs or [],
    }


def _context(binding, *, stale=False):
    body = "startup body"
    pack = {"body": body, "pack_hash": hashlib.sha256(body.encode()).hexdigest(),
            "stale": stale, "stale_sources": [], "source_xids": ["ABCDEF123456"]}
    return {"repository_identity": {"repository_fingerprint": binding["repository_fingerprint"]},
            "access_policy": {"mode": "mcp_only"}, "missing": [],
            "initial_protocol_selection": {"selected": binding["protocols"], "source": "test"},
            "startup_contract_pack": pack, "load_order": ["ABCDEF123456"],
            "workflow_protocol": {"version": "1"} if "workflow" in binding["protocols"] else None,
            "prompt_flow_protocol": ({"version": "1", "reconciliation": {"default": "report_only"}}
                                     if "prompt_flow" in binding["protocols"] else None),
            "reporting_protocol": {"version": "1"} if "reporting" in binding["protocols"] else None}


def test_instruction_startup_calls_required_tools_in_order(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id)
    calls = []

    async def call(name, args):
        calls.append((name, args))
        if name == "get_startup_context": return _context(binding)
        if name == "bind_skill_run":
            return {**{k: args.get(k) for k in ("run_id", "skill_id", "flow_id", "root_run_id", "parent_run_id", "work_item_id", "node_id")},
                    "repository_fingerprint": "repo-fp", "mcp_session_id": "session-1", "audit_enabled": True}
        raise AssertionError(f"unexpected tool {name}")

    result = asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert result["ok"] is True
    assert [name for name, _ in calls] == ["get_startup_context", "bind_skill_run"]
    assert all("client_record_command" not in args for _, args in calls)


def test_invalid_hash_fails_before_receipt(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id)
    binding["references"] = [{"xid": "ABCDEF123456", "content_hash": "0" * 64}]
    calls = []

    async def call(name, args):
        calls.append(name)
        if name == "get_startup_context": return _context(binding)
        if name == "bind_skill_run":
            return {**{k: args.get(k) for k in ("run_id", "skill_id", "flow_id", "root_run_id")},
                    "repository_fingerprint": "repo-fp", "mcp_session_id": "s", "audit_enabled": True}
        if name == "get_document_by_xid":
            return {"xid": "ABCDEF123456", "content": "body", "content_hash": hashlib.sha256(b"body").hexdigest(),
                    "repository_fingerprint": "repo-fp"}
        raise AssertionError(name)

    with pytest.raises(McpSubagentStartupError):
        asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


def test_bind_requires_complete_non_null_correlation(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id)

    async def call(name, args):
        if name == "get_startup_context":
            return _context(binding)
        if name == "bind_skill_run":
            # A host must never receive a partial correlation.
            assert all(args.get(k) for k in ("run_id", "skill_id", "flow_id", "root_run_id", "work_item_id"))
            return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "s", "audit_enabled": True}
        raise AssertionError(name)

    with pytest.raises((AssertionError, McpSubagentStartupError)):
        asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


def test_stale_pack_and_unselected_reporting_payload_fail_without_receipt(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id)

    async def stale(name, args):
        if name == "get_startup_context":
            value = _context(binding); value["startup_contract_pack"]["stale"] = True; return value
        raise AssertionError(name)

    with pytest.raises(McpSubagentStartupError, match="stale"):
        asyncio.run(read_mcp_subagent_startup(log, binding, stale))
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


@pytest.mark.parametrize("mutator", [
    lambda r: r.pop("run_id"), lambda r: r.update(run_id=None),
    lambda r: r.update(repository_fingerprint="wrong"),
    lambda r: r.update(parent_run_id="unexpected"), lambda r: r.update(flow_id="wrong-flow"),
])
def test_bind_response_mismatch_is_fail_closed(tmp_path, mutator):
    log, run_id = _run_log(tmp_path); binding = _binding(run_id)

    async def call(name, args):
        if name == "get_startup_context": return _context(binding)
        if name == "bind_skill_run":
            response = {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "s", "audit_enabled": True}
            mutator(response); return response
        raise AssertionError(name)

    with pytest.raises(McpSubagentStartupError): asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


def test_binding_snapshot_prevents_reference_redirect(tmp_path):
    log, run_id = _run_log(tmp_path); binding = _binding(run_id)
    ref = {"xid": "ABCDEF123456", "content_hash": hashlib.sha256(b"body").hexdigest()}
    binding["references"] = [ref]
    original = dict(ref)

    async def call(name, args):
        if name == "get_startup_context":
            binding["references"][0]["xid"] = "123456ABCDEF"; return _context(binding)
        if name == "bind_skill_run": return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "s", "audit_enabled": True}
        if name == "get_document_by_xid":
            assert args["xid"] == original["xid"]
            return {"xid": original["xid"], "content": "body", "content_hash": original["content_hash"], "repository_fingerprint": "repo-fp"}
        raise AssertionError(name)

    result = asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert result["binding"]["references"] == [original]
    assert result["documents"][-1]["xid"] == original["xid"]


def test_log_mutation_during_reference_read_rejects(tmp_path):
    log, run_id = _run_log(tmp_path); binding = _binding(run_id)
    body = "body"; binding["references"] = [{"xid": "ABCDEF123456", "content_hash": hashlib.sha256(body.encode()).hexdigest()}]
    changed = False

    async def call(name, args):
        nonlocal changed
        if name == "get_startup_context": return _context(binding)
        if name == "bind_skill_run": return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "s", "audit_enabled": True}
        if name == "get_document_by_xid":
            log.write_text(log.read_text().replace("instruction:executor", "changed:executor"), encoding="utf-8"); changed = True
            return {"xid": args["xid"], "content": body, "content_hash": binding["references"][0]["content_hash"], "repository_fingerprint": "repo-fp"}
        raise AssertionError(name)

    with pytest.raises(McpSubagentStartupError): asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert changed and "subagent.startup.read" not in log.read_text(encoding="utf-8")


def test_oversized_remote_reference_rejects(tmp_path):
    log, run_id = _run_log(tmp_path); binding = _binding(run_id)
    body = "x" * 256001; binding["references"] = [{"xid": "ABCDEF123456", "content_hash": hashlib.sha256(body.encode()).hexdigest()}]

    async def call(name, args):
        if name == "get_startup_context": return _context(binding)
        if name == "bind_skill_run": return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "s", "audit_enabled": True}
        if name == "get_document_by_xid": return {"xid": args["xid"], "content": body, "content_hash": binding["references"][0]["content_hash"], "repository_fingerprint": "repo-fp"}
        raise AssertionError(name)

    with pytest.raises(McpSubagentStartupError): asyncio.run(read_mcp_subagent_startup(log, binding, call))


def test_mcp_bound_event_precedes_reference_fetch(tmp_path):
    log, run_id = _run_log(tmp_path); binding = _binding(run_id)
    body = "body"; binding["references"] = [{"xid": "ABCDEF123456", "content_hash": hashlib.sha256(body.encode()).hexdigest()}]

    async def call(name, args):
        if name == "get_startup_context": return _context(binding)
        if name == "bind_skill_run":
            assert "mcp.bound" not in log.read_text(encoding="utf-8")
            return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "s", "audit_enabled": True}
        if name == "get_document_by_xid":
            assert "mcp.bound" in log.read_text(encoding="utf-8")
            return {"xid": args["xid"], "content": body, "content_hash": binding["references"][0]["content_hash"], "repository_fingerprint": "repo-fp"}
        raise AssertionError(name)

    result = asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert result["ok"] is True


def test_general_skill_is_rejected_before_network(tmp_path):
    log, run_id = _run_log(tmp_path); binding = _binding(run_id)
    log.write_text(log.read_text().replace("skill_id: `instruction`", "skill_id: `general_skill`"), encoding="utf-8")
    seen = []

    async def call(name, args):
        seen.append(name); raise AssertionError("network must not be called")

    with pytest.raises(McpSubagentStartupError): asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert seen == [] and "subagent.startup.read" not in log.read_text(encoding="utf-8")

def test_unselected_reporting_payload_rejects_before_bind(tmp_path):
    log, run_id = _run_log(tmp_path); binding = _binding(run_id)
    seen = []
    async def call(name, args):
        seen.append(name)
        if name == "get_startup_context":
            value = _context(binding); value["reporting_protocol"] = {"version": "1"}; return value
        raise AssertionError(name)
    with pytest.raises(McpSubagentStartupError): asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert seen == ["get_startup_context"]
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


@pytest.mark.parametrize("mutator", [
    lambda b: b.update({"source_mode": "filesystem"}),
    lambda b: b.update({"protocols": ["workflow", "workflow"]}),
    lambda b: b.update({"knowledge_access": {"mode": "on_demand", "catalog_tool": "wrong", "resolve_tool": "get_document_by_xid"}}),
])
def test_binding_boundaries_are_fail_closed(tmp_path, mutator):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id)
    mutator(binding)
    seen = []

    async def call(name, args):
        seen.append(name)
        return _context(binding)

    with pytest.raises((McpSubagentStartupError, ValueError)):
        asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert seen == []


@pytest.mark.parametrize("name,value", [
    ("access_policy", None), ("load_order", [{}]),
    ("initial_protocol_selection", {"selected": ["workflow", {}]}),
    ("prompt_flow_protocol", {"version": "1", "reconciliation": None}),
    ("workflow_protocol", {"version": 1}), ("missing", ["required-source"]),
])
def test_malformed_startup_rejected_before_bind(tmp_path, name, value):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id)
    async def call(tool, args):
        assert tool == "get_startup_context"
        reply = _context(binding)
        reply[name] = value
        return reply
    with pytest.raises(McpSubagentStartupError):
        asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


def test_noncacheable_reference_hash_still_checked(tmp_path):
    log, run_id = _run_log(tmp_path)
    expected_hash = hashlib.sha256(b"expected").hexdigest()
    binding = _binding(run_id, refs=[{"xid": "ABCDEF123456", "content_hash": expected_hash}])
    calls = []
    async def call(name, args):
        calls.append(name)
        if name == "get_startup_context":
            return _context(binding)
        if name == "bind_skill_run":
            return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "session", "audit_enabled": True}
        return {"xid": args["xid"], "content": "tampered", "content_hash": expected_hash,
                "repository_fingerprint": "repo-fp", "cache_policy": {"cache_recommended": False}}
    with pytest.raises(McpSubagentStartupError, match="hash"):
        asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert calls[-1] == "get_document_by_xid"
    assert "mcp.bound" in log.read_text(encoding="utf-8")
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


def test_total_context_limit_stops_further_reads(tmp_path):
    log, run_id = _run_log(tmp_path)
    body = "x" * 250000
    digest = hashlib.sha256(body.encode()).hexdigest()
    refs = [{"xid": f"{i:012X}", "content_hash": digest} for i in range(1, 6)]
    binding = _binding(run_id, refs=refs)
    reads = []
    async def call(name, args):
        if name == "get_startup_context":
            return _context(binding)
        if name == "bind_skill_run":
            return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "session", "audit_enabled": True}
        reads.append(args["xid"])
        return {"xid": args["xid"], "content": body, "content_hash": digest, "repository_fingerprint": "repo-fp"}
    with pytest.raises(McpSubagentStartupError, match="byte limit"):
        asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert reads == [r["xid"] for r in refs[:4]]
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


@pytest.mark.parametrize("stage,field,new", [
    ("get_startup_context", "flow_id", "other-flow"),
    ("bind_skill_run", "skill_id", "other_skill"),
    ("get_document_by_xid", "mcp_session_id", "other-session"),
    ("get_document_by_xid", "closure", "done"),
])
def test_run_change_at_transport_boundary_rejects(tmp_path, stage, field, new):
    from xrefkit.skillrun import _replace_log_field
    log, run_id = _run_log(tmp_path)
    body = "reference"
    digest = hashlib.sha256(body.encode()).hexdigest()
    binding = _binding(run_id, refs=[{"xid": "ABCDEF123456", "content_hash": digest}])
    changed = []
    async def call(name, args):
        if name == stage:
            text = log.read_text(encoding="utf-8")
            if field == "closure":
                text = text.replace("## Closure Gate\n\n- status: `pending`", "## Closure Gate\n\n- status: `done`")
            else:
                text, _ = _replace_log_field(text, field, new)
            log.write_text(text, encoding="utf-8")
            changed.append(True)
        if name == "get_startup_context":
            return _context(binding)
        if name == "bind_skill_run":
            return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "session", "audit_enabled": True}
        return {"xid": args["xid"], "content": body, "content_hash": digest, "repository_fingerprint": "repo-fp"}
    with pytest.raises(McpSubagentStartupError):
        asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert changed
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


def test_optional_references_and_reordered_selection(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id, protocols=["workflow", "reporting"])
    binding.pop("references")
    async def call(name, args):
        if name == "get_startup_context":
            reply = _context(binding)
            reply["initial_protocol_selection"]["selected"] = ["reporting", "workflow"]
            return reply
        assert name == "bind_skill_run"
        return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "session", "audit_enabled": True,
                "client_record_command": "this is data, not an executable command"}
    result = asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert result["state"] == "materialized"
    assert result["initial_protocol_selection"]["selected"] == ["reporting", "workflow"]


def test_canonical_selection_accepts_all_three_and_preserves_receipt(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id, protocols=["prompt_flow", "workflow", "reporting"])

    async def call(name, args):
        if name == "get_startup_context":
            reply = _context(binding)
            reply["initial_protocol_selection"] = {
                "available": ["prompt_flow", "workflow", "reporting"],
                "selected": ["prompt_flow", "workflow", "reporting"],
                "excluded": [], "source": "initialize", "selection_mode": "exclude",
            }
            return reply
        assert name == "bind_skill_run"
        return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "session",
                "audit_enabled": True}

    result = asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert result["initial_protocol_selection"]["selection_mode"] == "exclude"
    assert result["receipt"]["selection"] == result["initial_protocol_selection"]


def test_excluded_prompt_flow_may_be_null(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id, protocols=["workflow", "reporting"])

    async def call(name, args):
        if name == "get_startup_context":
            reply = _context(binding)
            reply["initial_protocol_selection"] = {
                "available": ["prompt_flow", "workflow", "reporting"],
                "selected": ["workflow", "reporting"],
                "excluded": ["prompt_flow"], "source": "initialize", "selection_mode": "exclude",
            }
            return reply
        assert name == "bind_skill_run"
        return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "session",
                "audit_enabled": True}

    result = asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert result["documents"][-2]["kind"] == "workflow_protocol"
    assert result["initial_protocol_selection"]["excluded"] == ["prompt_flow"]


def test_all_protocols_excluded_allows_empty_selection(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id, protocols=[])

    async def call(name, args):
        if name == "get_startup_context":
            reply = _context(binding)
            reply["initial_protocol_selection"] = {
                "available": ["prompt_flow", "workflow", "reporting"],
                "selected": [], "excluded": ["prompt_flow", "workflow", "reporting"],
                "source": "initialize", "selection_mode": "exclude",
            }
            return reply
        assert name == "bind_skill_run"
        return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "session",
                "audit_enabled": True}

    result = asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert result["initial_protocol_selection"]["selected"] == []
    assert [doc["kind"] for doc in result["documents"]] == ["startup_contract_pack"]


def test_legacy_selection_receipt_keeps_prompt_flow(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = _binding(run_id, protocols=["prompt_flow", "workflow"])

    async def call(name, args):
        if name == "get_startup_context":
            reply = _context(binding)
            reply["initial_protocol_selection"] = {
                "available": ["prompt_flow", "workflow", "reporting"],
                "selected": ["prompt_flow", "workflow"],
                "excluded": ["reporting"], "source": "initialize",
                "selection_mode": "legacy_include",
            }
            return reply
        assert name == "bind_skill_run"
        return {**args, "repository_fingerprint": "repo-fp", "mcp_session_id": "session",
                "audit_enabled": True}

    result = asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert result["initial_protocol_selection"]["selected"] == ["prompt_flow", "workflow"]
    assert result["receipt"]["selection"]["selection_mode"] == "legacy_include"
