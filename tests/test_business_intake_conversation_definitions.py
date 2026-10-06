from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("conversation_topic_branch_mapping", "9D6A4F2B1C80", "2E755FFA0A86", "59777C84933D", []),
    ("decision_topology_analysis", "B7E3C1A9D640", "502BB91D25FA", "2C927E868B25", ["7B3E5D1A6102", "7B3E5D1A6103"]),
]


def test_business_intake_v1_definitions_parse_aliases_and_preserve_legacy():
    repo = Path(__file__).resolve().parents[1]
    for skill_id, xid, body_xid, meta_xid, _ in CASES:
        relative = Path("skills/packs/business-intake") / skill_id / "SKILL.v1.md"
        definition = load_skill_definition(repo / relative)
        metadata = definition["metadata"]
        assert metadata["xid"] == xid
        assert set(metadata["aliases"]) == {body_xid, meta_xid}
        assert metadata["control_refs"] == []
        for forbidden in ("capability", "tuning", "responsibility", "execution_mode", "model", "maturity"):
            assert forbidden not in metadata
        assert "## Context Direction Guard" not in definition["method"]
        assert "## Reporting Contract" not in definition["method"]
        assert f"<!-- xid: {body_xid} -->" in (repo / relative.parent / "SKILL.md").read_text(encoding="utf-8")
        assert f"skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_text(encoding="utf-8")


def test_business_intake_v1_explicit_catalog_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path("skills/packs/business-intake") / skill_id / "SKILL.v1.md" for skill_id, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = [entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}]
    assert len(entries) == 2
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries)
    assert {entry.definition_xid for entry in entries} == {case[1] for case in CASES}
    for skill_id, _, _, _, seed_xids in CASES:
        definition = load_skill_definition(repo / (Path("skills/packs/business-intake") / skill_id / "SKILL.v1.md"))
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        if need_ids:
            resolved = catalog.resolve_skill_knowledge(skill_id, need_ids)
            assert resolved["unresolved_activation"] == []
            assert resolved["unsatisfied_required"] == []
            assert {candidate["xid"] for need in resolved["needs"] for candidate in need["candidates"]} >= set(seed_xids)

