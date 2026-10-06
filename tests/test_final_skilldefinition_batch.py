from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


PATHS = [
    Path("skills/brownfield-workflow/SKILL.v1.md"),
    Path("skills/csharp_error_policy_extraction/SKILL.v1.md"),
    Path("skills/source_structure_overview/SKILL.v1.md"),
    Path("skills/db_current_state_analysis/SKILL.v1.md"),
    Path("skills/db_design/SKILL.v1.md"),
    Path("skills/packs/batch-regression/batch-impact-regression/SKILL.v1.md"),
    Path("skills/os/domain_knowledge_catalog_preparation/SKILL.v1.md"),
    Path("skills/os/skill_flow_authoring/SKILL.v1.md"),
    Path("skills/test_tool_catalog_preparation/SKILL.v1.md"),
]


def test_final_batch_selects_together_without_identity_or_common_control_leaks():
    repo = Path(__file__).resolve().parents[1]
    definitions = [load_skill_definition(repo / path) for path in PATHS]
    xids = [definition["metadata"]["xid"] for definition in definitions]
    aliases = [
        alias
        for definition in definitions
        for alias in definition["metadata"]["aliases"]
    ]

    assert len(xids) == len(set(xids))
    assert set(xids).isdisjoint(aliases)
    assert all("CAP-" not in definition["method"] for definition in definitions)
    assert all(
        "7A2F4C8D1601"
        not in [xid for need in definition["metadata"]["knowledge_needs"] for xid in need["seed_xids"]]
        for definition in definitions
    )

    catalog = XRefCatalog.build(repo, skill_definition_paths=PATHS)
    expected = {definition["metadata"]["skill_id"] for definition in definitions}
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in expected}
    assert set(entries) == expected
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())


def test_no_public_legacy_skill_is_missing_a_v1_companion():
    repo = Path(__file__).resolve().parents[1]
    legacy_only = [
        path.parent.relative_to(repo).as_posix()
        for path in (repo / "skills").rglob("SKILL.md")
        if not (path.parent / "SKILL.v1.md").exists()
    ]
    assert legacy_only == []

