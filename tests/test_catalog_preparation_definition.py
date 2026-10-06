from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("domain_knowledge_catalog_preparation", "skills/os/domain_knowledge_catalog_preparation", "A7C9E2D4F610", "EE95165681E8", "A409BACC6918"),
    ("skill_flow_authoring", "skills/os/skill_flow_authoring", "B8D1A4C7E260", "C1B7A42D8E53", "D37E2B5C8A41"),
    ("test_tool_catalog_preparation", "skills/test_tool_catalog_preparation", "C9E2B5D8F370", "DE815228B04C", "F2A36B52C0EB"),
]


@pytest.mark.parametrize("skill_id,folder,xid,body_xid,meta_xid", CASES)
def test_v1_definitions_parse_with_aliases_and_concrete_metadata(skill_id, folder, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    definition_path = repo / folder / "SKILL.v1.md"
    definition = load_skill_definition(definition_path)
    metadata = definition["metadata"]
    assert metadata["skill_id"] == skill_id
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["inputs"] and metadata["outputs"]
    assert metadata["control_refs"] == []
    assert not any(key in metadata for key in ("capability", "tuning", "responsibility", "execution_mode", "model", "model_tier", "maturity"))
    assert "CAP-" not in definition["method"]
    assert "## Reporting Contract" not in definition["method"]
    assert "## Required Knowledge (XID)" not in definition["method"]
    assert (repo / folder / "SKILL.md").read_text(encoding="utf-8").startswith("<!-- xid: ")
    assert (repo / folder / "meta.md").read_text(encoding="utf-8").startswith("<!-- xid: ")


def test_explicit_catalog_and_knowledge_resolution_cover_the_trio():
    repo = Path(__file__).resolve().parents[1]
    paths = [repo / folder / "SKILL.v1.md" for _, folder, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}}
    assert set(entries) == {case[0] for case in CASES}
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())
    for skill_id, folder, *_ in CASES:
        definition = load_skill_definition(repo / folder / "SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []
