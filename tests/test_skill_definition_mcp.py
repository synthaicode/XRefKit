import asyncio
import contextlib
import hashlib
import io
import json

import pytest

from test_mcp_subagent_startup import _context
from xrefkit.__main__ import main
from xrefkit.execution_binding import build_execution_binding
from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.mcp.subagent_startup import McpSubagentStartupError, read_mcp_subagent_startup


def _definition(skill_id="sample_skill", xid="ABCDEF123456") -> str:
    metadata = {
        "schema_version": 1,
        "skill_id": skill_id,
        "xid": xid,
        "summary": "Inspect a bounded target",
        "applies_when": ["inspection requested"],
        "exclusions": ["unbounded implementation"],
        "inputs": ["target"],
        "outputs": ["report"],
        "criteria": [{
            "id": "coverage", "statement": "Target is covered",
            "verification": "Compare report and target",
        }],
        "knowledge_needs": [{
            "id": "rules", "query": "applicable rules", "required_when": "always",
            "seed_xids": ["123456ABCDEF"],
        }],
        "control_refs": ["B7A2C94F0E61"],
    }
    return (
        "---\r\n" + json.dumps(metadata) + "\r\n---\r\n"
        f"<!-- xid: {xid} -->\r\n<a id=\"xid-{xid}\"></a>\r\n"
        "# Definition method\r\nSECRET_METHOD_SENTINEL\r\n"
    )


def _write_definition(root, *, skill_id="sample_skill", xid="ABCDEF123456"):
    path = root / "definitions" / skill_id / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"\xef\xbb\xbf" + _definition(skill_id, xid).encode("utf-8")
    path.write_bytes(raw)
    return path, raw


def _legacy(root):
    path = root / "skills" / "sample_skill"
    path.mkdir(parents=True)
    (path / "meta.md").write_text(
        "<!-- xid: 111111111111 -->\n# Meta\n- skill_id: `sample_skill`\n"
        "- summary: legacy\n- skill_doc: `./SKILL.md`\n",
        encoding="utf-8",
    )
    (path / "SKILL.md").write_text(
        "<!-- xid: 222222222222 -->\n# Legacy method\n", encoding="utf-8",
    )


def _command(*args):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = main(list(args))
    return code, output.getvalue()


def test_opt_in_definition_replaces_legacy_and_transfers_one_exact_document(tmp_path):
    _legacy(tmp_path)
    definition, raw = _write_definition(tmp_path)
    legacy = XRefCatalog.build(tmp_path)
    assert legacy.get_skill("sample_skill", {})["definition_format"] == "legacy_split_v1"
    assert len(legacy.get_skill("sample_skill", {})["documents"]) == 2

    catalog = XRefCatalog.build(tmp_path, skill_definition_paths=[definition])
    entries = [entry for entry in catalog.skills if entry.skill_id == "sample_skill"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry.definition_format == "skill_definition_v1"
    assert entry.definition_content_hash == hashlib.sha256(raw).hexdigest()
    listed = catalog.list_skills(include_content=True)[0]
    assert listed["meta_content"] == listed["skill_content"] == ""
    assert "SECRET_METHOD_SENTINEL" not in json.dumps(listed)

    selected = catalog.get_skill("sample_skill", {})
    assert selected["path"] == "definitions/sample_skill/SKILL.md"
    assert len(selected["documents"]) == 1
    document = selected["documents"][0]
    assert document["xid"] == "ABCDEF123456"
    assert document["content"].encode("utf-8") == raw
    assert document["content_hash"] == hashlib.sha256(raw).hexdigest()
    cached = catalog.get_skill("sample_skill", {document["xid"]: document["content_hash"]})
    assert cached["documents"][0]["content_omitted"] is True


def test_definition_configuration_is_bounded_and_collision_checked(tmp_path):
    one, _ = _write_definition(tmp_path, skill_id="one", xid="ABCDEF123456")
    two, _ = _write_definition(tmp_path, skill_id="two", xid="ABCDEF123456")
    with pytest.raises(ValueError):
        XRefCatalog.build(tmp_path, skill_definition_paths=[one, two]).skills
    with pytest.raises(ValueError, match="within the repository"):
        XRefCatalog.build(tmp_path, skill_definition_paths=[tmp_path.parent / "outside.md"])


def test_mcp_startup_materializes_exact_definition_document(tmp_path):
    definition, _ = _write_definition(tmp_path)
    log = tmp_path / "work" / "run.md"
    code, output = _command(
        "skill", "run", "--root", str(tmp_path),
        "--definition", "definitions/sample_skill/SKILL.md",
        "--task", "Inspect", "--out", str(log),
        "--capability", "inspection", "--tuning", "bounded",
        "--responsibility", "report", "--execution-mode", "subagent_required", "--json",
    )
    assert code == 0, output
    run_id = json.loads(output)["run_id"]
    assert _command(
        "skill", "workitem", "--log", str(log), "--item", "WI-1",
        "--text", "Inspect", "--completion-criterion", "report checked",
        "--status", "pending", "--role", "sample_skill:executor",
    )[0] == 0
    catalog = XRefCatalog.build(tmp_path, skill_definition_paths=[definition])
    request = {
        "work_item_id": "WI-1", "source_mode": "mcp", "purpose": "Inspect",
        "capability": "inspection", "tuning": "bounded", "responsibility": "report",
        "instruction_basis": "explicit task", "scope_in": ["target"], "scope_out": [],
        "stop_conditions": ["missing evidence"], "protocols": ["workflow"],
        "knowledge_access": {"mode": "on_demand", "catalog_tool": "search_knowledge_catalog",
                             "resolve_tool": "get_document_by_xid"},
        "repository_fingerprint": catalog.repository_fingerprint,
    }
    binding = build_execution_binding(log, request)
    calls = []

    async def call(name, args):
        calls.append(name)
        if name == "get_startup_context":
            return _context(binding)
        if name == "bind_skill_run":
            return {**args, "repository_fingerprint": catalog.repository_fingerprint,
                    "mcp_session_id": "session", "audit_enabled": True}
        if name == "get_skill":
            return catalog.get_skill(args["skill_id"], args["known_document_versions"])
        raise AssertionError(name)

    result = asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert result["state"] == "materialized"
    assert calls == ["get_startup_context", "bind_skill_run", "get_skill"]
    assert [item["kind"] for item in result["documents"]].count("skill_definition") == 1
    assert result["documents"][-1]["content_hash"] == binding["definition_identity"]["sha256"]
    assert "subagent.startup.read" in log.read_text(encoding="utf-8")


def test_mcp_startup_rejects_definition_identity_mismatch(tmp_path):
    definition, raw = _write_definition(tmp_path)
    log = tmp_path / "work" / "run.md"
    code, output = _command(
        "skill", "run", "--root", str(tmp_path), "--definition", "definitions/sample_skill/SKILL.md",
        "--task", "Inspect", "--out", str(log), "--capability", "inspection",
        "--tuning", "bounded", "--responsibility", "report", "--execution-mode", "subagent_required", "--json",
    )
    assert code == 0, output
    run_id = json.loads(output)["run_id"]
    assert _command("skill", "workitem", "--log", str(log), "--item", "WI-1", "--text", "Inspect",
                    "--completion-criterion", "checked", "--status", "pending",
                    "--role", "sample_skill:executor")[0] == 0
    catalog = XRefCatalog.build(tmp_path, skill_definition_paths=[definition])
    request = {
        "work_item_id": "WI-1", "source_mode": "mcp", "purpose": "Inspect",
        "capability": "inspection", "tuning": "bounded", "responsibility": "report",
        "instruction_basis": "explicit", "scope_in": ["target"], "scope_out": [],
        "stop_conditions": ["missing"], "protocols": ["workflow"],
        "knowledge_access": {"mode": "on_demand", "catalog_tool": "search_knowledge_catalog",
                             "resolve_tool": "get_document_by_xid"},
        "repository_fingerprint": catalog.repository_fingerprint,
    }
    binding = build_execution_binding(log, request)

    async def call(name, args):
        if name == "get_startup_context": return _context(binding)
        if name == "bind_skill_run":
            return {**args, "repository_fingerprint": catalog.repository_fingerprint,
                    "mcp_session_id": "session", "audit_enabled": True}
        if name == "get_skill":
            result = catalog.get_skill("sample_skill", {})
            result["definition_content_hash"] = "0" * 64
            return result
        raise AssertionError(name)

    with pytest.raises(McpSubagentStartupError, match="identity"):
        asyncio.run(read_mcp_subagent_startup(log, binding, call))
    assert hashlib.sha256(raw).hexdigest() == binding["definition_identity"]["sha256"]
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")
