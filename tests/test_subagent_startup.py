import contextlib
import hashlib
import io
import json
from pathlib import Path

import pytest

from xrefkit.__main__ import main
from xrefkit.subagent_startup import STARTUP_SOURCES, PROTOCOL_SOURCES, read_subagent_startup


def command(*args):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = main(list(args))
    return code, output.getvalue()


@pytest.fixture
def startup(tmp_path):
    for path, xid in (*STARTUP_SOURCES, *PROTOCOL_SOURCES.values()):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"<!-- xid: {xid} -->\n# Contract\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("Use startup contract", encoding="utf-8")
    catalog = tmp_path / "knowledge/index.md"
    catalog.parent.mkdir()
    catalog.write_text("DO NOT AUTOLOAD KNOWLEDGE", encoding="utf-8")
    log = tmp_path / "work/run.md"
    code, result = command("workflow", "run", "--root", str(tmp_path), "--task", "bounded work",
                           "--out", str(log), "--completion-condition", "checked output", "--json")
    assert code == 0, result
    run_id = json.loads(result)["run_id"]
    assert command("skill", "workitem", "--log", str(log), "--item", "WI-1", "--text", "bounded work",
                   "--completion-criterion", "checked output", "--status", "pending", "--role", "instruction:executor")[0] == 0
    reference = tmp_path / "input.md"
    reference.write_text("Task input", encoding="utf-8")
    binding = {"schema_version": 1, "source_mode": "filesystem", "run_id": run_id, "work_item_id": "WI-1",
               "purpose": "bounded work", "capability": "analysis", "tuning": "local", "responsibility": "read only",
               "scope_in": ["input.md"], "scope_out": ["publication"], "stop_conditions": ["missing evidence"],
               "protocols": ["workflow"], "knowledge_access": {"mode": "on_demand", "catalog": "knowledge/index.md"},
               "references": [{"path": "input.md", "sha256": hashlib.sha256(reference.read_bytes()).hexdigest()}]}
    file = tmp_path / "binding.json"
    file.write_text(json.dumps(binding), encoding="utf-8")
    return tmp_path, log, file, binding


def test_materializes_only_selected_sources_and_audits(startup):
    root, log, file, _ = startup
    result = read_subagent_startup(root, log, file)
    assert result["state"] == "materialized"
    assert result["work_item"]["criterion"] == "checked output"
    paths = [d["path"] for d in result["documents"]]
    assert "input.md" in paths
    assert PROTOCOL_SOURCES["reporting"][0] not in paths
    assert "knowledge/index.md" not in paths
    assert "DO NOT AUTOLOAD" not in json.dumps(result)
    assert 'subagent.startup.read' in log.read_text()
    assert result["roles"]["checker"] == "instruction:checker"


@pytest.mark.parametrize("field,value", [
    ("run_id", "different"), ("work_item_id", "missing"), ("source_mode", "mcp"),
    ("protocols", ["reporting"]), ("protocols", ["workflow", "invalid"]),
    ("scope_in", "not a list"), ("responsibility", ""), ("schema_version", True),
    ("references", [{"path": "input.md"}]),
])
def test_invalid_binding_does_not_acknowledge_reads(startup, field, value):
    root, log, file, binding = startup
    before = log.read_bytes()
    binding[field] = value
    file.write_text(json.dumps(binding), encoding="utf-8")
    with pytest.raises(ValueError):
        read_subagent_startup(root, log, file)
    assert log.read_bytes() == before


def test_stale_reference_blocks(startup):
    root, log, file, _ = startup
    (root / "input.md").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="revision mismatch"):
        read_subagent_startup(root, log, file)
    assert 'subagent.startup.read' not in log.read_text()


def test_external_path_blocks(startup):
    root, log, file, binding = startup
    binding["references"][0]["path"] = "../outside.md"
    file.write_text(json.dumps(binding), encoding="utf-8")
    with pytest.raises(ValueError, match="within --root"):
        read_subagent_startup(root, log, file)


def test_missing_startup_and_wrong_xid_block(startup):
    root, log, file, _ = startup
    source = root / STARTUP_SOURCES[0][0]
    source.write_text("wrong document", encoding="utf-8")
    with pytest.raises(ValueError, match="XID mismatch"):
        read_subagent_startup(root, log, file)
    source.unlink()
    with pytest.raises(ValueError, match="not found"):
        read_subagent_startup(root, log, file)


def test_mcp_bound_run_cannot_use_local_fallback(startup):
    root, log, file, _ = startup
    log.write_text(log.read_text().replace('- mcp_session_id: `-`', '- mcp_session_id: `session-1`'), encoding="utf-8")
    with pytest.raises(ValueError, match="MCP-bound"):
        read_subagent_startup(root, log, file)


def test_unopened_log_cannot_load_skill(startup):
    root, log, file, _ = startup
    log.write_text(log.read_text().replace('opened_by_xrefkit_workflow_run', 'not_opened'), encoding="utf-8")
    with pytest.raises(ValueError, match="Load Gate"):
        read_subagent_startup(root, log, file)


def test_reporting_is_explicit_and_cli_emits_blocked_json(startup):
    root, log, file, binding = startup
    binding["protocols"].append("reporting")
    file.write_text(json.dumps(binding), encoding="utf-8")
    code, output = command("workflow", "subagent-read", "--root", str(root), "--log", str(log), "--binding", str(file), "--json")
    assert code == 0
    assert PROTOCOL_SOURCES["reporting"][0] in [d["path"] for d in json.loads(output)["documents"]]
    file.write_text("{broken", encoding="utf-8")
    code, output = command("workflow", "subagent-read", "--root", str(root), "--log", str(log), "--binding", str(file))
    assert code == 1
    result = json.loads(output)
    assert result["state"] == "blocked"
    assert "documents" not in result
