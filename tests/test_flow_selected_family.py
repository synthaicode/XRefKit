from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("cab_review_flow", "C7A4E9B2D610", "33D0A3A01B47", "AE3979CD83C0"),
    ("presentation_flow_review", "D8F1A6C3B520", "B2F5D8C31E64", "A1E4C7B29D53"),
    ("estimation_flow", "E2B7D9F4A130", "FB65EC653F0F", "EA208AA244DF"),
    ("release_planning_flow", "F5C8A2E6B710", "D216FD3C726C", "22DE60C2BBCB"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_flow_v1_parse_aliases_and_boundaries(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path(f"skills/{skill_id}/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["control_refs"] == []
    assert "CAP-" not in definition["method"]
    assert "## Reporting Contract" not in definition["method"]
    assert "## Required Knowledge (XID)" not in definition["method"]
    assert "skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_text()


def test_flow_v1_batch_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path(f"skills/{skill}/SKILL.v1.md") for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}}
    assert set(entries) == {case[0] for case in CASES}
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())
    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / f"skills/{skill_id}/SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []
