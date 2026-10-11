import copy
import hashlib
import json
from pathlib import Path

import pytest

from test_subagent_startup import command
from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.repository_skills import ADOPTION_PATH, load_repository_adoption
from xrefkit.xref import XrefConfig, build_index


@pytest.fixture
def adopted(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    doc = json.loads((repo / ADOPTION_PATH).read_text(encoding="utf-8"))
    selected = {"python_implementation_flow", "async_constraint_derivation", "db_design", "batch_impact_regression"}
    doc["entries"] = [e for e in doc["entries"] if e["skill_id"] in selected]
    for entry in doc["entries"]:
        target = tmp_path / entry["definition_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((repo / entry["definition_path"]).read_bytes())
    (tmp_path / ADOPTION_PATH).write_text(json.dumps(doc), encoding="utf-8")
    return tmp_path, doc


def test_catalog_defaults_to_one_definition_and_old_id_resolves(adopted):
    root, _ = adopted
    catalog = XRefCatalog.build(root)
    assert len(catalog.skills) == 4


def test_native_v1_source_adoption_requires_explicit_runtime_without_legacy_receipts(adopted):
    root, doc = adopted
    source = next(e for e in doc["entries"] if e["skill_id"] == "python_implementation_flow")
    native = {key: source[key] for key in ("skill_id", "definition_path", "definition_xid", "definition_sha256")}
    native.update(source_kind="native_v1", adopted=True,
                  adoption={"authority": "test human", "date": "2026-10-10", "basis": "Explicit native source registration"})
    doc["entries"] = [native]
    (root / ADOPTION_PATH).write_text(json.dumps(doc))
    parsed = load_repository_adoption(root)["entries"][0]
    assert parsed["legacy_sources"] == []
    assert all(r["value"] is None for r in parsed["runtime"].values())
    catalog = XRefCatalog.build(root)
    assert catalog.get_skill("python_implementation_flow")["maturity"] == "unassessed"
    log = root / "work/native.md"
    args = ("skill", "run", "--root", str(root), "--definition", native["definition_path"],
            "--task", "bounded native implementation", "--out", str(log), "--json")
    code, result = command(*args)
    assert code == 1 and "require --capability" in result
    code, result = command(*args, "--capability", "implementation", "--tuning", "bounded",
                           "--responsibility", "native analysis", "--execution-mode", "subagent_required")
    assert code == 0, result
    text = log.read_text()
    assert '"native_source"' in text and '"legacy_receipt"' not in text
    assert "- maturity: `unassessed`" in text


def test_native_v1_adoption_cannot_hide_legacy_receipts_or_missing_authority(adopted):
    root, doc = adopted
    source = doc["entries"][0]
    native = {key: source[key] for key in ("skill_id", "definition_path", "definition_xid", "definition_sha256")}
    native.update(source_kind="native_v1", adopted=True,
                  adoption={"authority": "", "date": "2026-10-10", "basis": "test"})
    doc["entries"] = [native]
    (root / ADOPTION_PATH).write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="source authority"):
        load_repository_adoption(root)
    native["adoption"]["authority"] = "test human"
    native["legacy_sources"] = []
    (root / ADOPTION_PATH).write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="adoption entry"):
        load_repository_adoption(root)


def test_existing_catalog_readiness_and_aliases_remain_unchanged(adopted):
    root, _ = adopted
    catalog = XRefCatalog.build(root)
    assert all(e.definition_format == "skill_definition_v1" for e in catalog.skills)
    assert catalog.get_skill("batch-impact-regression")["skill_id"] == "batch_impact_regression"
    assert catalog.get_skill("db_design")["maturity"] == "draft"
    assert catalog.get_skill("python_implementation_flow")["maturity"] == "unassessed"
    assert catalog.get_skill("async_constraint_derivation")["capability"] == ""
    ranked = {r["skill_id"]: r for r in catalog.rank_skills_for_purpose("async queues derive confirmations database design", limit=10)}
    assert ranked["async_constraint_derivation"]["execution_readiness"]["required_runtime_inputs"] == ["capability"]
    assert ranked["async_constraint_derivation"]["execution_readiness"]["runnable"] is False
    assert ranked["db_design"]["execution_readiness"]["repository_adopted"] is False
    response = catalog.get_document_by_xid("F6580A1C2346")
    assert response["resolved_via"] == "definition_alias"
    index, issues = build_index(XrefConfig(root=str(root)))
    assert not issues
    assert index["F6580A1C2346"].path == root / catalog.get_skill("async_constraint_derivation")["path"]
    assert index["F6580A1C2346"].content_hash == response["content_hash"]
    # A new split source is a candidate, not implicit repository adoption.
    candidate = root / "skills/unadopted"
    candidate.mkdir()
    (candidate / "meta.md").write_text("- skill_id: `unadopted`\n", encoding="utf-8")
    (candidate / "SKILL.md").write_text("# Candidate\n", encoding="utf-8")
    assert len(catalog.skills) == 4


def test_legacy_invocation_runs_v1_with_audited_explicit_values(adopted):
    root, _ = adopted
    log = root / "work/run.md"
    code, result = command("skill", "run", "--root", str(root),
                           "--meta", "skills/python_implementation_flow/meta.md",
                           "--task", "bounded Python implementation", "--out", str(log), "--json")
    assert code == 0, result
    text = log.read_text(encoding="utf-8")
    assert "- definition_format: `skill_definition_v1`" in text
    assert "- capability: `software_development`" in text
    assert "- responsibility: `implementation`" in text
    assert "- definition_adoption_sha256:" in text
    assert "legacy_declared" in text
    assert "- maturity: `unassessed`" in text


def test_missing_capability_refuses_without_creating_log_then_accepts_explicit_input(adopted):
    root, _ = adopted
    log = root / "work/run.md"
    args = ("skill", "run", "--root", str(root), "--meta",
            "skills/packs/constraint-derivation/async_constraint_derivation/meta.md",
            "--task", "derive async confirmations", "--out", str(log), "--json")
    code, result = command(*args)
    assert code == 1
    assert "require --capability" in result
    assert not log.exists()
    code, result = command(*args, "--capability", "explicit task capability")
    assert code == 0, result
    text = log.read_text(encoding="utf-8")
    assert "explicit_input" in text
    assert "- capability: `explicit task capability`" in text
    assert "- model_tier: `standard`" in text
    assert "- policy: `required`" in text
    assert "independent_quality_subagent_required" in text
    assert "definition_legacy_policy_provenance" in text


@pytest.mark.parametrize("selector,path", [
    ("--meta", "skills/db_design/meta.md"),
    ("--definition", "skills/db_design/SKILL.v1.md"),
])
def test_draft_cannot_bypass_refusal_with_complete_runtime_input(adopted, selector, path):
    root, _ = adopted
    code, result = command("skill", "run", "--root", str(root), selector, path,
                           "--task", "draft attempt", "--capability", "database design",
                           "--out", str(root / "work/run.md"), "--json")
    assert code == 1
    assert "not adopted" in result
    assert not (root / "work/run.md").exists()


@pytest.mark.parametrize("mutation", ["definition", "alias", "provenance", "draft"])
def test_manifest_is_fail_closed_on_revision_identity_or_adoption_drift(adopted, mutation):
    root, original = adopted
    doc = copy.deepcopy(original)
    entry = doc["entries"][0]
    if mutation == "definition":
        path = root / entry["definition_path"]
        path.write_bytes(path.read_bytes() + b"\nChanged method.\n")
    elif mutation == "alias":
        doc["entries"][1]["legacy_ids"] = [entry["skill_id"]]
    elif mutation == "provenance":
        entry["runtime"]["capability"]["source_sha256"] = "0" * 64
    else:
        entry = next(e for e in doc["entries"] if e["legacy_maturity"] == "draft")
        entry["adopted"] = True
    (root / ADOPTION_PATH).write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError):
        load_repository_adoption(root)


def test_real_repository_receipts_cover_all_old_identities():
    repo = Path(__file__).resolve().parents[1]
    doc = load_repository_adoption(repo)
    migrated = [e for e in doc["entries"] if e.get("source_kind") != "native_v1"]
    native = [e for e in doc["entries"] if e.get("source_kind") == "native_v1"]
    assert len(migrated) == 62
    assert sum(not e["adopted"] for e in migrated) == 26
    assert sum(e["adopted"] and e["runtime"]["capability"]["value"] is None for e in migrated) == 28
    assert {e["skill_id"] for e in native} == {
        "shared_asset_update_gate", "correction_retrospective_analyst"
    }
    assert all(e["adopted"] and e["legacy_sources"] == [] for e in native)
    assert all(value["value"] is None for e in native for value in e["runtime"].values())
    assert len(XRefCatalog.build(repo).skills) == len(migrated) + len(native) == 64


def test_removing_adoption_cannot_reuse_cached_retired_aliases(adopted):
    root, _ = adopted
    catalog = XRefCatalog.build(root)
    index, _ = build_index(XrefConfig(root=str(root)))
    assert "F6580A1C2346" in index
    (root / ADOPTION_PATH).unlink()
    with pytest.raises(ValueError, match="adoption record is missing"):
        catalog.get_skill("db_design")
    index, _ = build_index(XrefConfig(root=str(root)))
    assert "F6580A1C2346" not in index


def test_adoption_cache_revalidates_raw_definition_and_does_not_share_mutable_records(adopted):
    root, _ = adopted
    first = load_repository_adoption(root)
    first["entries"][0]["runtime"]["capability"]["value"] = "invented"
    second = load_repository_adoption(root)
    assert second["entries"][0]["runtime"]["capability"]["value"] != "invented"
    path = root / second["entries"][0]["definition_path"]
    path.write_bytes(path.read_bytes() + b"\nChanged bound method.\n")
    with pytest.raises(ValueError, match="revision mismatch"):
        load_repository_adoption(root)


def test_unrelated_live_document_cannot_hijack_an_adopted_retired_alias(adopted):
    root, _ = adopted
    docs = root / "docs"
    docs.mkdir()
    (docs / "foreign.md").write_text("<!-- xid: F6580A1C2346 -->\n# Different source\n", encoding="utf-8")
    response = XRefCatalog.build(root).get_document_by_xid("F6580A1C2346")
    assert response["error"] == "xid_conflict"
    assert len(response["matches"]) == 2
    assert "content" not in response


def test_cached_adoption_rechecks_resolved_definition_containment(adopted, monkeypatch):
    root, _ = adopted
    record = load_repository_adoption(root)
    target = root / record["entries"][0]["definition_path"]
    original_resolve = Path.resolve

    def retargeted(path, *args, **kwargs):
        # Model a directory link retargeted after the first validated load.
        if path == target:
            return root.parent / "outside" / "SKILL.v1.md"
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", retargeted)
    with pytest.raises(ValueError, match="normalized within root"):
        load_repository_adoption(root)


def test_adoption_manifest_is_bounded_before_json_parsing(adopted, monkeypatch):
    root, _ = adopted
    manifest = root / ADOPTION_PATH
    manifest.write_bytes(b" " * 2_000_002)
    original_open = Path.open
    reads = []

    class ObservedReader:
        def __init__(self, reader):
            self.reader = reader

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.reader.__exit__(*args)

        def read(self, size=-1):
            reads.append(size)
            return self.reader.read(size)

    def observed_open(path, *args, **kwargs):
        opened = original_open(path, *args, **kwargs)
        return ObservedReader(opened) if path == manifest else opened

    monkeypatch.setattr(Path, "open", observed_open)
    with pytest.raises(ValueError, match="exceeds byte limit"):
        load_repository_adoption(root)
    assert reads == [2_000_001]


def test_adoption_manifest_rejects_resolved_path_escape(adopted, monkeypatch):
    root, _ = adopted
    manifest = root / ADOPTION_PATH
    original_resolve = Path.resolve

    def retargeted(path, *args, **kwargs):
        if path == manifest:
            return root.parent / "outside" / "repository_adoption.json"
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", retargeted)
    with pytest.raises(ValueError, match="normalized within root"):
        load_repository_adoption(root)


def test_source_specific_semantic_regressions_remain_guarded():
    repo = Path(__file__).resolve().parents[1]
    cases = {
        "brownfield-workflow": ["references/requirements-validation.md", "references/testability-and-case-generation.md", "freshness", "testability"],
        "python_review": ["Create one concrete work item per active review", "actually referenced package version", "`blocked` when any `critical` finding stands"],
        "os/skill_calibration_evaluation": ["held-out", "quarantine", "isolated"],
        "packs/business-intake/conversation_topic_branch_mapping": ["internal planning only"],
        "packs/business-intake/decision_topology_analysis": ["internal planning only"],
        "packs/constraint-derivation/constraint_derivation_index": ["after all primary lists are complete", "Do not run the secondary pass before"],
        "pptx_spec_traceability": ["controls", "semantic unit", "labels"],
    }
    for directory, required in cases.items():
        text = " ".join((repo / "skills" / directory / "SKILL.v1.md").read_text(encoding="utf-8").split())
        for clause in required:
            assert clause in text, (directory, clause)
        assert "they neither relax these obligations nor add different requirements" in text


@pytest.mark.parametrize("policy,value", [("model_tier", []), ("model_tier", "unknown"), ("knowledge_inputs", [3])])
def test_legacy_runtime_policy_rejects_invalid_values(adopted, policy, value):
    root, doc = adopted
    doc["entries"][0]["legacy_runtime_policy"][policy]["value"] = value
    (root / ADOPTION_PATH).write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError, match="legacy"):
        load_repository_adoption(root)


def test_registered_knowledge_input_policy_is_preserved_without_a_catalog(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    doc = json.loads((repo / ADOPTION_PATH).read_text(encoding="utf-8"))
    doc["entries"] = [e for e in doc["entries"] if e["skill_id"] == "source_structure_overview"]
    entry = doc["entries"][0]
    target = tmp_path / entry["definition_path"]
    target.parent.mkdir(parents=True)
    target.write_bytes((repo / entry["definition_path"]).read_bytes())
    (tmp_path / ADOPTION_PATH).write_text(json.dumps(doc), encoding="utf-8")
    log = tmp_path / "work/run.md"
    code, result = command("skill", "run", "--root", str(tmp_path), "--definition", entry["definition_path"],
                           "--task", "prepare local test tool catalog", "--capability", "explicit test tool preparation", "--out", str(log), "--json")
    assert code == 0, result
    text = log.read_text(encoding="utf-8")
    assert "legacy_policy_provenance" in text
    requirements = json.loads(result)["domain_knowledge"]["requirements"]
    assert requirements == [{"name": "target_domain_context", "required": False,
                             "accepts": ["source-structure-overview", "current-source-structure-findings", "module-map", "service-map", "architecture-note"],
                             "purpose": "optional-prior-structure-context"}]


@pytest.fixture
def local_trial(adopted):
    import subprocess
    root, doc = adopted
    entry = next(e for e in doc["entries"] if e["skill_id"] == "db_design")
    basis = root / "observations/trial.md"
    basis.parent.mkdir()
    basis.write_text("# Synthetic tracked trial basis\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "add", "observations/trial.md"], check=True, capture_output=True)
    governance = {
        "schema_version": 1, "skill_id": entry["skill_id"], "definition_xid": entry["definition_xid"],
        "definition_content_hash": entry["definition_sha256"], "maturity": "trial",
        "observation_refs": ["observations/trial.md"], "governance_refs": [],
        "promotion": {"decision": "approved", "target_maturity": "trial", "authority": "synthetic human",
                      "decided_at": "2026-10-10T12:00:00+09:00", "basis_refs": ["observations/trial.md"]},
    }
    path = root / "governance/trial.json"
    path.parent.mkdir()
    path.write_text(json.dumps(governance), encoding="utf-8")
    entry["current_adoption"] = {
        "scope": "repository_local_trial", "governance_path": "governance/trial.json",
        "governance_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "authority": governance["promotion"]["authority"], "decided_at": governance["promotion"]["decided_at"],
        "basis": [{"path": "observations/trial.md", "sha256": hashlib.sha256(basis.read_bytes()).hexdigest()}],
    }
    (root / ADOPTION_PATH).write_text(json.dumps(doc), encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                    "commit", "-qm", "Synthetic trial fixture"], check=True, capture_output=True)
    return root, doc, entry, governance


def trial_command(root, *extra):
    return command("skill", "run", "--root", str(root), "--definition", "skills/db_design/SKILL.v1.md",
                   "--task", "synthetic local trial", "--out", str(root / "work/trial.md"),
                   "--capability", "design", "--tuning", "synthetic", "--responsibility", "bounded design",
                   "--execution-mode", "subagent_required", "--json", *extra)


def test_sealed_local_trial_preserves_history_and_cli_catalog_parity(local_trial):
    root, doc, entry, _ = local_trial
    resolved = load_repository_adoption(root)
    effective = next(e for e in resolved["entries"] if e["skill_id"] == "db_design")
    assert effective["adopted"] is False and effective["legacy_maturity"] == "draft"
    assert effective["effective_adopted"] is True and effective["effective_maturity"] == "trial"
    assert json.loads((root / ADOPTION_PATH).read_text())["entries"] == doc["entries"]
    catalog = XRefCatalog.build(root)
    skill = catalog.get_skill("db_design")
    assert skill["maturity"] == "trial"
    assert skill["maturity_governance"]["record_ref"]["content_hash"] == entry["current_adoption"]["governance_sha256"]
    code, result = trial_command(root)
    assert code == 0, result
    text = (root / "work/trial.md").read_text(encoding="utf-8")
    assert "- maturity: `trial`" in text
    assert "definition_current_adoption_provenance" in text
    assert entry["current_adoption"]["governance_sha256"] in text


@pytest.mark.parametrize("mutation", ["missing_governance", "governance_edit", "basis_edit", "basis_delete", "untracked", "definition_edit"])
def test_warmed_trial_revalidates_all_dependencies(local_trial, mutation):
    import subprocess
    root, _, entry, _ = local_trial
    load_repository_adoption(root)
    catalog = XRefCatalog.build(root)
    if mutation == "missing_governance":
        (root / "governance/trial.json").unlink()
    elif mutation == "governance_edit":
        (root / "governance/trial.json").write_text("{}", encoding="utf-8")
    elif mutation == "basis_edit":
        (root / "observations/trial.md").write_text("Changed", encoding="utf-8")
    elif mutation == "basis_delete":
        (root / "observations/trial.md").unlink()
    elif mutation == "untracked":
        subprocess.run(["git", "-C", str(root), "rm", "--cached", "observations/trial.md"], check=True, capture_output=True)
    else:
        path = root / entry["definition_path"]
        path.write_bytes(path.read_bytes() + b"\nchanged\n")
    with pytest.raises(ValueError):
        load_repository_adoption(root)
    with pytest.raises(ValueError):
        catalog.get_skill("db_design")
    code, _ = trial_command(root)
    assert code == 1 and not (root / "work/trial.md").exists()


@pytest.mark.parametrize("mutation", ["scope", "deprecated", "duplicate_basis", "timezone", "unapproved", "wrong_xid", "wrong_hash", "unsealed_ref", "wrong_authority", "nontrial", "unknown_key"])
def test_invalid_current_trial_is_refused(local_trial, mutation):
    root, doc, entry, governance = local_trial
    current = entry["current_adoption"]
    if mutation == "scope": current["scope"] = "shared"
    elif mutation == "deprecated": entry["legacy_maturity"] = "deprecated"
    elif mutation == "duplicate_basis": current["basis"] *= 2
    elif mutation == "timezone": current["decided_at"] = "2026-10-10T12:00:00"
    elif mutation == "unknown_key": current["extra"] = True
    else:
        if mutation == "unapproved": governance["promotion"]["decision"] = "rejected"
        elif mutation == "wrong_xid": governance["definition_xid"] = "AAAAAAAAAAAA"
        elif mutation == "wrong_hash": governance["definition_content_hash"] = "0" * 64
        elif mutation == "unsealed_ref": governance["observation_refs"] = ["work/unsealed.md"]
        elif mutation == "wrong_authority": governance["promotion"]["authority"] = "other"
        elif mutation == "nontrial": governance["maturity"] = governance["promotion"]["target_maturity"] = "stable"
        path = root / "governance/trial.json"
        path.write_text(json.dumps(governance), encoding="utf-8")
        current["governance_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (root / ADOPTION_PATH).write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError): load_repository_adoption(root)
    code, _ = trial_command(root)
    assert code == 1 and not (root / "work/trial.md").exists()


def test_explicit_other_governance_cannot_override_trial(local_trial):
    import subprocess
    root, _, _, _ = local_trial
    other = root / "governance/other.json"
    other.write_bytes((root / "governance/trial.json").read_bytes())
    subprocess.run(["git", "-C", str(root), "add", "governance/other.json"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                    "commit", "-qm", "Synthetic alternate record"], check=True, capture_output=True)
    code, result = trial_command(root, "--governance", "governance/other.json")
    assert code == 1 and "must match" in result
    assert not (root / "work/trial.md").exists()
    code, result = trial_command(root, "--governance", "governance/trial.json")
    assert code == 0, result


def test_governance_without_current_adoption_does_not_enable_draft(local_trial):
    root, doc, entry, _ = local_trial
    del entry["current_adoption"]
    (root / ADOPTION_PATH).write_text(json.dumps(doc), encoding="utf-8")
    code, result = trial_command(root, "--governance", "governance/trial.json")
    assert code == 1 and "not adopted" in result


@pytest.mark.parametrize("dependency", ["governance/trial.json", "observations/trial.md"])
def test_current_trial_rejects_resolved_dependency_escape(local_trial, monkeypatch, dependency):
    root, _, _, _ = local_trial
    original = Path.resolve
    def resolve(path, *args, **kwargs):
        if path == root / dependency:
            return root.parent / "outside" / path.name
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError, match="normalized within root"):
        load_repository_adoption(root)


def test_current_trial_rejects_duplicate_json_keys(local_trial):
    root, _, _, _ = local_trial
    path = root / ADOPTION_PATH
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace('"scope": "repository_local_trial"',
                                 '"scope": "repository_local_trial", "scope": "repository_local_trial"'), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_repository_adoption(root)


def test_current_trial_tracking_failure_is_controlled(local_trial, monkeypatch):
    import subprocess
    root, _, _, _ = local_trial
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("git", 10)
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(ValueError, match="tracked evidence check unavailable"):
        load_repository_adoption(root)


def test_local_trial_does_not_project_adoption_to_package_entries(local_trial, monkeypatch):
    from dataclasses import replace
    from xrefkit.mcp import catalog as module
    root, _, _, _ = local_trial
    build = module._build_definition_skill_entries
    def package_entries(*args, **kwargs):
        return [replace(entry, package_id="synthetic.distributed.package") for entry in build(*args, **kwargs)]
    monkeypatch.setattr(module, "_build_definition_skill_entries", package_entries)
    skill = next(e for e in XRefCatalog.build(root).skills if e.skill_id == "db_design")
    assert skill.repository_adoption is None
    assert skill.maturity == "unassessed" and skill.maturity_governance is None


def test_current_trial_rechecks_governance_hash_after_loading(local_trial, monkeypatch):
    from xrefkit import repository_skills as module
    root, _, _, _ = local_trial
    load = module.load_governance_record
    def changed(path):
        record = load(path)
        record["_content_hash"] = "0" * 64
        return record
    monkeypatch.setattr(module, "load_governance_record", changed)
    with pytest.raises(ValueError, match="changed during resolution"):
        load_repository_adoption(root)


@pytest.mark.parametrize("operation", ["content", "rank"])
def test_catalog_rechecks_definition_between_adoption_and_projection(local_trial, monkeypatch, operation):
    from xrefkit.mcp import catalog as module
    root, _, entry, _ = local_trial
    catalog = XRefCatalog.build(root)
    build = module._build_definition_skill_entries
    def changed(*args, **kwargs):
        path = root / entry["definition_path"]
        path.write_bytes(path.read_bytes() + b"\nchanged between reads\n")
        return build(*args, **kwargs)
    monkeypatch.setattr(module, "_build_definition_skill_entries", changed)
    with pytest.raises(ValueError, match="revision changed during resolution"):
        if operation == "content":
            catalog.get_skill("db_design")
        else:
            catalog.rank_skills_for_purpose("database design")


def test_tracking_git_never_inherits_protocol_stdin(local_trial, monkeypatch):
    import subprocess
    root, _, _, _ = local_trial
    run = subprocess.run
    observed = []
    def inspect(*args, **kwargs):
        observed.append(kwargs.get("stdin"))
        return run(*args, **kwargs)
    monkeypatch.setattr(subprocess, "run", inspect)
    load_repository_adoption(root)
    assert observed and all(value == subprocess.DEVNULL for value in observed)


@pytest.mark.parametrize("invalid_native", [None, "current_adoption", "date"])
def test_native_and_sealed_legacy_trial_coexist_without_boundary_bypass(local_trial, invalid_native):
    root, doc, trial, _ = local_trial
    source = next(e for e in doc["entries"] if e["skill_id"] != trial["skill_id"])
    native = {key: source[key] for key in ("skill_id", "definition_path", "definition_xid", "definition_sha256")}
    native.update(source_kind="native_v1", adopted=True,
                  adoption={"authority": "test human", "date": "2026-10-10", "basis": "Explicit native source registration"})
    if invalid_native == "current_adoption":
        native["current_adoption"] = copy.deepcopy(trial["current_adoption"])
    elif invalid_native == "date":
        native["adoption"]["date"] = "not-a-date"
    doc["entries"] = [native, trial]
    (root / ADOPTION_PATH).write_text(json.dumps(doc), encoding="utf-8")
    if invalid_native:
        with pytest.raises(ValueError):
            load_repository_adoption(root)
        return
    parsed = load_repository_adoption(root)["entries"]
    assert parsed[0]["legacy_sources"] == []
    assert all(r["value"] is None for r in parsed[0]["runtime"].values())
    assert parsed[1]["effective_adopted"] is True
    assert parsed[1]["effective_maturity"] == "trial"
    assert parsed[1]["legacy_maturity"] == "draft"
    catalog = XRefCatalog.build(root)
    assert catalog.get_skill(native["skill_id"])["maturity"] == "unassessed"
    assert catalog.get_skill(trial["skill_id"])["maturity"] == "trial"
    ranked = catalog.rank_skills_for_purpose("derive Python constraints", limit=10)
    assert any(r["skill_id"] == native["skill_id"] for r in ranked)
    import subprocess
    subprocess.run(["git", "-C", str(root), "add", ADOPTION_PATH], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "Synthetic combined native and trial fixture"], check=True, capture_output=True)
    code, result = command("skill", "run", "--root", str(root), "--definition", native["definition_path"],
                           "--task", "mixed adoption bounded native run", "--out", str(root / "work/native-mixed.md"),
                           "--capability", "implementation", "--tuning", "bounded",
                           "--responsibility", "native analysis", "--execution-mode", "subagent_required", "--json")
    assert code == 0, result
