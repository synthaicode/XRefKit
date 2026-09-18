from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


SKILLS = [
    "implementation_flow",
    "python_implementation_flow",
    "test_flow",
    "csharp_review",
    "python_review",
    "qa_gate_review",
    "review_report_composition",
]


def test_implementation_review_batch_has_unique_identity_and_selects_together():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path("skills") / skill_id / "SKILL.v1.md" for skill_id in SKILLS]
    definitions = [load_skill_definition(repo / path) for path in paths]
    xids = [definition["metadata"]["xid"] for definition in definitions]
    aliases = [
        alias
        for definition in definitions
        for alias in definition["metadata"]["aliases"]
    ]

    assert len(xids) == len(set(xids))
    assert set(xids).isdisjoint(aliases)

    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in SKILLS}
    assert set(entries) == set(SKILLS)
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())

