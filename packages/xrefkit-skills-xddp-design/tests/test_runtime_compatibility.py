"""Regress the installed text-only XDDP Skill through the actual Core runtime.

These checks do not evaluate an AI's change-design judgment. Representative
output fixtures exercise the packaged schema and explicit unknowns, not an LLM.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from importlib.metadata import distribution, version

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError
from packaging.requirements import Requirement
from pydantic import ValidationError as ModelValidationError

from xrefkit.discovery import discover_skill_packages
from xrefkit.models import LocalDomainSkill
from xrefkit.resolver import EffectiveSkillResolver
from xrefkit.workspace import CORE_PROTOCOL_VERSION, build_registry


PACKAGE = "xrefkit.skills.xddp.design"
SKILL = "xddp.design.change_design"
SCHEMA = "xid-schema-xddp-change-design"
INCLUDE = "xid-include-xddp-traceability-instruction"


def installed_package():
    matches = [p for p in discover_skill_packages() if p.package_id == PACKAGE]
    assert len(matches) == 1
    return matches[0]


def local_data(package):
    return {
        "skill_id": "project.xddp.compatibility",
        "xid": "xid-project-xddp-compatibility", "type": "domain_skill_wrapper",
        "xrefkit": {"extends": [{"ref": PACKAGE + "::" + SKILL,
            "xid": package.manifest.provides.skills[0].xid,
            "version": "==" + package.version, "mode": "contract_inheritance"}]},
    }


def resolve(registry, package, tmp_path, data=None):
    local = LocalDomainSkill.model_validate(data or local_data(package))
    path = tmp_path / "local.yaml"
    path.write_text(yaml.safe_dump(local.model_dump()), encoding="utf-8")
    registry.add_local_skill(skill=local, path=path, root=tmp_path,
                             local_id="project.compatibility")
    return EffectiveSkillResolver(registry).resolve_entry(local.skill_id)


def installed_registry():
    return build_registry(package_manifests=[], discover_entry_points=True,
                          enabled_package_ids={PACKAGE})


def copied_package(tmp_path):
    root = tmp_path / "package"
    shutil.copytree(installed_package().package_root, root)
    return root


def rewrite(path, change):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_installed_dependency_identity_and_distinct_protocol():
    dist = distribution("xrefkit-skills-xddp-design")
    package = installed_package()
    entries = [e for e in dist.entry_points if e.group == "xrefkit.skill_packages"]
    assert len(entries) == 1
    assert entries[0].name == package.entry_point_name == "xddp_design"
    assert entries[0].load()().resolve() == package.package_root.resolve()
    assert package.version == dist.version == "0.1.0"
    requirements = [Requirement(r) for r in dist.requires or []]
    core = next(r for r in requirements if r.name == "xrefkit")
    assert version("xrefkit") in core.specifier
    assert "0.6.0" not in core.specifier
    assert "0.7.0" not in core.specifier
    assert "2.0.0" not in core.specifier
    assert CORE_PROTOCOL_VERSION == "2.0.0"
    assert package.manifest.requires.xrefkit_core == ">=2.0.0 <3.0.0"


def test_contract_inheritance_references_and_hashed_sources(tmp_path):
    package = installed_package()
    registry = installed_registry()
    provided = package.manifest.provides.skills[0]
    base = registry.skills.require(SKILL).definition
    data = local_data(package)
    data["xrefkit"]["required_outputs"] = ["design_to_test_handoff"]
    data["xrefkit"]["includes"] = [{"xid": INCLUDE}]
    bundle = resolve(registry, package, tmp_path, data)
    assert bundle.base_contracts == [PACKAGE + "::" + SKILL]
    assert not bundle.conflicts
    assert set(bundle.required_outputs) == set(provided.required_outputs) | {"design_to_test_handoff"}
    assert set(base.must_not) == set(provided.must_not)
    assert set(base.required_outputs) == set(provided.required_outputs)
    assert set(bundle.references.knowledge) == set(provided.required_knowledge)
    assert set(bundle.references.review_axes) == set(provided.required_review_axes)
    assert bundle.references.schemas == [SCHEMA]
    assert [item.xid for item in bundle.loaded_texts.included] == [INCLUDE]
    assert [item.xid for item in bundle.loaded_texts.inherited] == [
        base.entry.xid, *(fragment.xid for fragment in base.required_fragments)]
    assert len(bundle.available_domain_knowledge) == 2
    assert all(item.selected for item in bundle.available_domain_knowledge)
    for trace in bundle.source_trace:
        root = package.package_root if trace.package_id else tmp_path
        assert "sha256:" + hashlib.sha256((root / trace.path).read_bytes()).hexdigest() == trace.content_hash
    for xid in [*bundle.references.knowledge, *bundle.references.review_axes,
                *bundle.references.schemas]:
        asset = registry.xids.require_asset(xid)
        assert asset.path.read_text(encoding="utf-8").strip()
        assert asset.path.resolve().is_relative_to(package.package_root.resolve())


@pytest.mark.parametrize("branch_id,intent", [
    ("db_schema_change", "table column change"),
    ("external_interface_change", "API change"),
])
def test_branches_are_on_demand_and_readable_by_xid(tmp_path, branch_id, intent):
    package = installed_package()
    registry = installed_registry()
    bundle = resolve(registry, package, tmp_path)
    base = registry.skills.require(SKILL).definition
    branch = next(branch for branch in base.branches if branch.id == branch_id)
    assert intent in branch.condition.any_intent
    available = next(item for item in bundle.branches_available if item.id == branch_id)
    assert available.load_policy == "on_demand"
    assert branch.xid in bundle.references.branches
    assert branch.xid not in {entry.xid for entry in bundle.loaded_texts.inherited}
    assert registry.xids.require_asset(branch.xid).path.read_text(encoding="utf-8").strip()


def output_validator():
    registry = installed_registry()
    schema = json.loads(registry.xids.require_asset(SCHEMA).path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def representative_output():
    return {"traceability": [{"item": "Pending to Approved",
        "basis": "current.md: documented status values; request.md: requested transition",
        "impact": "implementation target and external API contract remain unknown"}],
        "unknowns": ["missing external API contract", "missing implementation target"],
        "assumptions": [], "used_xids": [],
        "change_design": "Keep implementation pending until missing source evidence is supplied."}


def test_representative_change_design_and_evaluation_assets_are_packaged():
    package = installed_package()
    output_validator().validate(representative_output())
    root = package.package_root / "evaluation"
    manifest = yaml.safe_load((root / "manifest.yaml").read_text(encoding="utf-8"))
    assert len(manifest["cases"]) == 2
    assert manifest["run_policy"]["expected_answers_are_not_in_target"]
    assert manifest["run_policy"]["calibration_is_not_loaded_by_skill"]
    for case in manifest["cases"]:
        target = (root / case["target"]).resolve()
        expected_path = (root / case["expected"]).resolve()
        calibration_path = (root / case["calibration"]).resolve()
        assert case["skill_id"] == SKILL
        assert not expected_path.is_relative_to(target)
        assert not calibration_path.is_relative_to(target)
        assert len(list(target.glob("*.md"))) == 2
        assert all(path.read_text(encoding="utf-8").strip() for path in target.glob("*.md"))
        assert yaml.safe_load(expected_path.read_text(encoding="utf-8"))["case_id"] == case["id"]
        assert yaml.safe_load(calibration_path.read_text(encoding="utf-8"))["case_id"] == case["id"]
    for path in package.package_root.rglob("*.yaml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))
    for path in package.package_root.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("field", ["traceability", "unknowns", "assumptions", "used_xids", "change_design"])
def test_schema_rejects_missing_required_output(field):
    output = representative_output()
    del output[field]
    with pytest.raises(ValidationError, match="required property"):
        output_validator().validate(output)


def test_schema_rejects_untraced_item_and_wrong_unknown_type():
    validator = output_validator()
    output = representative_output()
    del output["traceability"][0]["basis"]
    with pytest.raises(ValidationError, match="basis"):
        validator.validate(output)
    output = representative_output()
    output["unknowns"] = "unknown evidence"
    with pytest.raises(ValidationError, match="array"):
        validator.validate(output)


def test_cli_discovers_and_resolves_installed_package(tmp_path):
    package = installed_package()
    (tmp_path / "local.yaml").write_text(yaml.safe_dump(local_data(package)), encoding="utf-8")
    manifest = {"local_id": "project.cli", "version": "0.1.0", "type": "project_local",
        "requires": {"xrefkit_core": ">=2.0.0 <3.0.0",
            "skill_packages": [{"package_id": PACKAGE, "version": "==" + package.version}]},
        "mounts": {"skills": [{"path": "local.yaml"}]}, "merge_policy": {}}
    manifest_path = tmp_path / "local_manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    command = [sys.executable, "-I", "-m", "xrefkit"]
    result = subprocess.run([*command, "package", "discover", "--json"],
                            cwd=tmp_path, capture_output=True, text=True, check=True)
    assert any(p["package_id"] == PACKAGE and p["version"] == package.version
               for p in json.loads(result.stdout))
    result = subprocess.run([*command, "show", "effective-skill", "project.xddp.compatibility",
        "--mode", "resolved-json", "--enable-entry-point-discovery", "--enabled-package", PACKAGE,
        "--local-manifest", str(manifest_path)], cwd=tmp_path, capture_output=True, text=True, check=True)
    bundle = json.loads(result.stdout)
    assert bundle["base_contracts"] == [PACKAGE + "::" + SKILL]
    assert set(bundle["required_outputs"]) == set(package.manifest.provides.skills[0].required_outputs)
    assert not bundle["conflicts"]


def test_incompatible_protocol_is_rejected(tmp_path):
    root = copied_package(tmp_path)
    path = root / "package_manifest.yaml"
    rewrite(path, lambda data: data["requires"].update(xrefkit_core=">=3.0.0"))
    with pytest.raises(ValueError, match="current core is 2.0.0"):
        build_registry(package_manifests=[path])


@pytest.mark.parametrize("field,value,error", [
    ("version", ">=1.0.0", "does not satisfy"),
    ("xid", "xid-wrong-base", "XID mismatch"),
    ("ref", "wrong.package::" + SKILL, "package mismatch"),
])
def test_wrong_wrapper_binding_is_rejected(tmp_path, field, value, error):
    package = installed_package()
    data = local_data(package)
    data["xrefkit"]["extends"][0][field] = value
    with pytest.raises(ValueError, match=error):
        resolve(installed_registry(), package, tmp_path, data)


@pytest.mark.parametrize("relative", [
    "skills/change_design/entry.md",
    "skills/change_design/fragments/traceability_required.md",
    "skills/change_design/fragments/unknowns_required.md",
    "knowledge/traceability_principles.md",
])
def test_missing_mandatory_text_fails_real_resolution(tmp_path, relative):
    package = installed_package()
    root = copied_package(tmp_path)
    (root / relative).unlink()
    registry = build_registry(package_manifests=[root / "package_manifest.yaml"])
    with pytest.raises(FileNotFoundError):
        resolve(registry, package, tmp_path)


@pytest.mark.parametrize("mutation,error", [
    ("escape", "escapes root"), ("weaken_outputs", "weaken required outputs"),
    ("override_must_not", "override must_not"), ("unknown_field", "Extra inputs"),
])
def test_invalid_skill_schema_and_extension_policy_are_rejected(tmp_path, mutation, error):
    root = copied_package(tmp_path)
    def change(data):
        if mutation == "escape":
            data["branches"][0]["path"] = "../outside.md"
        elif mutation == "unknown_field":
            data["unsupported_field"] = True
        else:
            key = "local_can_weaken_required_outputs" if mutation == "weaken_outputs" else "local_can_override_must_not"
            data["extension_policy"][key] = True
    rewrite(root / "skills/change_design.skill.yaml", change)
    with pytest.raises(ValueError, match=error):
        build_registry(package_manifests=[root / "package_manifest.yaml"])


def test_knowledge_cannot_be_loaded_as_include_fragment(tmp_path):
    package = installed_package()
    data = local_data(package)
    data["xrefkit"]["includes"] = [{"xid": package.manifest.provides.skills[0].required_knowledge[0]}]
    with pytest.raises(ValueError, match="includes only accepts fragment"):
        resolve(installed_registry(), package, tmp_path, data)


def test_local_cannot_drop_contract_with_unsupported_override():
    data = local_data(installed_package())
    data["xrefkit"]["must_not"] = []
    with pytest.raises(ModelValidationError, match="Extra inputs"):
        LocalDomainSkill.model_validate(data)
