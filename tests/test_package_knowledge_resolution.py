from dataclasses import replace

import pytest

from xrefkit.discovery import DiscoveredSkillPackage
from xrefkit.loaders import load_package_manifest
from xrefkit.mcp.catalog import XRefCatalog


def package_catalog(tmp_path, asset_path="knowledge/rules.md"):
    import yaml
    package_root = tmp_path / "package"
    package_root.mkdir()
    (package_root / "knowledge").mkdir()
    (package_root / "knowledge/rules.md").write_text("# Package rules\n\nRequired rules.\n")
    (package_root / "method.md").write_text("# Method\n")
    manifest = package_root / "package_manifest.yaml"
    manifest.write_text(yaml.safe_dump({
        "package_id": "example.rules", "package_type": "skill_package", "version": "1.0.0",
        "requires": {"xrefkit_core": ">=2.0.0 <3.0.0"},
        "provides": {
            "skills": [{"id": "example.review", "xid": "xid-skill-example", "path": "method.md"}],
            "knowledge": [{"id": "rules", "xid": "xid-knowledge-rules", "path": asset_path}],
        },
        "contract": {},
    }))
    package = DiscoveredSkillPackage("example", package_root, manifest, load_package_manifest(manifest))
    repo = tmp_path / "repo"
    repo.mkdir()
    return replace(XRefCatalog.build(repo), discovered_packages=(package,))


def test_manifest_identity_resolves_without_inline_xid(tmp_path):
    catalog = package_catalog(tmp_path)
    document = catalog.get_document_by_xid("xid-knowledge-rules")
    assert document["content"] == catalog.expand_knowledge("xid-knowledge-rules")["content"]
    assert document["xid"] == "xid-knowledge-rules"
    assert catalog.search_knowledge_catalog("Required rules")[0]["xid"] == "xid-knowledge-rules"
    cached = catalog.get_document_by_xid("xid-knowledge-rules", document["content_hash"])
    assert cached["content_hash"] == document["content_hash"]
    assert cached["content_omitted"] == document["cache_policy"]["cache_recommended"]


def test_duplicate_package_xid_refuses_selection(tmp_path):
    catalog = package_catalog(tmp_path)
    catalog = replace(catalog, discovered_packages=catalog.discovered_packages * 2)
    assert catalog.get_document_by_xid("xid-knowledge-rules")["error"] == "xid_conflict"
    with pytest.raises(ValueError, match="knowledge xid conflict"):
        catalog.expand_knowledge("xid-knowledge-rules")


def test_package_path_cannot_escape_root(tmp_path):
    catalog = package_catalog(tmp_path, "../outside.md")
    with pytest.raises(ValueError, match="escapes root"):
        catalog.get_document_by_xid("xid-knowledge-rules")
