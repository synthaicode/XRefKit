from pathlib import Path

import yaml

import xrefkit_skills_brownfield


def test_package_root_contains_manifest_and_skill():
    root = xrefkit_skills_brownfield.package_root()
    assert (root / "package_manifest.yaml").is_file()
    assert (root / "skills" / "brownfield_workflow.skill.yaml").is_file()
    assert (root / "skills" / "brownfield_execution_planning.skill.yaml").is_file()
    assert (root / "skills" / "brownfield_pattern_learning.skill.yaml").is_file()


def test_evaluation_manifest_references_existing_cases():
    root = xrefkit_skills_brownfield.package_root()
    manifest = yaml.safe_load((root / "evaluation" / "manifest.yaml").read_text())
    for case in manifest["cases"]:
        assert (root / "evaluation" / case["target"]).is_dir()
        assert (root / "evaluation" / case["expected"]).is_file()
        assert (root / "evaluation" / case["calibration"]).is_file()
