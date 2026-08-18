from pathlib import Path

import yaml

import xrefkit_skills_brownfield


def test_package_root_contains_manifest_and_skill():
    root = xrefkit_skills_brownfield.package_root()
    assert (root / "package_manifest.yaml").is_file()
    assert (root / "skills" / "brownfield_workflow.skill.yaml").is_file()


def test_evaluation_manifest_references_existing_cases():
    root = xrefkit_skills_brownfield.package_root()
    manifest = yaml.safe_load((root / "evaluation" / "manifest.yaml").read_text())
    for case in manifest["cases"]:
        assert (root / "evaluation" / case["target"]).is_dir()
        assert (root / "evaluation" / case["expected"]).is_file()
        assert (root / "evaluation" / case["calibration"]).is_file()


def test_testability_gate_is_packaged_and_required():
    root = xrefkit_skills_brownfield.package_root()
    reference = root / "skills" / "brownfield_workflow" / "references" / "testability-and-case-generation.md"
    skill_contract = yaml.safe_load(
        (root / "skills" / "brownfield_workflow.skill.yaml").read_text()
    )
    manifest = yaml.safe_load((root / "package_manifest.yaml").read_text())

    assert reference.is_file()
    assert "do not invent" in reference.read_text().lower()
    assert "test_case_candidates" in skill_contract["required_outputs"]
    assert "test_definition_gaps" in skill_contract["required_outputs"]
    assert "requirement_validation" in skill_contract["required_outputs"]
    assert "specification_reconciliation" in skill_contract["required_outputs"]
    assert "protected_invariants" in skill_contract["required_outputs"]
    assert "post_reconciliation_detail_plan" in skill_contract["required_outputs"]
    provided = manifest["provides"]["skills"][0]
    assert "testability_gate" in provided["required_outputs"]
    assert "requirement_validation" in provided["required_outputs"]
    assert "specification_reconciliation" in provided["required_outputs"]
    assert "generate_test_case_from_undefined_expectation" in provided["must_not"]
