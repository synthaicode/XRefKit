from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = {
    "brownfield-workflow": ("brownfield_workflow", "E1A7C4D9B260", "A17C4E8B2D91", "9B3D7A1C4E20"),
    "csharp_error_policy_extraction": ("csharp_error_policy_extraction", "F2B8D5A1C370", "FE342FB520D0", "B150A2A54169"),
    "source_structure_overview": ("source_structure_overview", "A6E3C9F2B470", "423C8B8F8AD0", "907B100F9F9D"),
}


def test_tracked_trio_parse_aliases_metadata_and_legacy_readability():
    repo = Path(__file__).resolve().parents[1]
    for directory, (skill_id, xid, body_xid, meta_xid) in CASES.items():
        path = repo / "skills" / directory / "SKILL.v1.md"
        definition = load_skill_definition(path)
        metadata = definition["metadata"]
        assert metadata["skill_id"] == skill_id
        assert metadata["xid"] == xid
        assert set(metadata["aliases"]) == {body_xid, meta_xid}
        assert metadata["control_refs"] == []
        for forbidden in ("capability", "tuning", "responsibility", "execution_mode", "model", "maturity"):
            assert forbidden not in metadata
        for common in ("## Reporting Contract", "## Logging", "## Context Direction Guard"):
            assert common not in definition["method"]
        assert f"<!-- xid: {body_xid} -->" in (repo / "skills" / directory / "SKILL.md").read_text(encoding="utf-8")
        assert f"<!-- xid: {meta_xid} -->" in (repo / "skills" / directory / "meta.md").read_text(encoding="utf-8")


def test_tracked_trio_combined_catalog_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [repo / "skills" / directory / "SKILL.v1.md" for directory in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES.values()}}
    assert set(entries) == {case[0] for case in CASES.values()}
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())
    for directory, (skill_id, *_rest) in CASES.items():
        definition = load_skill_definition(repo / "skills" / directory / "SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []
