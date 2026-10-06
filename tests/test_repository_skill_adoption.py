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
    assert len(doc["entries"]) == 62
    assert sum(not e["adopted"] for e in doc["entries"]) == 26
    assert sum(e["adopted"] and e["runtime"]["capability"]["value"] is None for e in doc["entries"]) == 28
    assert len(XRefCatalog.build(repo).skills) == 62


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
