"""Check the shipped repository derivation without a stdio child environment."""

from pathlib import Path
import json
import shutil

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.mcp.cli import main
from xrefkit.mcp.repository import markdown_xid_only_text


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = (
    "agent/000_agent_entry.md",
    "docs/core/models/017_base_and_xref_layering.md",
    "docs/core/contracts/011_startup_xref_routing.md",
    "docs/core/contracts/016_uncertainty_protocol.md",
    "docs/core/contracts/053_context_direction_security_guard.md",
    "docs/core/contracts/015_shared_memory_operations.md",
)
PACK_PATH = "docs/core/contracts/079_startup_contract_pack.md"


def test_repository_startup_pack_matches_sources_and_adopted_route(capsys):
    assert main(["check-startup-pack", "--repo", str(REPOSITORY_ROOT)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["pack_source"] == "repository_document"
    assert result["stale_sources"] == []
    pack = XRefCatalog.build(REPOSITORY_ROOT).get_startup_context()[
        "startup_contract_pack"
    ]
    assert "--definition <path-to-SKILL.v1.md>" in pack["body"]
    assert "valid explicit current" in pack["body"]
    assert "local-trial adoption binds approved trial governance and sealed evidence" in pack["body"]
    assert "missing inputs refuse execution" in pack["body"]


def test_repository_and_embedded_startup_packs_match(tmp_path):
    repository_pack = XRefCatalog.build(REPOSITORY_ROOT).get_startup_context()[
        "startup_contract_pack"
    ]
    embedded_pack = XRefCatalog.build(tmp_path).get_startup_context()[
        "startup_contract_pack"
    ]
    assert repository_pack["pack_source"] == "repository_document"
    assert embedded_pack["pack_source"] == "embedded_fallback"
    assert embedded_pack["source_hashes"] == repository_pack["source_hashes"], (
        "Update the packaged copies of the startup source documents."
    )
    source_list = "\nSources:\n"
    _, repository_separator, repository_body = repository_pack["body"].partition(source_list)
    _, embedded_separator, embedded_body = embedded_pack["body"].partition(source_list)
    assert repository_separator and embedded_separator, "Both packs must have a Sources list."
    assert markdown_xid_only_text(embedded_body) == repository_body, (
        "Update the model-facing text in both the repository and embedded startup packs."
    )


def test_source_change_still_fails_official_pack_check(tmp_path, capsys):
    for relative_path in (*SOURCE_PATHS, PACK_PATH):
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / relative_path, target)
    assert main(["check-startup-pack", "--repo", str(tmp_path)]) == 0
    capsys.readouterr()
    source = tmp_path / SOURCE_PATHS[0]
    with source.open("ab") as stream:
        stream.write(b"\nAn independently changed source obligation.\n")
    assert main(["check-startup-pack", "--repo", str(tmp_path)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["stale"] is True
    assert [item["xid"] for item in result["stale_sources"]] == ["0B5C58B5E5B2"]
