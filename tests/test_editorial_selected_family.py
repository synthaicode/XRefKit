from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("draft_authoring", "B6A9D3F1C720", "BFEF855AAA8D", "51FDA8671D61"),
    ("fact_review", "D4E8B2A6F190", "0AA2CEC66CB2", "7687FD352C4C"),
    ("reader_experience_review", "E1C7A5D9B430", "D84028E6F515", "79372C67DBA0"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_editorial_v1_parse_aliases_and_legacy(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path(f"skills/packs/editorial-ops/{skill_id}/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["control_refs"] == []
    assert "## Reporting Contract" not in definition["method"]
    assert "## Required Knowledge (XID)" not in definition["method"]
    assert "skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_text()


def test_editorial_v1_explicit_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path(f"skills/packs/editorial-ops/{skill}/SKILL.v1.md") for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}}
    assert set(entries) == {case[0] for case in CASES}
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())
    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / f"skills/packs/editorial-ops/{skill_id}/SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []
