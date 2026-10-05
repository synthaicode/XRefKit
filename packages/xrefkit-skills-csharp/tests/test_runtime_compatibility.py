"""Exercise the installed entry point and actual Core resolver, not just import."""
import json
from importlib.metadata import version

import yaml

from xrefkit.discovery import discover_skill_packages
from xrefkit.models import LocalDomainSkill
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
