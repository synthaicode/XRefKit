import asyncio
import copy
import json

import pytest

from test_subagent_startup import startup, command
from test_mcp_subagent_startup import _run_log, _binding, _context
from xrefkit.execution_binding import build_execution_binding, validate_binding_context
from xrefkit.subagent_startup import read_subagent_startup
from xrefkit.mcp.subagent_startup import read_mcp_subagent_startup
from xrefkit.skillrun import _replace_log_field


def request_for(binding):
    request = {k: v for k, v in binding.items() if k not in {"schema_version", "run_id"}}
    request["instruction_basis"] = "User requested bounded analysis"
    return copy.deepcopy(request)


def test_build_local_and_read_without_inheriting_skill_triad(startup):
    root, log, file, manual = startup
    request = request_for(manual)
    request["capability"] = "instruction-specific analysis"
    before = log.read_bytes()
    result = build_execution_binding(log, request)
    assert log.read_bytes() == before
    assert result["run_id"] == manual["run_id"]
    assert result["capability"] == request["capability"]
    assert result["run_snapshot"]["work_item"]["criterion"] == "checked output"
    assert result["run_snapshot"]["fields"]["task"] == "bounded work"
    request["scope_in"].append("must not leak")
    assert "must not leak" not in result["scope_in"]
    file.write_text(json.dumps(result), encoding="utf-8")
    materialized = read_subagent_startup(root, log, file)
    assert materialized["state"] == "materialized"
    assert materialized["binding"]["instruction_basis"] == "User requested bounded analysis"


@pytest.mark.parametrize("protocols", [
    [], ["prompt_flow"], ["workflow"], ["reporting"],
    ["prompt_flow", "workflow", "reporting"],
])
def test_binding_accepts_each_effective_protocol_selection(startup, protocols):
    _, log, _, manual = startup
    request = request_for(manual)
    request["protocols"] = protocols
    binding = build_execution_binding(log, request)
    assert binding["protocols"] == protocols


@pytest.mark.parametrize("key,value", [
    ("capability", ""), ("instruction_basis", ""), ("protocols", ["workflow", {}]),
    ("scope_in", []), ("source_mode", "other"), ("run_id", "injected"),
    ("model", "pretend-selected"), ("references", [{"path": "input.md"}]),
    ("repository_fingerprint", "illegal-in-filesystem"),
])
def test_bad_request_does_not_mutate_log(startup, key, value):
    _, log, _, manual = startup
    request = request_for(manual)
    request[key] = value
    before = log.read_bytes()
    with pytest.raises(ValueError):
        build_execution_binding(log, request)
    assert log.read_bytes() == before


@pytest.mark.parametrize("field,new", [
    ("executor", "different:executor"), ("authority", "changed authority"),
    ("flow_id", "different-flow"), ("task", "changed task"),
])
def test_changed_run_context_blocks_local_read(startup, field, new):
    root, log, file, manual = startup
    binding = build_execution_binding(log, request_for(manual))
    file.write_text(json.dumps(binding), encoding="utf-8")
    text = log.read_text(encoding="utf-8")
    if field == "task":
        text = text.replace("- task: bounded work", "- task: " + new)
    else:
        text, _ = _replace_log_field(text, field, new)
    log.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        read_subagent_startup(root, log, file)
    assert "subagent.startup.read" not in log.read_text(encoding="utf-8")


def test_changed_item_requires_regeneration(startup):
    _, log, _, manual = startup
    binding = build_execution_binding(log, request_for(manual))
    assert command("skill", "workitem", "--log", str(log), "--item", "WI-1",
                   "--completion-criterion", "checked output", "--status", "in_progress",
                   "--role", "instruction:executor")[0] == 0
    with pytest.raises(ValueError):
        validate_binding_context(log.read_text(encoding="utf-8"), binding)
    renewed = build_execution_binding(log, request_for(manual))
    validate_binding_context(log.read_text(encoding="utf-8"), renewed)


@pytest.mark.parametrize("mutation", ["closed", "missing_item", "missing_identity", "mcp_bound"])
def test_unusable_run_rejected(startup, mutation):
    _, log, _, manual = startup
    text = log.read_text(encoding="utf-8")
    if mutation == "closed":
        text = text.replace("## Closure Gate\n\n- status: `pending`", "## Closure Gate\n\n- status: `done`")
    elif mutation == "missing_item":
        manual["work_item_id"] = "MISSING"
    elif mutation == "missing_identity":
        text, _ = _replace_log_field(text, "skill_id", "-")
    else:
        text, _ = _replace_log_field(text, "mcp_session_id", "session")
    log.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        build_execution_binding(log, request_for(manual))


def test_marker_stripping_rejected_and_legacy_preserved(startup):
    _, log, _, manual = startup
    validate_binding_context(log.read_text(encoding="utf-8"), manual)
    binding = build_execution_binding(log, request_for(manual))
    for removed in ["binding_origin", "run_snapshot"]:
        bad = dict(binding)
        bad.pop(removed)
        with pytest.raises(ValueError):
            validate_binding_context(log.read_text(encoding="utf-8"), bad)


def test_generated_mcp_binding_survives_session_correlation(tmp_path):
    log, run_id = _run_log(tmp_path)
    manual = _binding(run_id)
    generated = build_execution_binding(log, request_for(manual))
    async def call(name, args):
        if name == "get_startup_context":
            return _context(manual)
        assert name == "bind_skill_run"
        return {**args, "mcp_session_id": "session", "repository_fingerprint": "repo-fp", "audit_enabled": True}
    result = asyncio.run(read_mcp_subagent_startup(log, generated, call))
    assert result["state"] == "materialized"
    assert "mcp.bound" in log.read_text(encoding="utf-8")


def test_stale_mcp_binding_blocks_before_transport(tmp_path):
    log, run_id = _run_log(tmp_path)
    binding = build_execution_binding(log, request_for(_binding(run_id)))
    text, _ = _replace_log_field(log.read_text(encoding="utf-8"), "authority", "changed")
    log.write_text(text, encoding="utf-8")
    async def call(name, args):
        pytest.fail("stale run must block before transport")
    with pytest.raises(ValueError):
        asyncio.run(read_mcp_subagent_startup(log, binding, call))


def test_cli_outputs_directly_readable_binding(startup):
    root, log, file, manual = startup
    request = root / "request.json"
    request.write_text(json.dumps(request_for(manual)), encoding="utf-8")
    code, output = command("workflow", "bind-execution", "--log", str(log), "--request", str(request), "--json")
    assert code == 0, output
    file.write_text(output, encoding="utf-8")
    assert read_subagent_startup(root, log, file)["state"] == "materialized"
    request.write_text("{}", encoding="utf-8")
    code, output = command("workflow", "bind-execution", "--log", str(log), "--request", str(request))
    assert code == 1
    assert json.loads(output)["state"] == "blocked"


def test_omitted_references_defaults_empty_and_local_general_skill_supported(startup):
    _, log, _, manual = startup
    request = request_for(manual)
    request.pop("references")
    text, _ = _replace_log_field(log.read_text(encoding="utf-8"), "skill_id", "general_skill")
    log.write_text(text, encoding="utf-8")
    binding = build_execution_binding(log, request)
    assert binding["references"] == []
    request.update(source_mode="mcp", repository_fingerprint="repo-fp",
                   knowledge_access={"mode": "on_demand", "catalog_tool": "search_knowledge_catalog", "resolve_tool": "get_document_by_xid"})
    with pytest.raises(ValueError):
        build_execution_binding(log, request)


def test_request_size_and_nonfinite_numbers_rejected(startup):
    _, log, _, manual = startup
    request = request_for(manual)
    request["purpose"] = "x" * 256001
    with pytest.raises(ValueError):
        build_execution_binding(log, request)
    request["purpose"] = float("nan")
    with pytest.raises(ValueError):
        build_execution_binding(log, request)


def test_multiline_task_change_is_not_hidden(startup):
    _, log, _, manual = startup
    text = log.read_text(encoding="utf-8").replace("- task: bounded work", "- task: first line\nsecond line")
    log.write_text(text, encoding="utf-8")
    binding = build_execution_binding(log, request_for(manual))
    assert binding["run_snapshot"]["fields"]["task"] == "first line\nsecond line"
    with pytest.raises(ValueError):
        validate_binding_context(text.replace("second line", "changed second line"), binding)
