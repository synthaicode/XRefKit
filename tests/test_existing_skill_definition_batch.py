from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog


def test_tracked_existing_skill_definitions_can_be_selected_together():
    repo = Path(__file__).resolve().parents[1]
    definitions = [
        Path("skills/dotnet_change_analysis/SKILL.v1.md"),
        Path("skills/packs/constraint-derivation/code_constraint_derivation/SKILL.v1.md"),
        Path("skills/security_review/SKILL.v1.md"),
        Path("skills/packs/editorial-ops/editorial_intake/SKILL.v1.md"),
    ]

    catalog = XRefCatalog.build(repo, skill_definition_paths=definitions)
    expected = {
        "dotnet_change_analysis",
        "code_constraint_derivation",
        "security_review",
        "editorial_intake",
    }
    selected = [entry for entry in catalog.skills if entry.skill_id in expected]

    assert {entry.skill_id for entry in selected} == expected
    assert len(selected) == len(expected)
    assert all(entry.definition_format == "skill_definition_v1" for entry in selected)
    assert len({entry.definition_xid for entry in selected}) == len(expected)
