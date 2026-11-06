"""Exercise the installed entry point and actual Core resolver, not just import."""
import json
import hashlib
from importlib.metadata import version

import yaml

from xrefkit.discovery import discover_skill_packages
from xrefkit.models import LocalDomainSkill
from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.resolver import EffectiveSkillResolver
from xrefkit.workspace import build_registry


def test_installed_package_resolves_every_skill(tmp_path):
    package = next(p for p in discover_skill_packages() if p.package_id == "xrefkit.skills.csharp")
    assert package.version == version("xrefkit-skills-csharp")
    registry = build_registry(package_manifests=[], discover_entry_points=True,
                              enabled_package_ids={package.package_id})
    for provided in package.manifest.provides.skills:
        base = registry.skills.require(provided.id)
        wrapper = LocalDomainSkill.model_validate({
            "skill_id": "project." + provided.id,
            "xid": "xid-project-" + provided.id.replace(".", "-"),
            "type": "domain_skill_wrapper",
            "xrefkit": {"extends": [{"ref": package.package_id + "::" + provided.id,
                                      "xid": provided.xid, "version": ">=" + package.version,
                                      "mode": "contract_inheritance"}]},
        })
        path = tmp_path / (provided.id + ".yaml")
        path.write_text(yaml.safe_dump(wrapper.model_dump()), encoding="utf-8")
        registry.add_local_skill(skill=wrapper, path=path, root=tmp_path, local_id="project.compatibility")
        bundle = EffectiveSkillResolver(registry).resolve_entry(wrapper.skill_id)
        assert set(base.definition.required_outputs) <= set(bundle.required_outputs)
        assert bundle.source_trace
        assert not bundle.conflicts
        for reference in base.definition.required_knowledge + base.definition.review_axes + base.definition.schemas:
            assert registry.xids.require_asset(reference).path.is_file()
        for asset in [base.definition.entry, *base.definition.required_fragments, *base.definition.branches]:
            assert (package.package_root / asset.path).read_text(encoding="utf-8").strip()
    for path in package.package_root.rglob("*.yaml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))
    for path in package.package_root.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def test_report_contract_survives_package_lookup_and_local_inheritance(tmp_path):
    """A local wrapper cannot silently lose the report or its review resources."""
    package = next(p for p in discover_skill_packages() if p.package_id == "xrefkit.skills.csharp")
    registry = build_registry(package_manifests=[], discover_entry_points=True,
                              enabled_package_ids={package.package_id})
    provided = next(skill for skill in package.manifest.provides.skills if skill.id == "csharp.review")
    base = registry.skills.require(provided.id)
    axis_xid = "xid-axis-csharp-operational-report"
    assert "review_report" in provided.required_outputs
    assert "review_report" in base.definition.required_outputs
    assert axis_xid in provided.required_review_axes
    assert axis_xid in base.definition.review_axes

    axis_asset = registry.xids.require_asset(axis_xid)
    axis = yaml.safe_load(axis_asset.path.read_text(encoding="utf-8"))
    assert axis["xid"] == axis_xid
    assert axis["checks"]
    assert len({check["id"] for check in axis["checks"]}) == len(axis["checks"])
    schema_xid = "xid-schema-csharp-review"
    assert schema_xid in base.definition.schemas
    schema = json.loads(registry.xids.require_asset(schema_xid).path.read_text(encoding="utf-8"))
    assert "review_report" in schema["required"]
    assert schema["properties"]["review_report"]["type"] == "string"
    assert schema["properties"]["review_report"]["minLength"] >= 1
    assert set(base.definition.required_outputs) <= set(schema["required"])

    wrapper = LocalDomainSkill.model_validate({
        "skill_id": "project.report_review",
        "xid": "xid-project-report-review",
        "type": "domain_skill_wrapper",
        "xrefkit": {
            "extends": [{"ref": package.package_id + "::" + provided.id,
                         "xid": provided.xid, "version": ">=" + package.version,
                         "mode": "contract_inheritance"}],
            "required_outputs": ["project_note"],
        },
    })
    path = tmp_path / "report-review.yaml"
    path.write_text(yaml.safe_dump(wrapper.model_dump()), encoding="utf-8")
    registry.add_local_skill(skill=wrapper, path=path, root=tmp_path, local_id="project.compatibility")
    bundle = EffectiveSkillResolver(registry).resolve_entry(wrapper.skill_id)
    assert {"review_report", "project_note"} <= set(bundle.required_outputs)
    assert axis_xid in bundle.references.review_axes
    assert schema_xid in bundle.references.schemas
    assert not bundle.conflicts
    expected_hash = "sha256:" + hashlib.sha256(
        (package.package_root / base.definition.entry.path).read_bytes()
    ).hexdigest()
    assert any(item.xid == base.definition.entry.xid and item.content_hash == expected_hash
               for item in bundle.loaded_texts.all_loaded())


def test_mcp_entry_delivery_includes_every_independent_report_check(tmp_path):
    """Normal get_skill delivery must suffice even without optional axis retrieval."""
    package = next(p for p in discover_skill_packages() if p.package_id == "xrefkit.skills.csharp")
    registry = build_registry(package_manifests=[], discover_entry_points=True,
                              enabled_package_ids={package.package_id})
    base = registry.skills.require("csharp.review")
    expected_entry = (package.package_root / base.definition.entry.path).read_text(encoding="utf-8")
    axis = yaml.safe_load(registry.xids.require_asset("xid-axis-csharp-operational-report").path.read_text(encoding="utf-8"))
    catalog = XRefCatalog.build(tmp_path, discover_packages=True)
    result = catalog.get_skill("csharp.review", {})
    assert result["package_id"] == package.package_id
    delivered = [document["content"] for document in result["documents"]
                 if not document.get("content_omitted")]
    assert expected_entry in delivered
    definition = next(yaml.safe_load(content) for content in delivered
                      if content != expected_entry)
    assert "review_report" in definition["required_outputs"]
    assert axis["xid"] in definition["review_axes"]
    acceptance = expected_entry.split("### Independent acceptance", 1)[1]
    normalized = " ".join(acceptance.split())
    for check in axis["checks"]:
        assert check["id"] in acceptance
        assert " ".join(check["description"].split()) in normalized
