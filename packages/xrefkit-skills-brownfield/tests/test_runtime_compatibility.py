"""Exercise the installed Brownfield contract with the actual Core runtime."""
import json
import re
import shutil
from importlib.metadata import metadata, version

import pytest
import yaml
from packaging.requirements import Requirement

from xrefkit.discovery import discover_skill_packages
from xrefkit.models import LocalDomainSkill
from xrefkit.resolver import EffectiveSkillResolver
from xrefkit.workspace import CORE_PROTOCOL_VERSION, build_registry


def installed_package():
    package = next(p for p in discover_skill_packages()
                   if p.package_id == "xrefkit.skills.brownfield")
    assert package.version == version("xrefkit-skills-brownfield")
    return package


def wrapper(package):
    provided = package.manifest.provides.skills[0]
    return LocalDomainSkill.model_validate({
        "skill_id": "project.brownfield.compatibility",
        "xid": "xid-project-brownfield-compatibility",
        "type": "domain_skill_wrapper",
        "xrefkit": {"extends": [{
            "ref": package.package_id + "::" + provided.id,
            "xid": provided.xid, "version": "==" + package.version,
            "mode": "contract_inheritance",
        }]},
    })


def test_installed_distribution_dependency_matches_core():
    requirements = [Requirement(value) for value in
                    metadata("xrefkit-skills-brownfield").get_all("Requires-Dist", [])]
    core = next(req for req in requirements if req.name == "xrefkit")
    assert version("xrefkit") in core.specifier
    assert "0.6.0" not in core.specifier
    assert "0.7.0" not in core.specifier
    assert CORE_PROTOCOL_VERSION == "2.0.0"


def test_installed_workflow_resolves_contract_and_all_required_assets(tmp_path):
    package = installed_package()
    registry = build_registry(package_manifests=[], discover_entry_points=True,
                              enabled_package_ids={package.package_id})
    provided = package.manifest.provides.skills[0]
    base = registry.skills.require(provided.id)
    local = wrapper(package)
    path = tmp_path / "brownfield.yaml"
    path.write_text(yaml.safe_dump(local.model_dump()), encoding="utf-8")
    registry.add_local_skill(skill=local, path=path, root=tmp_path,
                             local_id="project.compatibility")
    bundle = EffectiveSkillResolver(registry).resolve_entry(local.skill_id)
    assert not bundle.conflicts
    assert bundle.source_trace
    assert set(bundle.required_outputs) == set(provided.required_outputs)
    assert set(base.definition.must_not) == set(provided.must_not)
    assert set(bundle.references.knowledge) == set(provided.required_knowledge)
    assert set(bundle.references.review_axes) == set(provided.required_review_axes)
    for xid in [*bundle.references.knowledge, *bundle.references.review_axes,
                *bundle.references.schemas]:
        asset = registry.xids.require_asset(xid)
        text = asset.path.read_text(encoding="utf-8")
        assert text.strip()
        if asset.asset_type == "knowledge":
            assert "<!-- xid: " + xid.removeprefix("xid-") + " -->" in text
    assert len(bundle.available_domain_knowledge) == 6
    assert all(item.selected for item in bundle.available_domain_knowledge)


def test_workflow_entry_references_are_packaged_and_readable():
    package = installed_package()
    entry = package.package_root / "skills/brownfield_workflow/entry.md"
    text = entry.read_text(encoding="utf-8")
    references = re.findall(r"`(references/[^`]+\.md)`", text)
    assert len(references) == 10
    for relative in references:
        path = entry.parent / relative
        assert path.resolve().is_relative_to(package.package_root.resolve())
        assert path.read_text(encoding="utf-8").strip()
    phase_text = (entry.parent / "references/phase-workflow.md").read_text(encoding="utf-8")
    assert "requirements -> planning -> design -> manufacturing ->" in phase_text
    assert "testing" in phase_text
    for path in package.package_root.rglob("*.yaml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))
    for path in package.package_root.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def test_incompatible_protocol_is_rejected(tmp_path):
    package = installed_package()
    root = tmp_path / "package"
    shutil.copytree(package.package_root, root)
    path = root / "package_manifest.yaml"
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    manifest["requires"]["xrefkit_core"] = ">=3.0.0"
    path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="current core is 2.0.0"):
        build_registry(package_manifests=[path])


def test_missing_workflow_entry_fails_resolution(tmp_path):
    package = installed_package()
    root = tmp_path / "package"
    shutil.copytree(package.package_root, root)
    (root / "skills/brownfield_workflow/entry.md").unlink()
    registry = build_registry(package_manifests=[root / "package_manifest.yaml"])
    local = wrapper(package)
    path = tmp_path / "local.yaml"
    path.write_text(yaml.safe_dump(local.model_dump()), encoding="utf-8")
    registry.add_local_skill(skill=local, path=path, root=tmp_path,
                             local_id="project.compatibility")
    with pytest.raises(FileNotFoundError):
        EffectiveSkillResolver(registry).resolve_entry(local.skill_id)


def test_incompatible_local_package_version_is_rejected(tmp_path):
    package = installed_package()
    registry = build_registry(package_manifests=[package.manifest_path])
    local = wrapper(package)
    local.xrefkit.extends[0].version = ">=1.0.0"
    path = tmp_path / "local.yaml"
    path.write_text(yaml.safe_dump(local.model_dump()), encoding="utf-8")
    registry.add_local_skill(skill=local, path=path, root=tmp_path,
                             local_id="project.compatibility")
    with pytest.raises(ValueError, match="does not satisfy"):
        EffectiveSkillResolver(registry).resolve_entry(local.skill_id)
