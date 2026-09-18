from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition

CASES = [
    ("requirements_flow", "D4A7C91E2B60", "2B70BBF7B7BB", "6720268498FD"),
    ("investigation_flow", "E8B2D6A4C190", "9C0115875B0C", "3C06EF778A20"),
    ("manufacturing_self_check", "F1C8A3E6B270", "5D4E91B0D110", "60B1B69B0984"),
    ("pptx_spec_traceability", "A6D3F8B1C520", "4C8E2B1F6A20", "7F4C1A2D9E60"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_workflow_v1_migration(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path("skills") / skill_id / "SKILL.v1.md"
    definition = load_skill_definition(repo / relative)
    assert definition["metadata"]["xid"] == xid
    assert set(definition["metadata"]["aliases"]) == {body_xid, meta_xid}
    assert definition["metadata"]["control_refs"] == []
    assert "CAP-" not in definition["method"]
    assert "## Reporting Contract" not in definition["method"]
    assert "## Required Knowledge (XID)" not in definition["method"]
    assert "Context direction guard" not in definition["method"]
    assert f"<!-- xid: {body_xid} -->".encode() in (repo / relative.parent / "SKILL.md").read_bytes()
    assert b"skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_bytes()


def test_workflow_v1_explicit_batch_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path("skills") / skill / "SKILL.v1.md" for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = [entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}]
    assert len(entries) == len(CASES)
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries)
    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / Path("skills") / skill_id / "SKILL.v1.md")
        ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []


def test_complete_simple_flow_batch_selects_without_identity_collisions():
    repo = Path(__file__).resolve().parents[1]
    skill_ids = {
        "cab_review_flow", "presentation_flow_review", "estimation_flow",
        "release_planning_flow", "requirements_flow", "investigation_flow",
        "manufacturing_self_check", "pptx_spec_traceability",
    }
    paths = [Path("skills") / skill_id / "SKILL.v1.md" for skill_id in sorted(skill_ids)]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = [entry for entry in catalog.skills if entry.skill_id in skill_ids]

    assert {entry.skill_id for entry in entries} == skill_ids
    assert len({entry.definition_xid for entry in entries}) == len(skill_ids)
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries)
