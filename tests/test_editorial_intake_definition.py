from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


def test_editorial_intake_v1_aliases_catalog_knowledge_and_legacy_body():
    repo = Path(__file__).resolve().parents[1]
    relative = Path("skills/packs/editorial-ops/editorial_intake/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]
    assert metadata["xid"] == "7C4E9A2D6F81"
    assert set(metadata["aliases"]) == {"77F7D4CB9F99", "54437A84B3D0"}
    assert "capability" not in metadata
    assert "## Context Direction Guard" not in definition["method"]
    assert "## Reporting Contract" not in definition["method"]
    catalog = XRefCatalog.build(repo, skill_definition_paths=[relative])
    entries = [entry for entry in catalog.skills if entry.skill_id == "editorial_intake"]
    assert len(entries) == 1
    assert entries[0].definition_format == "skill_definition_v1"
    need_ids = [need["id"] for need in metadata["knowledge_needs"]]
    resolved = catalog.resolve_skill_knowledge("editorial_intake", need_ids)
    assert resolved["unresolved_activation"] == []
    assert resolved["unsatisfied_required"] == []
    assert all(need["satisfied"] is True for need in resolved["needs"])
    legacy = (repo / "skills/packs/editorial-ops/editorial_intake/SKILL.md").read_text(encoding="utf-8")
    assert "<!-- xid: 77F7D4CB9F99 -->" in legacy
    assert "skill_doc: `./SKILL.md`" in (repo / "skills/packs/editorial-ops/editorial_intake/meta.md").read_text(encoding="utf-8")
