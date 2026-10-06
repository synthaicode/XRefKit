from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("async_constraint_derivation", "9A4C7E1D2B60", "F6580A1C2344", "F6580A1C2345"),
    ("auth_constraint_derivation", "C8F2A6D1E430", "A7691B2D3457", "A7691B2D3456"),
    ("commonality_derivation", "E7B3C951A2D0", "B87A2C3E4568", "B87A2C3E4567"),
    ("cross_constraint_derivation", "F4A8D2C6B190", "E5812C0D7FB7", "E5812C0D7FB6"),
    ("design_constraint_derivation", "A6D9F3B1C720", "B214C6D8E012", "B214C6D8E011"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_selected_constraint_derivation_v1(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path(f"skills/packs/constraint-derivation/{skill_id}/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["control_refs"] == ["111D282CA0EA"]
    assert "## Reporting Contract" not in definition["method"]
    assert "## Required Knowledge (XID)" not in definition["method"]
    assert f"skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_text()


def test_selected_constraint_derivation_catalog_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path(f"skills/packs/constraint-derivation/{skill}/SKILL.v1.md") for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}}
    assert set(entries) == {case[0] for case in CASES}
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())
    for skill_id, _, _, _ in CASES:
        definition = load_skill_definition(repo / f"skills/packs/constraint-derivation/{skill_id}/SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []
