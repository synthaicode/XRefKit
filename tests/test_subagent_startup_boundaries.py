import hashlib
import json
from pathlib import Path

import pytest

import xrefkit.subagent_startup as adapter
from xrefkit.__main__ import main
from xrefkit.subagent_startup import (
    MAX_FILE_BYTES,
    PROTOCOL_SOURCES,
    STARTUP_SOURCES,
    read_subagent_startup,
)


def _command(*args):
    return main(list(args))


@pytest.fixture
def startup(tmp_path):
    for path, xid in (*STARTUP_SOURCES, *PROTOCOL_SOURCES.values()):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"<!-- xid: {xid} -->\n# Contract\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("Use startup contract", encoding="utf-8")
    catalog = tmp_path / "knowledge/index.md"
    catalog.parent.mkdir()
    catalog.write_text("catalog", encoding="utf-8")
    log = tmp_path / "work/run.md"
    assert _command(
        "workflow", "run", "--root", str(tmp_path), "--task", "bounded work",
        "--out", str(log), "--completion-condition", "checked output", "--json",
    ) == 0
    run_id = next(
        line.split("`")[1] for line in log.read_text().splitlines()
        if line.startswith("- run_id:")
    )
    assert _command(
        "skill", "workitem", "--log", str(log), "--item", "WI-1",
        "--text", "bounded work", "--completion-criterion", "checked output",
        "--status", "pending", "--role", "instruction:executor",
    ) == 0
    reference = tmp_path / "input.md"
    reference.write_text("Task input", encoding="utf-8")
    binding = {
        "schema_version": 1, "source_mode": "filesystem", "run_id": run_id,
        "work_item_id": "WI-1", "purpose": "bounded work", "capability": "analysis",
        "tuning": "local", "responsibility": "read only", "scope_in": ["input.md"],
        "scope_out": ["publication"], "stop_conditions": ["missing evidence"],
        "protocols": ["workflow"],
        "knowledge_access": {"mode": "on_demand", "catalog": "knowledge/index.md"},
        "references": [{"path": "input.md", "sha256": hashlib.sha256(reference.read_bytes()).hexdigest()}],
    }
    binding_path = tmp_path / "binding.json"
    binding_path.write_text(json.dumps(binding), encoding="utf-8")
    return tmp_path, log, binding_path, binding


def _write_binding(path, binding):
    path.write_text(json.dumps(binding), encoding="utf-8")


@pytest.mark.parametrize("status,extra,pattern", [
    ("done", (), "pending/in_progress"),
    ("blocked", ("--criterion-unknown-reason", "waiting for evidence"), "pending/in_progress"),
])
def test_finished_or_blocked_work_item_cannot_materialize(startup, status, extra, pattern):
    root, log, binding_path, _ = startup
    assert _command(
        "skill", "workitem", "--log", str(log), "--item", "WI-1",
        "--status", status, "--role", "instruction:executor",
        "--completion-criterion", "checked output", *extra,
    ) == 0
    before = log.read_bytes()
    with pytest.raises(ValueError, match=pattern):
        read_subagent_startup(root, log, binding_path)
    assert log.read_bytes() == before


def test_single_file_size_limit_blocks_without_acknowledgement(startup):
    root, log, binding_path, binding = startup
    reference = root / "input.md"
    reference.write_bytes(b"x" * (MAX_FILE_BYTES + 1))
    binding["references"][0]["sha256"] = hashlib.sha256(reference.read_bytes()).hexdigest()
    _write_binding(binding_path, binding)
    before = log.read_bytes()
    with pytest.raises(ValueError, match="exceeds byte limit"):
        read_subagent_startup(root, log, binding_path)
    assert log.read_bytes() == before


def test_total_context_size_limit_blocks_without_acknowledgement(startup):
    root, log, binding_path, binding = startup
    references = []
    for index in range(5):
        path = root / f"large-{index}.md"
        path.write_bytes(b"x" * 220_000)
        references.append({"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    binding["references"] = references
    _write_binding(binding_path, binding)
    before = log.read_bytes()
    with pytest.raises(ValueError, match="total byte limit"):
        read_subagent_startup(root, log, binding_path)
    assert log.read_bytes() == before


def test_symlink_reference_cannot_escape_root(startup, tmp_path):
    root, log, binding_path, binding = startup
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("outside", encoding="utf-8")
    link = root / "link.md"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable on this host")
    binding["references"] = [{"path": "link.md", "sha256": hashlib.sha256(outside.read_bytes()).hexdigest()}]
    _write_binding(binding_path, binding)
    with pytest.raises(ValueError, match="within --root"):
        read_subagent_startup(root, log, binding_path)


def test_logged_skill_body_is_loaded_only_after_opened_gate(startup):
    root, log, binding_path, _ = startup
    skill = root / "skill" / "SKILL.md"
    skill.parent.mkdir()
    skill.write_text("# Opened procedure\n", encoding="utf-8")
    text = log.read_text()
    log.write_text(text.replace("- skill_doc: `-`", "- skill_doc: `skill/SKILL.md`"), encoding="utf-8")
    result = read_subagent_startup(root, log, binding_path)
    document = next(doc for doc in result["documents"] if doc["path"] == "skill/SKILL.md")
    assert document["body"].replace("\r\n", "\n") == "# Opened procedure\n"


def test_read_race_is_rechecked_before_acknowledgement(startup, monkeypatch):
    root, log, binding_path, _ = startup
    original = adapter._read
    calls = {"input.md": 0}

    def racing_read(read_root, value, **kwargs):
        result = original(read_root, value, **kwargs)
        if value == "input.md":
            calls["input.md"] += 1
            if calls["input.md"] == 1:
                (root / "input.md").write_text("changed during read", encoding="utf-8")
        return result

    monkeypatch.setattr(adapter, "_read", racing_read)
    before = log.read_bytes()
    with pytest.raises(ValueError, match="revision mismatch"):
        read_subagent_startup(root, log, binding_path)
    assert log.read_bytes() == before
