from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


PATHS = [
    Path("skills/design_flow/SKILL.v1.md"),
    Path("skills/planning_flow/SKILL.v1.md"),
    Path("skills/packs/business-intake/business_learning_interview/SKILL.v1.md"),
    Path("skills/packs/business-intake/business_intake_scoping/SKILL.v1.md"),
    Path("skills/packs/business-intake/conversation_topic_branch_mapping/SKILL.v1.md"),
    Path("skills/packs/business-intake/decision_topology_analysis/SKILL.v1.md"),
]


def test_design_and_business_intake_batch_selects_without_identity_collision():
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

    catalog = XRefCatalog.build(repo, skill_definition_paths=PATHS)
    expected = {definition["metadata"]["skill_id"] for definition in definitions}
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in expected}
    assert set(entries) == expected
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())

