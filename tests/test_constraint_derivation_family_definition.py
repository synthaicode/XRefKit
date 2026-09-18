from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("integration_constraint_derivation", "9A1C4E7D2B60", "E547F90B1235", "E547F90B1234", ["81A6C4E2B190", "6F0D7C1A2E44"]),
    ("integration_scenario_derivation", "5F8B2D6A1C90", "F6923D1E80C9", "F6923D1E80C8", ["81A6C4E2B190", "C3F60AEB5D93"]),
    ("logic_constraint_derivation", "3D7A9E2B4C60", "D436E8FA0124", "D436E8FA0123", ["81A6C4E2B190", "4E5B8923C912"]),
    ("ui_constraint_derivation", "6B1F8D3A5E20", "C325D7E9F123", "C325D7E9F122", ["81A6C4E2B190", "31C5A06B7E22"]),
    ("constraint_derivation_index", "A4C9E2B7D160", "A103B5C7D901", "A103B5C7D900", ["81A6C4E2B190"]),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid,seed_xids", CASES)
def test_constraint_derivation_v1_migration(skill_id, xid, body_xid, meta_xid, seed_xids):
    repo = Path(__file__).resolve().parents[1]
    relative = Path("skills/packs/constraint-derivation") / skill_id / "SKILL.v1.md"
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["control_refs"] == ["111D282CA0EA"]
    assert "## Reporting Contract" not in definition["method"]
    assert "## Required Knowledge (XID)" not in definition["method"]
    assert "Context direction guard" not in definition["method"]

    legacy = (repo / relative.parent / "SKILL.md").read_bytes()
    assert f"<!-- xid: {body_xid} -->".encode() in legacy
    assert f"skill_doc: `./SKILL.md`".encode() in (repo / relative.parent / "meta.md").read_bytes()


def test_constraint_derivation_v1_explicit_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path("skills/packs/constraint-derivation") / skill / "SKILL.v1.md" for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = [entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}]
    assert len(entries) == len(CASES)
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries)
    assert {entry.definition_xid for entry in entries} == {case[1] for case in CASES}

    for skill_id, _, _, _, seed_xids in CASES:
        relative = Path("skills/packs/constraint-derivation") / skill_id / "SKILL.v1.md"
        definition = load_skill_definition(repo / relative)
        result = catalog.resolve_skill_knowledge(skill_id, [need["id"] for need in definition["metadata"]["knowledge_needs"]])
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []
        for expected, need in zip(seed_xids, result["needs"], strict=True):
            assert expected in [candidate["xid"] for candidate in need["candidates"]]


def test_complete_constraint_derivation_family_selects_without_identity_collisions():
    repo = Path(__file__).resolve().parents[1]
    family_root = Path("skills/packs/constraint-derivation")
    paths = sorted(family_root.glob("*/SKILL.v1.md"))
    relative_paths = [path.relative_to(repo) if path.is_absolute() else path for path in paths]

    assert len(relative_paths) == 11
    catalog = XRefCatalog.build(repo, skill_definition_paths=relative_paths)
    family_ids = {path.parent.name for path in relative_paths}
    entries = [entry for entry in catalog.skills if entry.skill_id in family_ids]

    assert {entry.skill_id for entry in entries} == family_ids
    assert len({entry.definition_xid for entry in entries}) == 11
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries)
