from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition

CASES = [
    ("doc_ship", "B4E8A1C7D260", "E4B61C9027AF", "9F38C7A15D4E", ["111D282CA0EA"]),
    ("judgment_log", "C6A2E9B4D170", "2A9E4C71D5F2", "E3C8A16D4B02", ["111D282CA0EA"]),
    ("retro", "D7F1A4C9B280", "C17B52E8F4A3", "6E8296A4C2D1", ["111D282CA0EA"]),
    ("skill_calibration_evaluation", "E3B7A1C8D490", "720938921D2C", "6F3A9C2D7B10", []),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid,control_refs", CASES)
def test_os_v1_migration(skill_id, xid, body_xid, meta_xid, control_refs):
    repo = Path(__file__).resolve().parents[1]
    relative = Path("skills/os") / skill_id / "SKILL.v1.md"
    definition = load_skill_definition(repo / relative)
    assert definition["metadata"]["xid"] == xid
    assert set(definition["metadata"]["aliases"]) == {body_xid, meta_xid}
    assert definition["metadata"]["control_refs"] == control_refs
    assert "CAP-" not in definition["method"]
    assert "## Reporting Contract" not in definition["method"]
    assert "Context direction guard" not in definition["method"]
    assert f"<!-- xid: {body_xid} -->".encode() in (repo / relative.parent / "SKILL.md").read_bytes()
    assert b"skill_doc: `./SKILL.md`" in (repo / relative.parent / "meta.md").read_bytes()
    assert definition["metadata"]["inputs"] and definition["metadata"]["outputs"]
    assert definition["metadata"]["applies_when"]


def test_os_v1_explicit_batch_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path("skills/os") / skill / "SKILL.v1.md" for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = [entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}]
    assert len(entries) == len(CASES)
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries)
    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / Path("skills/os") / skill_id / "SKILL.v1.md")
        ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []


def test_artifact_and_os_batch_selects_without_identity_collisions():
    repo = Path(__file__).resolve().parents[1]
    paths = [
        Path("skills/xlsx_spec_traceability/SKILL.v1.md"),
        Path("skills/marketing-explainer-video/SKILL.v1.md"),
        Path("skills/marketing_slide_png/SKILL.v1.md"),
        Path("skills/import_skill/SKILL.v1.md"),
        *[Path("skills/os") / skill / "SKILL.v1.md" for skill, *_ in CASES],
    ]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    expected = {
        "xlsx_spec_traceability", "marketing_explainer_video",
        "marketing_slide_png", "import_skill",
        *[skill for skill, *_ in CASES],
    }
    entries = [entry for entry in catalog.skills if entry.skill_id in expected]
    assert {entry.skill_id for entry in entries} == expected
    assert len({entry.definition_xid for entry in entries}) == len(expected)
