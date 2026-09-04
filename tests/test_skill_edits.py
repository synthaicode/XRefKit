from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog


def _repo(tmp_path: Path) -> Path:
    skill = tmp_path / "skills" / "sample"
    skill.mkdir(parents=True)
    (skill / "meta.md").write_text(
        "# Skill Meta: sample\n"
        "- skill_id: `sample`\n"
        "- summary: sample review\n"
        "- use_when: review sample\n"
        "- skill_doc: `./SKILL.md`\n",
        encoding="utf-8",
    )
    (skill / "SKILL.md").write_text(
        "<!-- xid: SAMPLE-SKILL -->\n# Sample Skill\n\nOriginal procedure.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_prepare_edit_replaces_catalog_content_and_resolves_xid(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    catalog = XRefCatalog.build(root)

    prepared = catalog.prepare_skill_edit("sample")
    assert prepared["created"] is True
    assert prepared["source_kind"] == "repository"
    assert (root / ".xrefkit" / "skill-edits" / "sample" / "SKILL.md").exists()

    overlay = root / prepared["overlay_skill_path"]
    overlay.write_text(
        "<!-- xid: SAMPLE-SKILL -->\n# Sample Skill\n\nUpdated procedure.\n",
        encoding="utf-8",
    )
    selected = catalog.get_skill("sample")
    assert "Updated procedure" in selected["skill_content"]
    assert selected["zone_metadata"]["local_edit"] is True
    document = catalog.get_document_by_xid("SAMPLE-SKILL")
    assert "Updated procedure" in document["content"]


def test_export_and_deactivate_preserve_local_files(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    catalog = XRefCatalog.build(root)
    prepared = catalog.prepare_skill_edit("sample")
    overlay = root / prepared["overlay_skill_path"]
    overlay.write_text(overlay.read_text(encoding="utf-8") + "\nAdded locally.\n", encoding="utf-8")

    exported = catalog.export_skill_edit("sample")
    assert exported["changed"] is True
    assert "Added locally" in exported["patch"]
    deactivated = catalog.deactivate_skill_edit("sample")
    assert deactivated["active"] is False
    assert overlay.exists()
    assert "Original procedure" in catalog.get_skill("sample")["skill_content"]


def test_create_local_knowledge_is_cataloged_and_exportable(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    catalog = XRefCatalog.build(root)
    created = catalog.create_local_knowledge(
        "LOCAL-KNOWLEDGE",
        "<!-- xid: LOCAL-KNOWLEDGE -->\n# Local rule\n\nUse this project rule.\n",
    )
    assert created["created"] is True
    assert "LOCAL-KNOWLEDGE" in [entry["xid"] for entry in catalog.list_knowledge_catalog()]
    resolved = catalog.get_document_by_xid("LOCAL-KNOWLEDGE")
    assert "Use this project rule" in resolved["content"]
    assert "Local rule" in catalog.export_local_knowledge("LOCAL-KNOWLEDGE")["patch"]
    catalog.deactivate_local_knowledge("LOCAL-KNOWLEDGE")
    assert "LOCAL-KNOWLEDGE" not in [entry["xid"] for entry in catalog.list_knowledge_catalog()]
