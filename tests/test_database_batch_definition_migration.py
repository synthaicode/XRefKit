from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("db_current_state_analysis", "B6D4A1E9C730", "C48A0E2D91F5", "6B8C70DA119E"),
    ("db_design", "C7E5B2F0D841", "A68F54D72C19", "5D7C2A90B631"),
    (
        "batch_impact_regression",
        "E8F6C3A1D952",
        "517E99B3082E",
        "9D2E6A4C7B81",
    ),
]


def _paths(repo: Path):
    return [
        Path("skills/db_current_state_analysis/SKILL.v1.md"),
        Path("skills/db_design/SKILL.v1.md"),
        Path("skills/packs/batch-regression/batch-impact-regression/SKILL.v1.md"),
    ]


def test_database_batch_v1_definitions_parse_with_aliases_and_preserve_legacy():
    repo = Path(__file__).resolve().parents[1]
    for skill_id, xid, body_xid, meta_xid in CASES:
        relative = next(p for p in _paths(repo) if load_skill_definition(repo / p)["metadata"]["skill_id"] == skill_id)
        definition = load_skill_definition(repo / relative)
        metadata = definition["metadata"]
        assert metadata["xid"] == xid
        assert set(metadata["aliases"]) == {body_xid, meta_xid}
        assert metadata["control_refs"] == []
        assert not {"capability", "tuning", "responsibility", "execution_mode", "model", "maturity"} & metadata.keys()
        assert "CAP-" not in definition["method"]
        assert "Skill operating contract" not in definition["method"]
        assert "Context direction guard" not in definition["method"]
        legacy_dir = repo / relative.parent
        assert f"<!-- xid: {body_xid} -->" in (legacy_dir / "SKILL.md").read_text(encoding="utf-8")
        assert f"<!-- xid: {meta_xid} -->" in (legacy_dir / "meta.md").read_text(encoding="utf-8")


def test_database_batch_combined_explicit_catalog_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = _paths(repo)
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = {entry.skill_id: entry for entry in catalog.skills}
    assert set(entries) >= {case[0] for case in CASES}
    assert all(entries[case[0]].definition_format == "skill_definition_v1" for case in CASES)
    assert {entries[case[0]].definition_xid for case in CASES} == {case[1] for case in CASES}

    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / next(p for p in paths if load_skill_definition(repo / p)["metadata"]["skill_id"] == skill_id))
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        resolved = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert resolved["unresolved_activation"] == []
        assert resolved["unsatisfied_required"] == []


def test_domain_boundaries_and_forbidden_common_refs_are_explicit():
    repo = Path(__file__).resolve().parents[1]
    current = load_skill_definition(repo / "skills/db_current_state_analysis/SKILL.v1.md")
    design = load_skill_definition(repo / "skills/db_design/SKILL.v1.md")
    batch = load_skill_definition(repo / "skills/packs/batch-regression/batch-impact-regression/SKILL.v1.md")
    assert {need["id"] for need in current["metadata"]["knowledge_needs"]} == {
        "database_current_state_analysis_viewpoints",
        "database_design_viewpoints",
        "current_source_structure_findings_catalog",
        "csharp_naming_convention_extraction",
    }
    assert {need["id"] for need in design["metadata"]["knowledge_needs"]} == {
        "database_design_viewpoints",
        "database_current_state_analysis_viewpoints",
        "current_source_structure_findings_catalog",
        "csharp_naming_convention_extraction",
        "design_constraint_derivation_catalog",
    }
    assert batch["metadata"]["knowledge_needs"] == []
    common_names = {"skill_operating_contract", "context_direction_guard", "workflow", "reporting", "logging"}
    common_xids = {"B7A2C94F0E61", "7A2F4C8D1601", "6B2D9F4A1C73"}
    for definition in (current, design, batch):
        for need in definition["metadata"]["knowledge_needs"]:
            assert need["id"] not in common_names
            assert not common_xids.intersection(need["seed_xids"])
    assert "SQL export" in current["method"]
    assert "design" in current["method"].lower()
    assert any("production" in value.lower() for value in batch["metadata"]["exclusions"])
    assert "baseline" in batch["method"]
