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


def installed_catalog(tmp_path, monkeypatch):
    """Simulate entry-point installation, then use the real package discovery loader."""
    import yaml
    from types import SimpleNamespace
    from xrefkit import discovery
    catalog = package_catalog(tmp_path)
    package = catalog.discovered_packages[0]
    root = package.package_root
    manifest = yaml.safe_load(package.manifest_path.read_text())
    manifest["provides"]["skills"][0]["path"] = "method.skill.yaml"
    manifest["provides"]["skills"][0]["required_knowledge"] = ["xid-knowledge-rules"]
    manifest["provides"]["review_axes"] = [{"id": "axis", "xid": "xid-axis-rules", "path": "axis.yaml"}]
    manifest["provides"]["schemas"] = [{"id": "schema", "xid": "xid-schema-rules", "path": "schema.json"}]
    package.manifest_path.write_text(yaml.safe_dump(manifest))
    (root / "method.skill.yaml").write_text(yaml.safe_dump({
        "skill_id": "example.review", "xid": "xid-skill-example",
        "entry": {"xid": "xid-entry-example", "path": "method.md", "load_policy": "required_inline"},
        "required_outputs": ["report"], "required_knowledge": ["xid-knowledge-rules"],
        "review_axes": ["xid-axis-rules"], "schemas": ["xid-schema-rules"],
        "must_not": [], "extension_policy": {},
    }))
    (root / "axis.yaml").write_text("axis_id: example\nxid: xid-axis-rules\nchecks: []\n")
    (root / "schema.json").write_text('{"type":"object"}\n')
    ep = SimpleNamespace(name="example", load=lambda: lambda: root)
    monkeypatch.setattr(discovery, "_select_entry_points", lambda group: [ep])
    return XRefCatalog.build(catalog.repo_root, discover_packages=True)


def test_discovered_required_knowledge_is_resolved_and_all_declared_assets_are_fetchable(tmp_path, monkeypatch):
    catalog = installed_catalog(tmp_path, monkeypatch)
    skill = catalog.get_skill("example.review")
    assert skill["required_knowledge"] == [{"xid": "xid-knowledge-rules", "required": True, "reason": "package declaration"}]
    resolved = catalog.resolve_skill_knowledge("example.review")
    assert not resolved["unsatisfied_required"]
    assert resolved["slots"][0]["bind"] == "xid-knowledge-rules"
    assert resolved["slots"][0]["required"] is True and resolved["slots"][0]["satisfied"] is True
    for xid in ("xid-knowledge-rules", "xid-axis-rules", "xid-schema-rules", "xid-entry-example", "xid-skill-example"):
        assert catalog.get_document_by_xid(xid)["content"]
    assert catalog.expand_knowledge("xid-knowledge-rules")["content"].startswith("# Package rules")


def test_undeclared_file_is_not_exposed_and_absent_need_remains_unsatisfied(tmp_path, monkeypatch):
    catalog = installed_catalog(tmp_path, monkeypatch)
    package = catalog.discovered_packages[0]
    (package.package_root / "secret.md").write_text("<!-- xid: ABCDEF123456 -->\n# Never declared")
    with pytest.raises(KeyError):
        catalog.get_document_by_xid("ABCDEF123456")
    package.manifest.provides.knowledge.clear()
    resolved = catalog.resolve_skill_knowledge("example.review")
    assert resolved["unsatisfied_required"] == ["xid-knowledge-rules"]
    assert resolved["slots"][0]["candidates"] == []
    with pytest.raises(KeyError):
        catalog.expand_knowledge("xid-knowledge-rules")


def test_live_asset_changes_invalidate_catalog_and_document_cache(tmp_path, monkeypatch):
    catalog = installed_catalog(tmp_path, monkeypatch)
    path = catalog.discovered_packages[0].package_root / "axis.yaml"
    before = catalog.catalog_version
    document = catalog.get_document_by_xid("xid-axis-rules")
    path.write_text(path.read_text() + "summary: revised\n")
    current = catalog.get_document_by_xid("xid-axis-rules", document["content_hash"])
    assert not current["content_omitted"]
    assert current["content_hash"] != document["content_hash"]
    assert catalog.catalog_version != before


def test_duplicate_knowledge_cannot_silently_satisfy_required_slot(tmp_path, monkeypatch):
    catalog = installed_catalog(tmp_path, monkeypatch)
    (catalog.repo_root / "knowledge").mkdir()
    (catalog.repo_root / "knowledge/local.md").write_text("<!-- xid: xid-knowledge-rules -->\n# Conflicting local rules")
    with pytest.raises(ValueError, match="knowledge xid conflict"):
        catalog.resolve_skill_knowledge("example.review")


@pytest.mark.parametrize("relative", ["../outside.md", "/absolute.md", "C:/absolute.md", "knowledge/../rules.md", "knowledge\\rules.md"])
def test_nonportable_or_escaping_declarations_refused(tmp_path, relative):
    catalog = package_catalog(tmp_path, relative)
    with pytest.raises(ValueError, match="package asset escapes root"):
        catalog.get_document_by_xid("xid-knowledge-rules")


def test_symlink_escape_is_not_exposed(tmp_path):
    catalog = package_catalog(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("private outside content")
    inside = catalog.discovered_packages[0].package_root / "knowledge/rules.md"
    inside.unlink()
    try:
        inside.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not available")
    with pytest.raises(ValueError, match="escapes root"):
        catalog.get_document_by_xid("xid-knowledge-rules")


def test_package_cannot_shadow_embedded_startup_identity(tmp_path):
    catalog = package_catalog(tmp_path)
    catalog.discovered_packages[0].manifest.provides.knowledge[0].xid = "0B5C58B5E5B2"
    with pytest.raises(ValueError, match="core startup XID"):
        catalog.get_document_by_xid("0B5C58B5E5B2")


def test_inline_identity_mismatch_refused(tmp_path):
    catalog = package_catalog(tmp_path)
    path = catalog.discovered_packages[0].package_root / "knowledge/rules.md"
    path.write_text("<!-- xid: ABCDEF123456 -->\n# Wrong identity")
    with pytest.raises(ValueError, match="identity does not match"):
        catalog.expand_knowledge("xid-knowledge-rules")


@pytest.mark.parametrize(("declared", "inline", "accepted"), [
    ("xid-7A2F4C8D1401", "7A2F4C8D1401", True),
    ("7A2F4C8D1401", "xid-7A2F4C8D1401", True),
    ("xid-7A2F4C8D1401", "7A2F4C8D1402", False),
    ("xid-knowledge-rules", "knowledge-rules", False),
    ("xid-7A2F4C8D1401-extra", "7A2F4C8D1401", False),
])
def test_native_hex_inline_identity_compatibility(tmp_path, declared, inline, accepted):
    catalog = package_catalog(tmp_path)
    package = catalog.discovered_packages[0]
    package.manifest.provides.knowledge[0].xid = declared
    (package.package_root / "knowledge/rules.md").write_text(f"<!-- xid: {inline} -->\n# Rules")
    if accepted:
        assert catalog.get_document_by_xid(declared)["xid"] == declared
        assert catalog.expand_knowledge(declared)["content"]
    else:
        with pytest.raises(ValueError, match="identity does not match"):
            catalog.get_document_by_xid(declared)


def test_prefixed_native_startup_identity_cannot_shadow_core(tmp_path):
    catalog = package_catalog(tmp_path)
    catalog.discovered_packages[0].manifest.provides.knowledge[0].xid = "xid-0B5C58B5E5B2"
    with pytest.raises(ValueError, match="core startup XID"):
        catalog.get_document_by_xid("xid-0B5C58B5E5B2")


def test_native_seed_resolves_prefixed_package_asset(tmp_path):
    catalog = package_catalog(tmp_path)
    package = catalog.discovered_packages[0]
    package.manifest.provides.knowledge[0].xid = "xid-7A2F4C8D1701"
    bare = catalog.get_document_by_xid("7A2F4C8D1701")
    prefixed = catalog.get_document_by_xid("xid-7A2F4C8D1701")
    assert bare["content_hash"] == prefixed["content_hash"]
    assert bare["content"] == prefixed["content"]

    duplicate = replace(catalog, discovered_packages=(package, package))
    assert duplicate.get_document_by_xid("7A2F4C8D1701")["error"] == "xid_conflict"
