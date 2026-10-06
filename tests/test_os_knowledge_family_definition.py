from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition

CASES = [
    ("knowledge_ontology_management", "F8A2C6D1B370", "EB78A6EAFBCC", "83EDDDB5E158"),
    ("source_structure_findings_registration", "A9C4E1B7D260", "C8D4E7A19F62", "E42C9F1A6B70"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_os_knowledge_v1_migration(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path("skills/os") / skill_id / "SKILL.v1.md"
    definition = load_skill_definition(repo / relative)
    assert definition["metadata"]["xid"] == xid
    assert set(definition["metadata"]["aliases"]) == {body_xid, meta_xid}
    assert definition["metadata"]["control_refs"] == ["B1D42A6F90C3"]
    assert "CAP-" not in definition["method"]
    assert "## Reporting Contract" not in definition["method"]
    assert "Context direction guard" not in definition["method"]
    assert definition["metadata"]["inputs"] and definition["metadata"]["outputs"]
    assert f"<!-- xid: {body_xid} -->".encode() in (repo / relative.parent / "SKILL.md").read_bytes()
    assert b"skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_bytes()


def test_os_knowledge_v1_explicit_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path("skills/os") / skill / "SKILL.v1.md" for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = [entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}]
    assert len(entries) == len(CASES)
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries)
    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / Path("skills/os") / skill_id / "SKILL.v1.md")
        result = catalog.resolve_skill_knowledge(skill_id, [n["id"] for n in definition["metadata"]["knowledge_needs"]])
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []


def test_medium_os_batch_selects_without_identity_collisions():
    repo = Path(__file__).resolve().parents[1]
    skill_ids = {
        "goal_mode", "legacy_flow_skill_migration", "consultation_research_mapping",
        "knowledge_ontology_management", "source_structure_findings_registration",
    }
    paths = [Path("skills/os") / skill / "SKILL.v1.md" for skill in sorted(skill_ids)]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = [entry for entry in catalog.skills if entry.skill_id in skill_ids]
    assert {entry.skill_id for entry in entries} == skill_ids
    assert len({entry.definition_xid for entry in entries}) == len(skill_ids)
