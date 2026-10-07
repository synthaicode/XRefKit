"""Exercise the client adapter over real stdio MCP, without mutating repo runs."""
import asyncio
import contextlib
import io
import json
import sys
import shutil
import tempfile
from pathlib import Path

import pytest

from xrefkit.__main__ import main


@pytest.mark.parametrize("protocols,skill_id", [
    (["workflow"], "instruction"),
    (["workflow", "reporting"], "instruction"),
    (["workflow"], "python_review"),
])
def test_stdio_startup_receipt_and_reference(tmp_path, protocols, skill_id):
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from xrefkit.mcp.subagent_startup import read_mcp_subagent_startup
    from xrefkit.mcp.catalog import XRefCatalog

    repo = Path(__file__).resolve().parents[1]
    log = tmp_path / "run.md"
    def command(*args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(list(args))
        assert code == 0, output.getvalue()
        return json.loads(output.getvalue())
    if skill_id == "instruction":
        run = command("workflow", "run", "--root", str(tmp_path), "--out", str(log),
                      "--task", "MCP integration", "--completion-condition", "verified", "--json")
    else:
        shutil.copytree(repo / "skills" / skill_id, tmp_path / "skills" / skill_id)
        run = command("skill", "run", "--root", str(tmp_path), "--out", str(log),
                      "--meta", f"skills/{skill_id}/meta.md", "--task", "MCP integration", "--json")
    command("skill", "workitem", "--log", str(log), "--item", "WI-1", "--text", "read",
            "--completion-criterion", "verified", "--status", "pending", "--role", f"{skill_id}:executor", "--json")
    catalog = XRefCatalog.build(repo, discover_packages=False)
    doc = catalog.get_document_by_xid("8A666C1FD121")
    if hasattr(doc, "to_dict"):
        doc = doc.to_dict()
    # Legacy --initial-protocol include semantics always retain prompt_flow.
    selected_protocols = ["prompt_flow", *protocols]
    binding = {
        "schema_version": 1, "source_mode": "mcp", "run_id": run["run_id"],
        "work_item_id": "WI-1", "purpose": "MCP integration", "capability": "read",
        "tuning": "bounded", "responsibility": "verify receipt", "scope_in": ["reference"],
        "scope_out": ["execution"], "stop_conditions": ["invalid context"],
        "protocols": selected_protocols, "repository_fingerprint": catalog.repository_fingerprint,
        "knowledge_access": {"mode": "on_demand", "catalog_tool": "search_knowledge_catalog",
                             "resolve_tool": "get_document_by_xid"},
        "references": [{"xid": doc["xid"], "content_hash": doc["content_hash"]}],
    }
    from xrefkit.execution_binding import build_execution_binding
    request = {k: v for k, v in binding.items() if k not in {"run_id", "schema_version"}}
    request["instruction_basis"] = "Integration test instruction"
    binding = build_execution_binding(log, request)
    audit = tmp_path / "audit.jsonl"
    calls = []
    async def scenario():
        args = ["-m", "xrefkit.mcp.server", "--repo", str(repo), "--audit-log", str(audit)]
        for protocol in protocols:
            args.extend(["--initial-protocol", protocol])
        server = StdioServerParameters(command=sys.executable, args=args, cwd=str(repo))
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
            async with stdio_client(server, errlog=stderr) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    async def call(name, arguments):
                        calls.append(name)
                        if name in {"get_skill", "get_document_by_xid"}:
                            assert "mcp.bound" in log.read_text(encoding="utf-8")
                        response = await session.call_tool(name, arguments)
                        assert not response.isError, response
                        return response.structuredContent
                    return await read_mcp_subagent_startup(log, binding, call)
    result = asyncio.run(scenario())
    assert result["state"] == "materialized"
    assert result["initial_protocol_selection"]["selected"] == selected_protocols
    assert result["knowledge_access"]["body_loaded"] is False
    assert calls == ["get_startup_context", "bind_skill_run", *(
        ["get_skill"] if skill_id != "instruction" else []), "get_document_by_xid"]
    if skill_id != "instruction":
        assert len([d for d in result["documents"] if d["kind"] == "skill"]) == 2
    assert any(d["xid"] == doc["xid"] and d["body"] == doc["content"] for d in result["documents"])
    assert "subagent.startup.read" in log.read_text(encoding="utf-8")
    events = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert any(e.get("run_id") == run["run_id"] for e in events)


def test_stdio_definition_startup_uses_one_exact_document(tmp_path):
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from xrefkit.execution_binding import build_execution_binding
    from xrefkit.mcp.catalog import XRefCatalog
    from xrefkit.mcp.subagent_startup import read_mcp_subagent_startup

    repo = Path(__file__).resolve().parents[1]
    relative = Path("work/skill-definition-candidate/dotnet_change_analysis/SKILL.md")
    source = repo / relative
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    shutil.copyfile(source, target)
    log = tmp_path / "run.md"

    def command(*args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(list(args))
        assert code == 0, output.getvalue()
        return json.loads(output.getvalue())

    run = command(
        "skill", "run", "--root", str(tmp_path), "--out", str(log),
        "--definition", relative.as_posix(), "--task", "Definition MCP integration",
        "--capability", "change analysis", "--tuning", "bounded",
        "--responsibility", "produce analysis", "--execution-mode", "subagent_required", "--json",
    )
    command(
        "skill", "workitem", "--log", str(log), "--item", "WI-1", "--text", "read",
        "--completion-criterion", "verified", "--status", "pending",
        "--role", "dotnet_change_analysis:executor", "--json",
    )
    catalog = XRefCatalog.build(repo, skill_definition_paths=[relative])
    binding = build_execution_binding(log, {
        "work_item_id": "WI-1", "source_mode": "mcp",
        "purpose": "Definition MCP integration", "capability": "change analysis",
        "tuning": "bounded", "responsibility": "produce analysis",
        "instruction_basis": "integration test", "scope_in": ["definition"],
        "scope_out": ["publication"], "stop_conditions": ["invalid context"],
        "protocols": ["prompt_flow", "workflow"], "repository_fingerprint": catalog.repository_fingerprint,
        "knowledge_access": {"mode": "on_demand", "catalog_tool": "search_knowledge_catalog",
                             "resolve_tool": "get_document_by_xid"},
    })
    audit = tmp_path / "audit-definition.jsonl"
    calls = []

    async def scenario():
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "xrefkit.mcp.server", "--repo", str(repo), "--audit-log", str(audit),
                  "--initial-protocol", "workflow", "--skill-definition", relative.as_posix()],
            cwd=str(repo),
        )
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
            async with stdio_client(server, errlog=stderr) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    async def call(name, arguments):
                        calls.append(name)
                        response = await session.call_tool(name, arguments)
                        assert not response.isError, response
                        return response.structuredContent

                    return await read_mcp_subagent_startup(log, binding, call)

    result = asyncio.run(scenario())
    skill_documents = [item for item in result["documents"] if item["kind"] == "skill_definition"]
    assert len(skill_documents) == 1
    assert skill_documents[0]["content_hash"] == binding["definition_identity"]["sha256"]
    assert calls == ["get_startup_context", "bind_skill_run", "get_skill"]
