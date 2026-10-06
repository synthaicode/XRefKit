from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition

CASES = [
    ("crosspost_release", "B7D2A9F4C160", "A3FD70D101B7", "E2E73BDF143A"),
    ("editorial_ops_index", "C8E1A6D3B270", "67179146EEB3", "14BEA21097F6"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_editorial_v1_migration(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path("skills/packs/editorial-ops") / skill_id / "SKILL.v1.md"
    definition = load_skill_definition(repo / relative)
    assert definition["metadata"]["xid"] == xid
    assert set(definition["metadata"]["aliases"]) == {body_xid, meta_xid}
    assert definition["metadata"]["control_refs"] == []
    assert "## Reporting Contract" not in definition["method"]
    assert "## Required Knowledge (XID)" not in definition["method"]
    assert "Context direction guard" not in definition["method"]
    assert "human" in definition["method"].lower()
    assert f"<!-- xid: {body_xid} -->".encode() in (repo / relative.parent / "SKILL.md").read_bytes()
    assert b"skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_bytes()


def test_editorial_v1_explicit_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path("skills/packs/editorial-ops") / skill / "SKILL.v1.md" for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = [entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}]
    assert len(entries) == 2
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries)
    for skill_id, *_ in CASES:
        relative = Path("skills/packs/editorial-ops") / skill_id / "SKILL.v1.md"
        definition = load_skill_definition(repo / relative)
        needs = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, needs)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []


def test_complete_editorial_family_selects_without_identity_collisions():
    repo = Path(__file__).resolve().parents[1]
    family_root = Path("skills/packs/editorial-ops")
    paths = sorted(family_root.glob("*/SKILL.v1.md"))

    assert len(paths) == 6
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    family_ids = {path.parent.name for path in paths}
    entries = [entry for entry in catalog.skills if entry.skill_id in family_ids]

    assert {entry.skill_id for entry in entries} == family_ids
    assert len({entry.definition_xid for entry in entries}) == 6
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries)
