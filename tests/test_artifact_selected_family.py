from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("xlsx_spec_traceability", "xlsx_spec_traceability", "A7C3E9D2F610", "2D1B6A9E7C40", "5A7C2D4E9130"),
    ("marketing-explainer-video", "marketing_explainer_video", "B8F1A6C4D720", "5E147B19D33D", "A6B923E41178"),
    ("marketing_slide_png", "marketing_slide_png", "C2E7B9F5A130", "91B67D4AC2F3", "5E2C4A90D711"),
    ("import_skill", "import_skill", "D5A8C1E6B740", "7C2A492D2B72", "1DF4555E1B02"),
]


@pytest.mark.parametrize("directory,skill_id,xid,body_xid,meta_xid", CASES)
def test_artifact_v1_parse_concrete_metadata_and_legacy(directory, skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path(f"skills/{directory}/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]
    assert metadata["skill_id"] == skill_id
    assert metadata["xid"] == xid
    assert set(metadata["aliases"]) == {body_xid, meta_xid}
    assert metadata["inputs"] and metadata["outputs"]
    assert metadata["control_refs"] == []
    assert "CAP-" not in definition["method"]
    assert "## Reporting Contract" not in definition["method"]
    assert "skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_text()


def test_artifact_v1_explicit_batch_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path(f"skills/{directory}/SKILL.v1.md") for directory, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    ids = {case[1] for case in CASES}
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in ids}
    assert set(entries) == ids
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())
    for directory, skill_id, *_ in CASES:
        definition = load_skill_definition(repo / f"skills/{directory}/SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []
