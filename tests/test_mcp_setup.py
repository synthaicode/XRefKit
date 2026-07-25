from __future__ import annotations

import json
from pathlib import Path

from xrefkit.__main__ import main


def test_mcp_setup_writes_reviewable_workspace(tmp_path: Path, capsys) -> None:
    output = tmp_path / "setup-output"
    root = tmp_path / "repo"

    assert main(["mcp", "setup", "--repo", str(root), "--output", str(output), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["output"] == str(output.resolve())
    assert (output / "SETUP.md").is_file()
    assert (output / "vscode-mcp.json").is_file()
    assert (output / "AGENTS.md.append.md").is_file()
    assert (output / "CLAUDE.md.append.md").is_file()
    assert (output / "import-report.json").is_file()

    vscode = json.loads((output / "vscode-mcp.json").read_text(encoding="utf-8"))
    server = vscode["servers"]["xrefkit"]
    assert server["type"] == "stdio"
    assert server["args"][-2:] == ["--transport", "stdio"]


def test_mcp_setup_imports_existing_batch_skill_before_writing_report(tmp_path: Path, capsys) -> None:
    source = tmp_path / "existing"
    skill = source / "skills" / "legacy-review"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Legacy Review\n\nReview the supplied change.\n", encoding="utf-8")
    root = tmp_path / "repo"
    output = tmp_path / "setup-output"

    exit_code = main(
        [
            "mcp",
            "setup",
            "--repo",
            str(root),
            "--import",
            str(source),
            "--output",
            str(output),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code in {0, 1}
    assert (root / "skills" / "imported.legacy-review" / "SKILL.md").is_file()
    report = json.loads((output / "import-report.json").read_text(encoding="utf-8"))
    assert report["import"]["converted_skills"][0]["skill_id"] == "imported.legacy-review"
    assert payload["output"] == str(output.resolve())


def test_mcp_setup_apply_copies_config_and_appends_instructions(tmp_path: Path, capsys) -> None:
    output = tmp_path / "setup-output"
    root = tmp_path / "repo"
    root.mkdir()
    assert main(["mcp", "setup", "--repo", str(root), "--output", str(output)]) == 0
    capsys.readouterr()

    assert main(["mcp", "setup-apply", "--source", str(output), "--repo", str(root)]) == 0
    capsys.readouterr()
    assert (root / ".vscode" / "mcp.json").is_file()
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "XRefKit MCP Skill Routing" in agents

    assert main(["mcp", "setup-apply", "--source", str(output), "--repo", str(root)]) == 0
    assert (root / "AGENTS.md").read_text(encoding="utf-8").count("XRefKit MCP Skill Routing") == 1
