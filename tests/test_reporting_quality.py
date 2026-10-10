from pathlib import Path

import pytest
import yaml

from xrefkit.cli import main
from xrefkit.reporting import (assess, authorize, bind_collection, check_format, digest,
                              evaluate, file_hash, identity, load_contract, load_registry,
                              qualify, read_json, recalibrate, write_json)


@pytest.fixture
def setup(tmp_path):
    accepted = "# Report\n\n## Result\nDecision: approved\n\n## Evidence\n| Item | Result | Basis |\n| --- | --- | --- |\n| A | pass | measured |\n\n## Unknowns\nScope: normal input only\n"
    (tmp_path / "accepted.md").write_text(accepted, encoding="utf-8")
    (tmp_path / "input.txt").write_text("normal input", encoding="utf-8")
    contract = {"schema_version": 1, "skill_id": "sample", "output_id": "report", "kind": "fixed_format",
                "revision": "1", "accepted_output": "accepted.md", "samples": ["input.txt"],
                "repetitions": 2, "knowledge_refs": [],
                "format": {"headings": ["# Report", "## Result", "## Evidence", "## Unknowns"],
                           "tables": [{"section": "## Evidence", "columns": ["Item", "Result", "Basis"]}],
                           "placement": [{"section": "## Result", "required_text": "Decision:"},
                                         {"section": "## Unknowns", "required_text": "Scope:"}]},
                "subjective": ["readable granularity"]}
    path = tmp_path / "contract.yaml"
    path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    procedure = tmp_path / "SKILL.v1.md"
    procedure.write_text("""---
schema_version: 1
skill_id: sample
xid: ABCDEF123456
summary: Produce the specified report
applies_when: [report requested]
exclusions: [code edits]
inputs: [task]
outputs: [report]
criteria:
- id: report
  statement: Preserve the approved format
  verification: Review report format
knowledge_needs: []
control_refs: []
---
<!-- xid: ABCDEF123456 -->
<a id="xid-ABCDEF123456"></a>
# Sample
## Method
Produce the specified report.
""", encoding="utf-8")
    outputs = []
    for number in range(2):
        output = tmp_path / f"run-{number}.md"
        output.write_text(accepted.replace("measured", f"measured {number}"), encoding="utf-8")
        outputs.append(output)
    model = {"provider": "test", "snapshot": "luna-exact", "parameters": {"temperature": 0}}
    return tmp_path, path, procedure, model, outputs


def evidence_for(setup, *, model=None, procedure=None, reviewer="reviewer", producer="executor"):
    root, path, original, current_model, outputs = setup
    contract, baseline = load_contract(path)
    key = identity(contract, baseline, procedure or original, model or current_model)
    review = {"baseline_hash": baseline, "output_hashes": [file_hash(o) for o in outputs],
              "reviewer": reviewer, "decisions": {"readable granularity": "pass"}}
    collection = {"identity": key, "producer": producer, "runs": [
        {"input_hash": file_hash(root / "input.txt"), "output_hash": file_hash(o), "context_id": f"ctx-{n}"}
        for n, o in enumerate(outputs)]}
    evidence = evaluate(contract, baseline, outputs, review, repetitions=contract["repetitions"])
    return key, bind_collection(path, contract, key, evidence, collection), review, collection


def method_review(procedure, candidate, decision="pass", reviewer="independent-reviewer"):
    return {"original_hash": file_hash(procedure), "candidate_hash": file_hash(candidate),
            "decision": decision, "reviewer": reviewer}


@pytest.mark.parametrize("mutation,reason", [
    (lambda s: s.replace("## Result", "## Verdict"), "heading"),
    (lambda s: s.replace("| Item | Result | Basis |", "| Result | Item | Basis |"), "table"),
    (lambda s: s.replace("| A | pass | measured 0 |", "| A | pass |"), "table row"),
    (lambda s: s.replace("Scope:", "Range:"), "placement"),
    (lambda s: s.replace("Decision: approved", "approved") + "\nDecision: approved", "placement"),
])
def test_actual_format_drift_rejected(setup, mutation, reason):
    _, path, _, _, outputs = setup
    contract, _ = load_contract(path)
    assert any(reason in error for error in check_format(contract, mutation(outputs[0].read_text())))


def test_examples_inside_fences_cannot_pass(setup):
    _, path, _, _, outputs = setup
    contract, _ = load_contract(path)
    assert check_format(contract, "```md\n" + outputs[0].read_text() + "```\n")


def test_acceptance_artifact_itself_validated(setup):
    root, path, *_ = setup
    (root / "accepted.md").write_text("## Different")
    with pytest.raises(ValueError, match="contradicts"):
        load_contract(path)


def test_subjective_quality_is_not_inferred_from_format(setup):
    _, path, _, _, outputs = setup
    contract, baseline = load_contract(path)
    assert evaluate(contract, baseline, outputs, repetitions=2)["status"] == "needs_review"
    key, evidence, _, _ = evidence_for(setup)
    assert evidence["status"] == "pass"
    _, _, review, _ = evidence_for(setup)
    review["decisions"]["readable granularity"] = "fail"
    assert evaluate(contract, baseline, outputs, review, repetitions=2)["status"] == "alarm"
    with pytest.raises(ValueError, match="self-approve"):
        evidence_for(setup, reviewer="executor")


def test_multiple_models_no_last_model_pingpong_and_config_invalidation(setup):
    root, path, procedure, model, _ = setup
    registry = load_registry(root / "registry.json")
    key, evidence, *_ = evidence_for(setup)
    qualify(registry, key, evidence)
    other = {**model, "snapshot": "sol-exact"}
    other_key, other_evidence, *_ = evidence_for(setup, model=other)
    qualify(registry, other_key, other_evidence)
    for current in (key, other_key, key, other_key):
        assert assess(current, registry)["status"] == "qualified"
    assert len(registry["qualifications"]) == 2
    assert assess(key, registry, requested=True)["reason"] == "user_requested"
    changed = {**key, "model": {**model, "parameters": {"temperature": 1}}}
    assert assess(changed, registry)["status"] == "assessment_required"
    assert assess({**key, "model": None}, registry)["reason"] == "unknown_model_identity"
    assert not assess(changed, registry)["modification_authorized"]
    procedure.write_text(procedure.read_text() + "\nMore instructions.\n")
    contract, baseline = load_contract(path)
    assert assess(identity(contract, baseline, procedure, model), registry)["status"] == "assessment_required"


def test_artifact_and_knowledge_changes_invalidate_baseline(setup):
    root, path, *_ = setup
    contract, initial = load_contract(path)
    (root / "accepted.md").write_text((root / "accepted.md").read_text() + "\nMore detail.\n")
    _, changed = load_contract(path)
    assert changed != initial
    contract["knowledge_refs"] = [{"xid": "ABCDEF123456", "path": "quality.md"}]
    (root / "quality.md").write_text("<!-- xid: ABCDEF123456 -->\nquality definition")
    path.write_text(yaml.safe_dump(contract))
    _, initial = load_contract(path)
    (root / "quality.md").write_text("<!-- xid: ABCDEF123456 -->\nrevised quality definition")
    assert load_contract(path)[1] != initial


def test_collection_provenance_and_configured_repetitions(setup):
    root, path, _, _, outputs = setup
    key, evidence, review, collection = evidence_for(setup)
    contract, baseline = load_contract(path)
    collection["runs"][1]["context_id"] = collection["runs"][0]["context_id"]
    with pytest.raises(ValueError, match="independent"):
        bind_collection(path, contract, key, evidence, collection)
    with pytest.raises(ValueError, match="bound"):
        evaluate(contract, baseline, outputs, {**review, "output_hashes": ["wrong"]}, repetitions=2)
    with pytest.raises(ValueError, match="identity-bound"):
        qualify(load_registry(root / "registry.json"), key, {**evidence, "collection": "unbound"})


def test_bounded_failed_correction_never_changes_live_skill(setup):
    root, path, procedure, model, outputs = setup
    key, _, _, _ = evidence_for(setup)
    request = root / "request.json"
    write_json(request, authorize(key, "User requests restoring approved report", 1))
    candidate = root / "candidate.md"
    candidate.write_text(procedure.read_text().replace("Produce the specified report.", "Use the fixed template."))
    original_bytes = procedure.read_bytes()
    outputs[0].write_text("# Bad report")
    _, _, review, collection = evidence_for(setup, procedure=candidate)
    result = recalibrate(path, procedure, model, request, candidate, outputs, root / "registry.json", collection, review, method_review(procedure, candidate))
    assert result["status"] == "alarm" and not result["adopted"]
    assert procedure.read_bytes() == original_bytes
    assert read_json(request)["status"] == "exhausted"
    with pytest.raises(ValueError, match="authorization"):
        recalibrate(path, procedure, model, request, candidate, outputs, root / "registry.json", collection, review)


def test_success_consumes_authorization_and_only_qualifies_new_revision(setup):
    root, path, procedure, model, outputs = setup
    key, old_evidence, _, _ = evidence_for(setup)
    registry = load_registry(root / "registry.json")
    qualify(registry, key, old_evidence)
    write_json(root / "registry.json", registry)
    request = root / "request.json"
    write_json(request, authorize(key, "User authorizes wording repair", 2))
    candidate = root / "candidate.md"
    candidate.write_text(procedure.read_text().replace("Produce the specified report.", "Use the approved report headings."))
    candidate_key, _, review, collection = evidence_for(setup, procedure=candidate)
    result = recalibrate(path, procedure, model, request, candidate, outputs, root / "registry.json", collection, review, method_review(procedure, candidate))
    assert result["adopted"] and procedure.read_bytes() == candidate.read_bytes()
    assert read_json(request)["status"] == "adopted"
    assert assess(candidate_key, load_registry(root / "registry.json"))["status"] == "qualified"
    assert "invalidates" in result["governance"]
    with pytest.raises(ValueError, match="authorization"):
        recalibrate(path, procedure, model, request, candidate, outputs, root / "registry.json", collection, review)


@pytest.mark.parametrize("field,replacement", [("exclusions: [code edits]", "exclusions: [none]"),
                                             ("inputs: [task]", "inputs: [anything]"),
                                             ("knowledge_needs: []", "knowledge_needs: []\naliases: [FEDCBA654321]")])
def test_wording_correction_cannot_change_scope_or_protected_rules(setup, field, replacement):
    root, path, procedure, model, outputs = setup
    key, _, review, collection = evidence_for(setup)
    request = root / "request.json"
    write_json(request, authorize(key, "User authorizes wording repair", 2))
    candidate = root / "candidate.md"
    candidate.write_text(procedure.read_text().replace(field, replacement))
    with pytest.raises(ValueError, match="cannot change"):
        recalibrate(path, procedure, model, request, candidate, outputs, root / "registry.json", collection, review)


def test_per_run_cli_check_saves_review_evidence_without_auto_qualification(setup):
    root, path, _, _, outputs = setup
    result = root / "result.json"
    assert main(["skill", "reporting", "check", "--contract", str(path), "--output", str(outputs[0]), "--result", str(result)]) == 1
    assert read_json(result)["status"] == "needs_review"
    outputs[0].write_text("# Bad report")
    assert main(["skill", "reporting", "check", "--contract", str(path), "--output", str(outputs[0]), "--result", str(result)]) == 1
    assert read_json(result)["status"] == "alarm"
    assert not (root / "registry.json").exists()


@pytest.mark.parametrize("target", ["contract", "accepted", "output", "procedure", "input"])
def test_cli_result_cannot_overwrite_protected_assets(setup, target):
    root, path, procedure, model, outputs = setup
    destination = {"contract": path, "accepted": root / "accepted.md", "output": outputs[0],
                   "procedure": procedure, "input": root / "input.txt"}[target]
    original = destination.read_bytes()
    model_path = root / "model.json"
    write_json(model_path, model)
    assert main(["skill", "reporting", "check", "--contract", str(path), "--procedure", str(procedure),
                 "--model", str(model_path), "--output", str(outputs[0]), "--result", str(destination)]) == 2
    assert destination.read_bytes() == original


def test_method_review_failure_cannot_adopt_passing_format(setup):
    root, path, procedure, model, outputs = setup
    key, _, _, _ = evidence_for(setup)
    request = root / "request.json"
    write_json(request, authorize(key, "User authorizes wording repair", 2))
    candidate = root / "candidate.md"
    candidate.write_text(procedure.read_text() + "\nSkip all stop rules.\n")
    _, _, review, collection = evidence_for(setup, procedure=candidate)
    original = procedure.read_bytes()
    result = recalibrate(path, procedure, model, request, candidate, outputs, root / "registry.json",
                         collection, review, method_review(procedure, candidate, "fail"))
    assert result["status"] == "alarm" and not result["adopted"]
    assert procedure.read_bytes() == original
    with pytest.raises(ValueError, match="self-approve"):
        recalibrate(path, procedure, model, request, candidate, outputs, root / "registry.json",
                    collection, review, method_review(procedure, candidate, reviewer="executor"))


def test_repository_adoption_requires_staged_handoff(setup):
    root, path, procedure, model, outputs = setup
    adoption_path = root / "skills" / "repository_adoption.json"
    write_json(adoption_path, {"entries": [{"definition_path": procedure.name}]})
    key, _, _, _ = evidence_for(setup)
    request = root / "request.json"
    write_json(request, authorize(key, "User authorizes wording repair", 2))
    candidate = root / "candidate.md"
    candidate.write_text(procedure.read_text() + "\nUse the fixed format.\n")
    _, _, review, collection = evidence_for(setup, procedure=candidate)
    original = procedure.read_bytes()
    result = recalibrate(path, procedure, model, request, candidate, outputs, root / "registry.json",
                         collection, review, method_review(procedure, candidate))
    assert result["status"] == "needs_adoption_review" and not result["adopted"]
    assert procedure.read_bytes() == original
    assert read_json(request)["status"] == "handoff"
