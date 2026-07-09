from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from xrefkit.gate import cmd_gate


def test_cutover_readiness_reports_missing_surfaces(tmp_path: Path, capsys) -> None:
    (tmp_path / "xrefkit.toml").write_text(
        '[runtime]\ncommand_authority = "legacy_authoritative"\n', encoding="utf-8"
    )
    args = Namespace(
        gate_cmd="eval",
        profile="command-cutover-readiness",
        root=str(tmp_path),
        json=True,
    )

    assert cmd_gate(args) == 1
    result = json.loads(capsys.readouterr().out)
    assert "package_manifest" in result["failed"]


def test_cutover_readiness_requires_legacy_entry_state(tmp_path: Path, capsys) -> None:
    required = [
        "pyproject.toml",
        "xrefkit/resources/base/contracts.json",
        "xrefkit/resources/base/model_body.md",
        "tools/contracts.yaml",
        "knowledge/source_analysis/source_structure_catalog.yaml",
        "xrefkit/mcp/server.py",
        "tools/site_build.py",
        "site/source_manifest.json",
    ]
    for relative in required:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    (tmp_path / "xrefkit.toml").write_text(
        '[runtime]\ncommand_authority = "xrefkit_authoritative"\n', encoding="utf-8"
    )
    args = Namespace(
        gate_cmd="eval",
        profile="command-cutover-readiness",
        root=str(tmp_path),
        json=True,
    )

    assert cmd_gate(args) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["failed"] == ["legacy_authority_entry_state"]
