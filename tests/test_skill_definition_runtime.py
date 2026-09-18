import hashlib
import json

import pytest

from test_subagent_startup import command
from xrefkit.execution_binding import build_execution_binding


def _definition() -> str:
    metadata = {
        "schema_version": 1,
        "skill_id": "definition_sample",
        "xid": "ABCDEF123456",
        "summary": "Inspect one bounded target",
        "applies_when": ["inspection is requested"],
        "exclusions": [],
        "inputs": ["target"],
        "outputs": ["report"],
        "criteria": [{
            "id": "coverage",
            "statement": "The target is covered",
            "verification": "Compare the report with the target",
        }],
        "knowledge_needs": [],
        "control_refs": ["B7A2C94F0E61"],
    }
    method = (
        "<!-- xid: ABCDEF123456 -->\n"
        '<a id="xid-ABCDEF123456"></a>\n\n'
        "# Method\n\nInspect the selected target.\n"
    )
    return "---\n" + json.dumps(metadata) + "\n---\n" + method


def _request(source_mode="filesystem"):
    request = {
        "work_item_id": "WI-1",
        "source_mode": source_mode,
        "purpose": "inspect a bounded target",
        "capability": "repository inspection",
        "tuning": "preserve unknowns",
        "responsibility": "produce the bounded report",
        "instruction_basis": "explicit user instruction",
        "scope_in": ["selected target"],
        "scope_out": [],
        "stop_conditions": ["required evidence is missing"],
        "protocols": ["workflow"],
        "knowledge_access": {"mode": "on_demand", "catalog": "knowledge/index.md"},
    }
    if source_mode == "mcp":
        request["repository_fingerprint"] = "repository-fingerprint"
        request["knowledge_access"] = {
            "mode": "on_demand",
            "catalog_tool": "search_knowledge_catalog",
            "resolve_tool": "get_document_by_xid",
        }
    return request


def _open_run(tmp_path):
    definition = tmp_path / "skills" / "definition_sample" / "SKILL.md"
    definition.parent.mkdir(parents=True)
    definition.write_text(_definition(), encoding="utf-8")
    log = tmp_path / "work" / "run.md"
    code, output = command(
        "skill", "run", "--root", str(tmp_path),
        "--definition", "skills/definition_sample/SKILL.md",
        "--task", "Inspect the target", "--out", str(log),
        "--capability", "repository inspection",
        "--tuning", "preserve unknowns",
        "--responsibility", "produce the bounded report",
        "--execution-mode", "subagent_required", "--json",
    )
    assert code == 0, output
    assert command(
        "skill", "workitem", "--log", str(log), "--item", "WI-1",
        "--text", "Inspect target", "--completion-criterion", "report covers target",
        "--status", "pending", "--role", "definition_sample:executor",
    )[0] == 0
    return definition, log


def test_definition_run_records_dynamic_routing_and_exact_revision(tmp_path):
    definition, log = _open_run(tmp_path)
    text = log.read_text(encoding="utf-8")
    digest = hashlib.sha256(definition.read_bytes()).hexdigest()
    assert "- maturity: `definition_v1`" in text
    assert "- meta: `-`" in text
    assert "- skill_doc: `skills/definition_sample/SKILL.md`" in text
    assert "- definition_xid: `ABCDEF123456`" in text
    assert "- definition_path: `skills/definition_sample/SKILL.md`" in text
    assert f"- definition_sha256: `{digest}`" in text
    assert "- capability: `repository inspection`" in text
    assert "- tuning: `preserve unknowns`" in text
    assert "- responsibility: `produce the bounded report`" in text
    assert "- execution_mode: `subagent_required`" in text

    binding = build_execution_binding(log, _request())
    assert binding["definition_identity"] == {
        "xid": "ABCDEF123456",
        "path": "skills/definition_sample/SKILL.md",
        "sha256": digest,
    }
    assert binding["run_snapshot"]["fields"]["definition_sha256"] == digest


def test_definition_binding_rejects_runtime_drift_and_unavailable_mcp(tmp_path):
    _, log = _open_run(tmp_path)
    request = _request()
    request["tuning"] = "different tuning"
    with pytest.raises(ValueError, match="tuning does not match"):
        build_execution_binding(log, request)
    with pytest.raises(ValueError, match="definition-backed MCP startup is not available"):
        build_execution_binding(log, _request("mcp"))


def test_definition_run_requires_complete_runtime_routing(tmp_path):
    definition = tmp_path / "SKILL.md"
    definition.write_text(_definition(), encoding="utf-8")
    code, output = command(
        "skill", "run", "--root", str(tmp_path), "--definition", "SKILL.md",
        "--task", "Inspect", "--capability", "analysis", "--tuning", "bounded",
        "--responsibility", "report", "--json",
    )
    assert code == 1
    assert "--execution-mode" in output

