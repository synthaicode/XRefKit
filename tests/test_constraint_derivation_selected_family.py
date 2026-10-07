from repository_skill_receipts import assert_preserved_source_boundary
from repository_skill_receipts import assert_legacy_receipt
from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = [
    ("async_constraint_derivation", "9A4C7E1D2B60", "F6580A1C2346", "F6580A1C2345"),
    ("auth_constraint_derivation", "C8F2A6D1E430", "A7691B2D3457", "A7691B2D3456"),
    ("commonality_derivation", "E7B3C951A2D0", "B87A2C3E4568", "B87A2C3E4567"),
    ("cross_constraint_derivation", "F4A8D2C6B190", "E5812C0D7FB7", "E5812C0D7FB6"),
    ("design_constraint_derivation", "A6D9F3B1C720", "B214C6D8E012", "B214C6D8E011"),
]


@pytest.mark.parametrize("skill_id,xid,body_xid,meta_xid", CASES)
def test_selected_constraint_derivation_v1(skill_id, xid, body_xid, meta_xid):
    repo = Path(__file__).resolve().parents[1]
    relative = Path(f"skills/packs/constraint-derivation/{skill_id}/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    metadata = definition["metadata"]
    assert metadata["xid"] == xid
    expected_aliases = {body_xid, meta_xid}
    if skill_id == "async_constraint_derivation":
        expected_aliases.add("F6580A1C2344")  # Previously published candidate alias.
    assert set(metadata["aliases"]) == expected_aliases
    assert metadata["control_refs"] == ["111D282CA0EA"]
    assert_preserved_source_boundary(definition)
    assert_legacy_receipt(repo / relative.parent / 'meta.md')


def test_selected_constraint_derivation_catalog_and_knowledge_resolution():
    repo = Path(__file__).resolve().parents[1]
    paths = [Path(f"skills/packs/constraint-derivation/{skill}/SKILL.v1.md") for skill, *_ in CASES]
    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    entries = {entry.skill_id: entry for entry in catalog.skills if entry.skill_id in {case[0] for case in CASES}}
    assert set(entries) == {case[0] for case in CASES}
    assert all(entry.definition_format == "skill_definition_v1" for entry in entries.values())
    for skill_id, _, _, _ in CASES:
        definition = load_skill_definition(repo / f"skills/packs/constraint-derivation/{skill_id}/SKILL.v1.md")
        need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
        result = catalog.resolve_skill_knowledge(skill_id, need_ids)
        assert result["unresolved_activation"] == []
        assert result["unsatisfied_required"] == []


def test_async_definition_resolves_actual_legacy_body_identity_after_retirement(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    path = repo / "skills/packs/constraint-derivation/async_constraint_derivation/SKILL.v1.md"
    definition = load_skill_definition(path)
    # A retired split source must resolve through the configured successor.
    successor = tmp_path / "SKILL.v1.md"
    successor.write_bytes(path.read_bytes())
    catalog = XRefCatalog.build(tmp_path, skill_definition_paths=[successor])
    resolved = catalog.get_document_by_xid("F6580A1C2346")
    assert resolved["content_hash"] == definition["content_hash"]
    assert resolved["content"].encode("utf-8") == path.read_bytes()
    assert resolved["xid"] == definition["metadata"]["xid"]
    assert resolved["requested_xid"] == "F6580A1C2346"
    assert resolved["resolved_via"] == "definition_alias"
    cached = catalog.get_document_by_xid("F6580A1C2346", resolved["content_hash"])
    assert cached["cache_status"] == "not_modified"


def test_alias_does_not_replace_present_source_or_hide_conflicts(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    source = repo / "skills/packs/constraint-derivation/async_constraint_derivation"
    successor = tmp_path / "SKILL.v1.md"
    successor.write_bytes((source / "SKILL.v1.md").read_bytes())
    documents = tmp_path / "docs"
    documents.mkdir()
    original = documents / "original.md"
    original.write_bytes(b"<!-- xid: F6580A1C2346 -->\n# External original source\n")
    catalog = XRefCatalog.build(tmp_path, skill_definition_paths=[successor])
    resolved = catalog.get_document_by_xid("F6580A1C2346")
    assert resolved["xid"] == "F6580A1C2346"
    assert "resolved_via" not in resolved
    (documents / "conflicting.md").write_bytes(original.read_bytes())
    conflict = catalog.get_document_by_xid("F6580A1C2346")
    assert conflict["error"] == "xid_conflict"
    assert len(conflict["matches"]) == 2


def test_managed_definition_alias_and_canonical_share_raw_identity(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    source = repo / "skills/packs/constraint-derivation/async_constraint_derivation/SKILL.v1.md"
    directory = tmp_path / "skills" / "async_constraint_derivation"
    directory.mkdir(parents=True)
    successor = directory / "SKILL.v1.md"
    successor.write_bytes(source.read_bytes())
    definition = load_skill_definition(successor)
    catalog = XRefCatalog.build(tmp_path, skill_definition_paths=[successor])
    canonical = catalog.get_document_by_xid(definition["metadata"]["xid"])
    alias = catalog.get_document_by_xid("F6580A1C2346")
    assert canonical["content"].encode("utf-8") == successor.read_bytes()
    assert canonical["content_hash"] == alias["content_hash"] == definition["content_hash"]
    assert canonical["xid"] == alias["xid"]
    cached = catalog.get_document_by_xid(canonical["xid"], alias["content_hash"])
    assert cached["cache_status"] == "not_modified"
