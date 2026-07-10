from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from xrefkit.cli import main
from xrefkit.goalstate import (
    _goal_lease_path,
    acquire_lease,
    append_packet,
    define_goal,
    observe_wake,
)


def test_goal_requires_acceptance_evidence_before_completion(tmp_path: Path, capsys) -> None:
    assert main([
        "goal", "define", "--root", str(tmp_path), "--goal", "migration",
        "--state", "xrefkit is authoritative",
        "--acceptance", "cli:all commands use xrefkit",
        "--acceptance", "mcp:integrated MCP starts", "--json",
    ]) == 0
    capsys.readouterr()

    assert main([
        "goal", "complete", "--root", str(tmp_path), "--goal", "migration",
        "--observed-state", "implementation finished",
        "--evidence", "cli=tests/cli.txt", "--json",
    ]) == 1
    failed = json.loads(capsys.readouterr().out)
    assert "missing acceptance evidence: ['mcp']" in failed["errors"]

    assert main([
        "goal", "complete", "--root", str(tmp_path), "--goal", "migration",
        "--observed-state", "xrefkit is authoritative",
        "--evidence", "cli=tests/cli.txt", "--evidence", "mcp=tests/mcp.txt", "--json",
    ]) == 0
    completed = json.loads(capsys.readouterr().out)
    assert completed["data"]["status"] == "complete"


def test_goal_ids_use_distinct_persisted_paths(tmp_path: Path) -> None:
    base = dict(root=str(tmp_path), state="active", acceptance=["ready:yes"], owner="owner")
    assert define_goal(Namespace(goal="a-b", **base)).ok
    assert define_goal(Namespace(goal="a_b", **base)).ok

    first = main(["goal", "show", "--root", str(tmp_path), "--goal", "a-b", "--json"])

    assert first == 0
    assert len(list((tmp_path / "work" / "goal_mode" / "goals").glob("*.json"))) == 2


def test_corrupt_lease_is_rejected_without_overwrite(tmp_path: Path) -> None:
    common = dict(root=str(tmp_path), goal="migration")
    assert append_packet(Namespace(**common, summary="continue", next_action="resume", status="valid", created_by=None, continuation_log=None, artifact=[], boundary=None, stop_condition=[], drift_check=[], source_run_key=None, trace_id=None, parent_packet=None, subgoal=None, resume_blocker=[], expiry_hint=None)).ok
    assert observe_wake(Namespace(**common, source="test", recovery_type="weekly", note=None)).ok
    lease_path = _goal_lease_path(tmp_path, "migration")
    lease_path.write_text("{broken", encoding="utf-8")

    result = acquire_lease(Namespace(**common, owner="worker", ttl_hours=1, source_packet=None))

    assert result.ok is False
    assert "corrupt persisted state" in result.errors[0]
    assert lease_path.read_text(encoding="utf-8") == "{broken"


def test_corrupt_lease_show_returns_structured_failure(tmp_path: Path) -> None:
    lease_path = _goal_lease_path(tmp_path, "migration")
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    lease_path.write_text("{broken", encoding="utf-8")

    result = main(["goal", "lease", "show", "--root", str(tmp_path), "--goal", "migration", "--json"])

    assert result == 1
