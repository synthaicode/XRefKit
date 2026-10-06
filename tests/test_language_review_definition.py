from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("csharp_review", "F1A7C3D9E240", "466B980B8ED3", "218463E0F3ED"),
    ("python_review", "F1A7C3D9E241", "B4C1D2E3F4A6", "B4C1D2E3F4A5"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_language_review_v1_metadata_aliases_boundaries_and_legacy(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path(f"skills/{skill_id}/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["control_refs"] == []
    forbidden = {"capability", "tuning", "responsibility", "execution_mode", "model", "maturity"}
    assert forbidden.isdisjoint(metadata)
    for common_section in (
        "## Reporting Contract",
        "## Required Knowledge (XID)",
        "## Logging",
        "## Context Direction Guard",
        "## Execution Role",
        "## Check Role",
        "## Quality Gate",
    ):
        assert common_section not in definition["method"]
    assert "unknown" in definition["method"]
    assert "handoff" in definition["method"]
    legacy = (repo / relative.parent / "SKILL.md").read_bytes()
    assert legacy.startswith(f"<!-- xid: {body_xid} -->".encode())
    meta = (repo / relative.parent / "meta.md").read_text(encoding="utf-8")
    assert f"<a id=\"xid-{meta_xid}\"></a>" in meta
    assert "skill_doc: `./SKILL.md`" in meta


def test_language_review_v1_explicit_catalog_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path(f"skills/{skill_id}/SKILL.v1.md") for skill_id, *_ in CASES]
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
        assert [need["id"] for need in result["needs"]] == need_ids
