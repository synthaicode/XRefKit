from __future__ import annotations

import json
from pathlib import Path

from xrefkit.cli import main


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
