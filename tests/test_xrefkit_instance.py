from __future__ import annotations

import json
from pathlib import Path

from xrefkit.cli import main
from xrefkit.instance import load_instance_manifest


def test_init_creates_manifest_and_startup_files(tmp_path: Path, capsys) -> None:
    result = main(["init", "--root", str(tmp_path), "--instance-id", "sample", "--json"])

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command_authority"] == "legacy_authoritative"
    assert (tmp_path / "xrefkit.toml").is_file()
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / "CHATGPT.md").is_file()
    assert load_instance_manifest(tmp_path / "xrefkit.toml").startup_xid == "C3A1F78D9B22"


def test_init_preserves_existing_startup_file(tmp_path: Path, capsys) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_text("custom\n", encoding="utf-8")

    assert main(["init", "--root", str(tmp_path), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert "AGENTS.md" in payload["preserved"]
    assert agents.read_text(encoding="utf-8") == "custom\n"


def test_unified_cli_dispatches_xref(tmp_path: Path, capsys) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ok.md").write_text(
        '<!-- xid: A01234567890 -->\n<a id="xid-A01234567890"></a>\n\n# Ok\n',
        encoding="utf-8",
    )

    assert main(["xref", "check", "--root", str(tmp_path), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["issues"] == []
    assert payload["index_size"] == 1
