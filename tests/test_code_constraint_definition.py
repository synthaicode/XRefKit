from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


def test_code_constraint_v1_parses_with_unique_legacy_aliases_and_catalog_selection():
    repo = Path(__file__).resolve().parents[1]
    relative = Path("skills/packs/constraint-derivation/code_constraint_derivation/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]

    assert metadata["schema_version"] == 1
    assert metadata["xid"] == "7C4E9A1B2D60"
    assert set(metadata["aliases"]) == {"D4701BFC6EA4", "D4701BFC6EA5"}
    assert metadata["xid"] not in metadata["aliases"]
    assert len(metadata["aliases"]) == len(set(metadata["aliases"]))
    assert not {"capability", "tuning", "responsibility", "execution_mode", "model_tier", "maturity"} & set(metadata)

    catalog = XRefCatalog.build(repo, skill_definition_paths=[relative])
    entries = [entry for entry in catalog.skills if entry.skill_id == "code_constraint_derivation"]
    assert len(entries) == 1
    assert entries[0].definition_format == "skill_definition_v1"
    assert entries[0].definition_xid == metadata["xid"]


def test_code_constraint_v1_resolves_selected_knowledge_and_legacy_files_are_unchanged():
    repo = Path(__file__).resolve().parents[1]
    relative = Path("skills/packs/constraint-derivation/code_constraint_derivation/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]

    catalog = XRefCatalog.build(repo, skill_definition_paths=[relative])
    result = catalog.resolve_skill_knowledge("code_constraint_derivation", need_ids)
    assert result["unresolved_activation"] == []
    assert result["unsatisfied_required"] == []
    assert [need["id"] for need in result["needs"]] == need_ids
    assert all(need["activation_state"] == "active" for need in result["needs"])
    assert all(need["satisfied"] is True for need in result["needs"])

    meta = (repo / "skills/packs/constraint-derivation/code_constraint_derivation/meta.md").read_text(encoding="utf-8")
    legacy = (repo / "skills/packs/constraint-derivation/code_constraint_derivation/SKILL.md").read_text(encoding="utf-8")
    assert "skill_doc: `./SKILL.md`" in meta
    assert "<!-- xid: D4701BFC6EA4 -->" in meta
    assert "<!-- xid: D4701BFC6EA5 -->" in legacy
    assert "## Reporting Contract" not in definition["method"]
    assert "111D282CA0EA" in definition["metadata"]["control_refs"]
