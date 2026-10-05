"""Exercise the installed entry point and actual Core resolver, not just import."""
import json
import subprocess
import sys
from importlib.metadata import version

import yaml

from xrefkit.discovery import discover_skill_packages
from xrefkit.models import LocalDomainSkill
from xrefkit.resolver import EffectiveSkillResolver
from xrefkit.workspace import build_registry


def test_installed_package_resolves_every_skill(tmp_path):
    package = next(p for p in discover_skill_packages() if p.package_id == "xrefkit.skills.batch_regression")
    assert package.version == version("xrefkit-skills-batch-regression")
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


def test_bundled_regression_report(tmp_path):
    from xrefkit_skills_batch_regression import package_root

    assets = package_root() / "skill_assets"
    fixtures = assets / "fixtures"
    output = tmp_path / "report.json"
    subprocess.run([sys.executable, str(assets / "scripts" / "batch_regression.py"),
                    "report", str(fixtures / "config.json"),
                    str(fixtures / "old-results.json"), str(fixtures / "new-results.json"),
                    "--output", str(output)], check=True)
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["all_candidate_count"] == 4
    assert report["summary"]["post_constraint_count"] == 3
    assert report["summary"]["planned_difference"] == 1
    assert report["summary"]["unexplained_difference"] == 1
    assert report["summary"]["baseline_match"] == 1
    assert report["summary"]["human_judgments_required"]
