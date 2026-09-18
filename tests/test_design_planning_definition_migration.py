from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("design_flow", "6A4F8C2D1E70", "3D7A91B54210", "1B28D96E4C11"),
    ("planning_flow", "6A4F8C2D1E71", "486C9EEE8A9D", "E3F2F376922F"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_pair_definitions_parse_with_aliases_and_preserve_method(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    definition = load_skill_definition(repo / "skills" / skill_id / "SKILL.v1.md")
    metadata = definition["metadata"]
    assert metadata["schema_version"] == 1
    assert metadata["skill_id"] == skill_id
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["inputs"] and metadata["outputs"] and metadata["criteria"]
    assert metadata["control_refs"] == []
    assert definition["method"].lstrip().startswith("<!-- xid:")
    assert f"xid-{xid}" in definition["method"]
    assert "## Method" in definition["method"]
    assert "## Stop and handoff" in definition["method"]


@pytest.mark.parametrize("case", CASES)
def test_pair_omits_runtime_and_common_control_metadata(case):
    skill_id = case[0]
    repo = Path(__file__).resolve().parents[1]
    definition = load_skill_definition(repo / "skills" / skill_id / "SKILL.v1.md")
    forbidden = {"capability", "tuning", "responsibility", "execution_mode", "model", "maturity"}
    assert forbidden.isdisjoint(definition["metadata"])
    assert "## Reporting Contract" not in definition["method"]


def test_pair_is_explicitly_catalog_selected_and_knowledge_resolves():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path("skills") / skill_id / "SKILL.v1.md" for skill_id, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = [
        entry for entry in catalog.skills
        if entry.skill_id in {"design_flow", "planning_flow"}
    ]
    assert len(entries) == 2
    selected = {entry.skill_id: entry for entry in entries}
    assert set(selected) == {"design_flow", "planning_flow"}
    assert all(entry.definition_format == "skill_definition_v1" for entry in selected.values())
    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / "skills" / skill_id / "SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []


@pytest.mark.parametrize("case", CASES)
def test_legacy_files_remain_readable_and_unchanged_identity(case):
    skill_id = case[0]
    repo = Path(__file__).resolve().parents[1]
    body = (repo / "skills" / skill_id / "SKILL.md").read_text(encoding="utf-8")
    meta = (repo / "skills" / skill_id / "meta.md").read_text(encoding="utf-8")
    expected = next(item for item in CASES if item[0] == skill_id)
    assert f"xid-{expected[2]}" in body
    assert f"xid-{expected[3]}" in meta
    assert f"# Skill: {skill_id}" in body
    assert f"# Skill Meta: {skill_id}" in meta
