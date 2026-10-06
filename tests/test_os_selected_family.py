from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("goal_mode", "E6A2C9F4B710", "8E17D4C2B6A5", "5C2D7A91E4F3"),
    ("legacy_flow_skill_migration", "F8C1A5D3E920", "C5E2A7D19F84", "8F1D7A2C4B63"),
    ("consultation_research_mapping", "A4D7B2E9C610", "0EE4E8E8223E", "0985CDA7359E"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_os_v1_parse_concrete_metadata_aliases_and_legacy(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path(f"skills/os/{skill_id}/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["inputs"] and metadata["outputs"]
    assert metadata["control_refs"] == []
    assert "## Reporting Contract" not in definition["method"]
    assert "## Required Knowledge (XID)" not in definition["method"]
    assert "CAP-" not in definition["method"]
    assert "skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_text()


def test_os_v1_explicit_batch_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path(f"skills/os/{skill}/SKILL.v1.md") for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    ids = {case[0] for case in CASES}
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in ids}
    assert set(entries) == ids
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())
    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / f"skills/os/{skill_id}/SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []
