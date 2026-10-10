import shutil
from pathlib import Path

import pytest
import yaml

from xrefkit.cli import main
from xrefkit.reporting import (assess, authorize, bind_collection, evaluate, file_hash, identity,
                              load_registry, qualify, read_json, recalibrate, write_json)
from xrefkit.reporting_profiles import attachment, load_profile, profile_metadata, select_profile


EXAMPLES = Path(__file__).resolve().parents[1] / "knowledge/quality/profiles"


def rewrite_profile(path, change):
    text = path.read_text(encoding="utf-8")
    metadata = profile_metadata(path)
    change(metadata)
    body = text.split("---", 2)[2]
    path.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---" + body, encoding="utf-8")


@pytest.fixture
def profiles(tmp_path):
    for name in ("example_target_a", "example_target_b"):
        shutil.copytree(EXAMPLES / name, tmp_path / name)
    procedure = tmp_path / "SKILL.v1.md"
    procedure.write_text("""---
schema_version: 1
skill_id: example_report
xid: ABCDEF123456
summary: Generate the selected target report
applies_when: [acceptance report requested]
exclusions: [code edits]
inputs: [ordinary task and selected quality Knowledge]
outputs: [acceptance_report]
criteria:
- id: target_quality
  statement: Use the selected applicable quality Knowledge
  verification: Independent reviewer applies the selected profile
knowledge_needs: []
control_refs: []
---
<!-- xid: ABCDEF123456 -->
<a id="xid-ABCDEF123456"></a>
# Example
## Method
Generate using the selected applicable target profile.
""", encoding="utf-8")
    return tmp_path, [tmp_path / name / "profile.md" for name in ("example_target_a", "example_target_b")], procedure


def context(target):
    return {"target_id": target, "skill_id": "example_report", "output_id": "acceptance_report"}


def approved_stub(profile):
    # This acceptance exists only in synthetic unit-test data, never repository examples.
    rewrite_profile(profile, lambda p: p["approval"].update(status="approved", authority="test-only stub owner"))


def collected(profile, procedure, outputs=None):
    target = profile_metadata(profile)["target"]["id"]
    contract, baseline = load_profile(profile, **context(target))
    model = {"provider": "test-only", "snapshot": "exact-test-model", "parameters": {}}
    key = identity(contract, baseline, procedure, model)
    if outputs is None:
        outputs = []
        for index in range(contract["repetitions"]):
            path = profile.parent / f"output-{index}.txt"
            shutil.copyfile(profile.parent / contract["accepted_output"], path)
            outputs.append(path)
    review = {"baseline_hash": baseline, "output_hashes": [file_hash(p) for p in outputs],
              "reviewer": "independent-test-reviewer", "decisions": {c: "pass" for c in contract["subjective"]}}
    evidence = evaluate(contract, baseline, outputs, review, repetitions=contract["repetitions"])
    collection = {"identity": key, "producer": "test-executor", "runs": [
        {"input_hash": file_hash(profile.parent / contract["samples"][0]), "output_hash": file_hash(path),
         "context_id": f"{target}-{index}"} for index, path in enumerate(outputs)]}
    return key, bind_collection(profile, contract, key, evidence, collection), review, collection, outputs, model


def test_same_skill_selects_two_target_formats_and_rejects_cross_target_output(profiles):
    _, paths, _ = profiles
    contracts = []
    for path, target in zip(paths, ("example_target_a", "example_target_b")):
        selection = select_profile(paths, **context(target))
        assert selection["status"] == "selected"
        assert Path(selection["selected"]["path"]) == path
        contract, baseline = load_profile(path, **context(target))
        contracts.append((contract, baseline))
        result = evaluate(contract, baseline, [path.parent / contract["accepted_output"]], repetitions=1)
        assert result["checks"][0]["findings"] == []
        assert result["status"] == "needs_review"  # examples cannot establish acceptance
    a, b = contracts
    assert a[0]["format"]["headings"] != b[0]["format"]["headings"]
    assert evaluate(a[0], a[1], [paths[1].parent / b[0]["accepted_output"]], repetitions=1)["status"] == "alarm"


def test_missing_mismatch_ambiguous_and_explicit_applicable_xid(profiles):
    root, paths, _ = profiles
    assert select_profile(paths, **context("unknown_target"))["status"] == "missing_profile"
    assert select_profile([paths[0]], **context("example_target_b"))["status"] == "profile_mismatch"
    wrong_skill = {**context("example_target_a"), "skill_id": "other_skill"}
    with pytest.raises(ValueError, match="not applicable"):
        load_profile(paths[0], **wrong_skill)
    duplicate = root / "another" / "profile.md"
    shutil.copytree(paths[0].parent, duplicate.parent)
    rewrite_profile(duplicate, lambda p: p.update(xid="C9F4E10683D2", profile_id="alternate_target_a", revision="example-2"))
    text = duplicate.read_text().replace("<!-- xid: A7D2C9E461B0 -->", "<!-- xid: C9F4E10683D2 -->").replace('id="xid-A7D2C9E461B0"', 'id="xid-C9F4E10683D2"')
    duplicate.write_text(text)
    for candidates in ([paths[0], duplicate], [duplicate, paths[0]]):
        assert select_profile(candidates, **context("example_target_a"))["status"] == "ambiguous_profile"
        assert select_profile(candidates, **context("example_target_a"), xid="A7D2C9E461B0")["status"] == "selected"
    assert select_profile(paths, **context("example_target_a"), xid="B8E3D0F572C1")["status"] == "profile_mismatch"
    assert select_profile(paths, **context("example_target_a"), target_revision="different")["status"] == "missing_profile"


def test_target_a_qualification_does_not_qualify_b_and_relocation_preserves_identity(profiles):
    root, paths, procedure = profiles
    for path in paths:
        approved_stub(path)
    a_key, a_evidence, *_ = collected(paths[0], procedure)
    b_key, b_evidence, *_ = collected(paths[1], procedure)
    registry = load_registry(root / "registry.json")
    qualify(registry, a_key, a_evidence)
    assert assess(a_key, registry)["status"] == "qualified"
    assert assess(b_key, registry)["status"] == "assessment_required"
    qualify(registry, b_key, b_evidence)
    assert len(registry["qualifications"]) == 2
    relocated = root / "relocated" / "profile.md"
    shutil.copytree(paths[0].parent, relocated.parent)
    relocated_key, *_ = collected(relocated, procedure)
    assert relocated_key == a_key
    assert assess(relocated_key, registry)["status"] == "qualified"


@pytest.mark.parametrize("asset", ["profile", "approval", "exemplar", "input", "target", "criteria"])
def test_profile_or_acceptance_asset_change_invalidates_qualification(profiles, asset):
    root, paths, procedure = profiles
    profile = paths[0]
    approved_stub(profile)
    key, evidence, *_ = collected(profile, procedure)
    registry = load_registry(root / "registry.json")
    qualify(registry, key, evidence)
    if asset == "profile":
        profile.write_text(profile.read_text() + "\nMore profile explanation.\n")
    elif asset == "target":
        rewrite_profile(profile, lambda p: p["target"].update(revision="changed-target"))
    elif asset == "criteria":
        rewrite_profile(profile, lambda p: p["subjective"].append("new criterion"))
    else:
        filename = {"approval": "provenance.txt", "exemplar": "exemplar.txt", "input": "input.txt"}[asset]
        path = profile.parent / "assets" / filename
        path.write_text(path.read_text() + "\nAdditional information.\n")
    new_key, *_ = collected(profile, procedure)
    assert new_key != key
    assert assess(new_key, registry)["status"] == "assessment_required"


def test_examples_never_qualify_or_authorize_even_after_passing_review(profiles):
    root, paths, procedure = profiles
    key, evidence, *_ = collected(paths[0], procedure)
    assert evidence["checks"][0]["findings"] == []
    assert evidence["status"] == "needs_review"
    assert assess(key, load_registry(root / "registry.json"))["reason"] == "unapproved_profile"
    with pytest.raises(ValueError, match="passing bound evidence"):
        qualify(load_registry(root / "registry.json"), key, evidence)
    with pytest.raises(ValueError, match="example/proposed"):
        authorize(key, "restore quality", 2)


@pytest.mark.parametrize("value", ["../outside.txt", "C:/original/accepted.txt", "/original/accepted.txt", "assets\\accepted.txt"])
def test_profile_attachment_paths_are_portable_and_confined(profiles, value):
    _, paths, _ = profiles
    with pytest.raises(ValueError, match="portable"):
        attachment(paths[0], value)


@pytest.mark.parametrize("mutation", [
    lambda s: s.replace("revision: example-1", "revision: example-1\nrevision: hidden", 1),
    lambda s: s.replace("knowledge_refs: []", "knowledge_refs: &hidden []"),
    lambda s: s.replace("knowledge_refs: []", "knowledge_refs: *hidden"),
    lambda s: s.replace("schema: xrefkit.target_output_quality_profile/v1", "schema: unsupported"),
])
def test_malformed_profile_not_silently_accepted(profiles, mutation):
    _, paths, _ = profiles
    paths[0].write_text(mutation(paths[0].read_text()))
    with pytest.raises((ValueError, yaml.YAMLError)):
        profile_metadata(paths[0])


def test_cli_selection_and_review_receipts_and_protected_profile_assets(profiles):
    root, paths, _ = profiles
    selection = root / "selected.json"
    common = ["--profile", str(paths[0]), "--profile", str(paths[1]), "--target", "example_target_b",
              "--skill-id", "example_report", "--output-id", "acceptance_report"]
    assert main(["skill", "reporting", "select", *common, "--result", str(selection)]) == 0
    assert read_json(selection)["selected"]["xid"] == "B8E3D0F572C1"
    result = root / "check.json"
    output = paths[1].parent / "assets/exemplar.txt"
    assert main(["skill", "reporting", "check", *common, "--output", str(output), "--result", str(result)]) == 1
    assert read_json(result)["checks"][0]["findings"] == []
    assert read_json(result)["quality_source"] == "Knowledge_profile"
    for protected in (paths[0], paths[1].parent / "assets/provenance.txt", output):
        original = protected.read_bytes()
        assert main(["skill", "reporting", "check", *common, "--output", str(output), "--result", str(protected)]) == 2
        assert protected.read_bytes() == original


def test_correction_authorization_bound_to_target_and_profile_baseline(profiles):
    root, paths, procedure = profiles
    for profile in paths:
        approved_stub(profile)
    a_key, _, _, _, _, model = collected(paths[0], procedure)
    request = root / "request.json"
    write_json(request, authorize(a_key, "Restore Target A's approved form", 2))
    candidate = root / "candidate.md"
    candidate.write_text(procedure.read_text() + "\nPreserve selected target headings.\n")
    _, _, review, collection, outputs, _ = collected(paths[1], candidate)
    method_review = {"original_hash": file_hash(procedure), "candidate_hash": file_hash(candidate),
                     "reviewer": "independent-reviewer", "decision": "pass"}
    with pytest.raises(ValueError, match="does not match"):
        recalibrate(paths[1], procedure, model, request, candidate, outputs, root / "registry.json",
                    collection, review, method_review, profile_context=context("example_target_b"))
    _, _, review, collection, outputs, _ = collected(paths[0], candidate)
    original_baseline = paths[0].read_bytes()
    result = recalibrate(paths[0], procedure, model, request, candidate, outputs, root / "registry.json",
                         collection, review, method_review, profile_context=context("example_target_a"))
    assert result["adopted"] and paths[0].read_bytes() == original_baseline
