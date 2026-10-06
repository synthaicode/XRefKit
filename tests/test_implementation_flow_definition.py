from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("implementation_flow", "D7B4E9A2C610", "0ACF69A599D3", "1832ADA8D6D4"),
    ("python_implementation_flow", "E8C1A7D4B920", "C5D6E7F8A9B1", "C5D6E7F8A9B0"),
    ("test_flow", "F9D2B6E5C130", "62F9F44D7711", "2D7B0A661990"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_flow_definition_parses_with_legacy_aliases_and_skill_method(
    skill_id: str, xid: str, body_xid: str, meta_xid: str
) -> None:
    repo = Path(__file__).resolve().parents[1]
    definition_path = repo / "skills" / skill_id / "SKILL.v1.md"
    definition = load_skill_definition(definition_path)
    metadata = definition["metadata"]

    assert metadata["schema_version"] == 1
    assert metadata["skill_id"] == skill_id
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["inputs"] and metadata["outputs"]
    assert metadata["criteria"]
    assert metadata["control_refs"] == []
    assert definition["method"].strip().startswith("<!-- xid:")
    assert f"xid-{xid}" in definition["method"]
    assert "## Startup" in definition["method"]
    assert "## Closure" in definition["method"]


@pytest.mark.parametrize("case", CASES)
def test_flow_definition_omits_runtime_and_common_control_metadata(case) -> None:
    skill_id = case[0]
    repo = Path(__file__).resolve().parents[1]
    definition = load_skill_definition(repo / "skills" / skill_id / "SKILL.v1.md")
    metadata = definition["metadata"]
    forbidden = {"capability", "tuning", "responsibility", "execution_mode", "model", "maturity"}
    assert forbidden.isdisjoint(metadata)
    assert "## Reporting Contract" not in definition["method"]


def test_flow_definitions_are_explicitly_catalog_selected_and_knowledge_resolves() -> None:
    repo = Path(__file__).resolve().parents[1]
    paths = [Path("skills") / skill_id / "SKILL.v1.md" for skill_id, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    expected = {case[0] for case in CASES}
    selected = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in expected}
    assert set(selected) == expected
    assert all(entry.definition_format == "skill_definition_v1" for entry in selected.values())
    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / "skills" / skill_id / "SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_legacy_files_remain_readable_and_retain_original_xids(
    skill_id: str, xid: str, body_xid: str, meta_xid: str
) -> None:
    repo = Path(__file__).resolve().parents[1]
    body = (repo / "skills" / skill_id / "SKILL.md").read_text(encoding="utf-8")
    meta = (repo / "skills" / skill_id / "meta.md").read_text(encoding="utf-8")
    assert f"xid-{body_xid}" in body
    assert f"xid-{meta_xid}" in meta
    assert f"# Skill: {skill_id}" in body
    assert f"# Skill Meta: {skill_id}" in meta
