from pathlib import Path
import subprocess

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("qa_gate_review", "A1B2C3D4E5F6", "09B250B1A8FB", "6655C6BD6238"),
    ("review_report_composition", "B1C2D3E4F5A6", "02E852427ED9", "8F312706C5F0"),
]


def test_qa_report_v1_parse_aliases_boundaries_and_legacy_bytes():
    repo = Path(__file__).resolve().parents[1]
    for skill_id, xid, body_xid, meta_xid in CASES:
        directory = repo / "skills" / skill_id
        definition = load_skill_definition(directory / "SKILL.v1.md")
        metadata = definition["metadata"]
        assert metadata["xid"] == xid
        assert set(metadata["aliases"]) == {body_xid, meta_xid}
        assert metadata["control_refs"] == []
        forbidden = ("capability", "tuning", "responsibility", "execution_mode", "model", "maturity")
        assert not any(key in metadata for key in forbidden)
        assert "## Reporting Contract" not in definition["method"]
        assert "## Required Knowledge (XID)" not in definition["method"]
        for legacy in ("SKILL.md", "meta.md"):
            current = (directory / legacy).read_bytes()
            original = subprocess.run(
                ["git", "show", f"HEAD:skills/{skill_id}/{legacy}"],
                cwd=repo,
                check=True,
                capture_output=True,
            ).stdout
            assert current.replace(b"\r\n", b"\n") == original.replace(b"\r\n", b"\n")


def test_qa_report_v1_explicit_catalog_selection_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [repo / "skills" / skill_id / "SKILL.v1.md" for skill_id, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    ids = {skill_id for skill_id, *_ in CASES}
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in ids}
    assert set(entries) == ids
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())
    for skill_id, *_ in CASES:
        definition = load_skill_definition(repo / "skills" / skill_id / "SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []
