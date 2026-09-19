from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


def test_security_review_v1_migration_and_legacy_body_are_preserved():
    repo = Path(__file__).resolve().parents[1]
    definition_path = Path("skills/security_review/SKILL.v1.md")
    definition = load_skill_definition(repo / definition_path)

    assert definition["metadata"]["xid"] == "7C4E9A2D1F60"
    assert set(definition["metadata"]["aliases"]) == {"3575A687EBCA", "1BCE02850126"}
    assert "CAP-QA-007" not in definition["method"]
    assert "## Required Capability Definitions" not in definition["method"]
    assert "## Required Knowledge (XID)" not in definition["method"]
    assert "## Reporting Contract" not in definition["method"]
    assert [need["id"] for need in definition["metadata"]["knowledge_needs"]] == ["csharp_quality_review_criteria"]

    catalog = XRefCatalog.build(repo, skill_definition_paths=[definition_path])
    entries = [entry for entry in catalog.skills if entry.skill_id == "security_review"]
    assert len(entries) == 1
    assert entries[0].definition_format == "skill_definition_v1"
    assert entries[0].definition_xid == "7C4E9A2D1F60"

    need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
    resolved = catalog.resolve_skill_knowledge("security_review", need_ids)
    assert resolved["unresolved_activation"] == []
    assert resolved["unsatisfied_required"] == []
    assert [need["id"] for need in resolved["needs"]] == need_ids
    assert all(need["satisfied"] is True for need in resolved["needs"])

    legacy = (repo / "skills/security_review/SKILL.md").read_bytes()
    assert legacy.startswith(b"<!-- xid: 3575A687EBCA -->")
    assert b"CAP-QA-007" in legacy
    meta = (repo / "skills/security_review/meta.md").read_text(encoding="utf-8")
    assert "skill_doc: `./SKILL.md`" in meta
