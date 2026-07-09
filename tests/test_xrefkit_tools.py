from __future__ import annotations

import json
from pathlib import Path

from xrefkit.cli import main
from tools.site_build import build_site


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_tool_contracts_are_listed_by_stable_id_and_xid(capsys) -> None:
    assert main(["tools", "--root", str(REPO_ROOT), "list", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    by_id = {item["tool_id"]: item for item in payload}
    assert by_id["structure_graph_report"]["xid"] == "A1C4E7B92001"
    assert by_id["site_build"]["execution_location"] == "client"


def test_tool_show_accepts_xid(capsys) -> None:
    assert main(["tools", "--root", str(REPO_ROOT), "show", "A1C4E7B92004", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["tool_id"] == "di_registration_report"


def test_site_builder_expands_trees_and_checks_links(tmp_path: Path) -> None:
    (tmp_path / "source").mkdir()
    (tmp_path / "source/index.html").write_text('<img src="asset.png">', encoding="utf-8")
    (tmp_path / "source/asset.png").write_bytes(b"png")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"schema":"xrefkit.site/v1","trees":[{"source":"source","target":""}]}',
        encoding="utf-8",
    )

    result = build_site(tmp_path, manifest, tmp_path / "out", check=False)

    assert result["ok"] is True
    assert (tmp_path / "out/index.html").is_file()
