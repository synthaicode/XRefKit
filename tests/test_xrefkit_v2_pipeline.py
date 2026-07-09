from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from pydantic import TypeAdapter

from xrefkit.cli import main
from xrefkit.loaders import load_local_domain_skill, load_local_manifest, load_package_manifest, load_skill_definition
from xrefkit.mcp_tools import effective_skill_get, skill_resolve_entry, startup_get_contract
from xrefkit.models import RunLogEvent
from xrefkit.registry import XRefKitRegistry
from xrefkit.resolver import EffectiveSkillResolver
from xrefkit.runlog import JsonlRunLogWriter, read_run_log_aggregate
from xrefkit.workspace import build_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_XDDP_PACKAGE_ROOT = REPO_ROOT / "packages" / "xrefkit-skills-xddp-design" / "src" / "xrefkit_skills_xddp_design"
REPO_XDDP_PACKAGE_MANIFEST = REPO_XDDP_PACKAGE_ROOT / "package_manifest.yaml"
REPO_CSHARP_PACKAGE_ROOT = REPO_ROOT / "packages" / "xrefkit-skills-csharp" / "src" / "xrefkit_skills_csharp"
REPO_CSHARP_PACKAGE_MANIFEST = REPO_CSHARP_PACKAGE_ROOT / "package_manifest.yaml"
REPO_SAMPLE_LOCAL_MANIFEST = REPO_ROOT / "samples" / "xrefkit-v2" / "order-system" / "xrefkit.local" / "local_manifest.yaml"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_yaml(path: Path, data: dict) -> None:
    _write(path, yaml.safe_dump(data, sort_keys=False))


def _sample_workspace(root: Path, include_xids: list[str] | None = None) -> tuple[Path, Path]:
    package_root = root / "pkg"
    local_root = root / "xrefkit.local"
    include_xids = include_xids or [
        "xid-include-xddp-traceability-instruction",
        "xid-include-xddp-unknowns-instruction",
        "xid-include-xddp-traceability-instruction",
    ]

    _write(package_root / "skills" / "change_design" / "entry.md", "entry\n")
    _write(package_root / "skills" / "common" / "traceability_instruction.md", "include traceability\n")
    _write(package_root / "skills" / "common" / "unknowns_instruction.md", "include unknowns\n")
    _write(package_root / "skills" / "change_design" / "fragments" / "traceability_required.md", "traceability\n")
    _write(package_root / "skills" / "change_design" / "branches" / "db_schema_change.md", "db branch\n")
    _write(package_root / "knowledge" / "traceability_principles.md", "knowledge\n")

    skill_yaml = {
        "skill_id": "xddp.design.change_design",
        "xid": "xid-skill-xddp-design-change-design",
        "entry": {
            "xid": "xid-entry-xddp-design-change-design",
            "path": "skills/change_design/entry.md",
            "load_policy": "required_inline",
        },
        "required_fragments": [
            {
                "id": "traceability_required",
                "xid": "xid-fragment-xddp-traceability-required",
                "path": "skills/change_design/fragments/traceability_required.md",
                "load_policy": "required_inline",
            }
        ],
        "branches": [
            {
                "id": "db_schema_change",
                "xid": "xid-branch-xddp-design-db-schema-change",
                "path": "skills/change_design/branches/db_schema_change.md",
                "condition": {"any_intent": ["database schema change"]},
                "load_policy": "on_demand",
            }
        ],
        "required_outputs": ["traceability", "unknowns", "used_xids"],
        "required_knowledge": ["xid-xddp-traceability-principles"],
        "extension_policy": {},
    }
    _write_yaml(package_root / "skills" / "change_design.skill.yaml", skill_yaml)

    package_manifest = {
        "package_id": "xrefkit.skills.xddp.design",
        "package_type": "skill_package",
        "version": "1.0.0",
        "requires": {"xrefkit_core": ">=2.0.0 <3.0.0"},
        "provides": {
            "skills": [
                {
                    "id": "xddp.design.change_design",
                    "xid": "xid-skill-xddp-design-change-design",
                    "path": "skills/change_design.skill.yaml",
                    "required_outputs": ["traceability", "unknowns", "used_xids"],
                }
            ],
            "fragments": [
                {
                    "id": "xddp.traceability_instruction",
                    "xid": "xid-include-xddp-traceability-instruction",
                    "path": "skills/common/traceability_instruction.md",
                },
                {
                    "id": "xddp.unknowns_instruction",
                    "xid": "xid-include-xddp-unknowns-instruction",
                    "path": "skills/common/unknowns_instruction.md",
                }
            ],
            "knowledge": [
                {
                    "id": "xddp.traceability_principles",
                    "xid": "xid-xddp-traceability-principles",
                    "path": "knowledge/traceability_principles.md",
                }
            ],
        },
        "contract": {},
    }
    package_manifest_path = package_root / "package_manifest.yaml"
    _write_yaml(package_manifest_path, package_manifest)

    _write(local_root / "knowledge" / "current_spec.md", "current spec\n")
    _write(local_root / "knowledge" / "billing_spec.md", "billing spec\n")
    local_skill = {
        "skill_id": "project.order_change_design",
        "xid": "xid-project-skill-order-change-design",
        "type": "domain_skill_wrapper",
        "xrefkit": {
            "extends": [
                {
                    "ref": "xrefkit.skills.xddp.design::xddp.design.change_design",
                    "xid": "xid-skill-xddp-design-change-design",
                    "version": ">=1.0.0 <2.0.0",
                    "mode": "contract_inheritance",
                }
            ],
            "includes": [{"xid": xid} for xid in include_xids],
            "injects": {"knowledge": ["xid-project-current-spec"]},
            "required_outputs": ["applied_skills"],
        },
    }
    _write_yaml(local_root / "skills" / "order_change_design.skill.yaml", local_skill)

    local_manifest = {
        "local_id": "project.order-system",
        "version": "0.1.0",
        "type": "project_local",
        "requires": {
            "xrefkit_core": ">=2.0.0 <3.0.0",
            "skill_packages": [{"package_id": "xrefkit.skills.xddp.design", "version": ">=1.0.0 <2.0.0"}],
        },
        "mounts": {
            "skills": [{"path": "skills/order_change_design.skill.yaml"}],
            "knowledge": [
                {"id": "project.current_spec", "xid": "xid-project-current-spec", "path": "knowledge/current_spec.md"},
                {"id": "project.billing_spec", "xid": "xid-project-billing-spec", "path": "knowledge/billing_spec.md"},
            ],
        },
        "merge_policy": {},
    }
    local_manifest_path = local_root / "local_manifest.yaml"
    _write_yaml(local_manifest_path, local_manifest)
    return package_manifest_path, local_manifest_path


def test_loaders_read_package_skill_local_and_domain_skill(tmp_path: Path) -> None:
    package_manifest_path, local_manifest_path = _sample_workspace(tmp_path)

    package = load_package_manifest(package_manifest_path)
    skill = load_skill_definition(package_manifest_path.parent / package.provides.skills[0].path)
    local = load_local_manifest(local_manifest_path)
    domain = load_local_domain_skill(local_manifest_path.parent / local.mounts.skills[0].path)

    assert package.package_id == "xrefkit.skills.xddp.design"
    assert skill.skill_id == "xddp.design.change_design"
    assert domain.skill_id == "project.order_change_design"


def test_registry_indexes_packages_skills_knowledge_and_xids(tmp_path: Path) -> None:
    package_manifest_path, local_manifest_path = _sample_workspace(tmp_path)
    local = load_local_manifest(local_manifest_path)

    registry = XRefKitRegistry()
    package = load_package_manifest(package_manifest_path)
    registry.add_package(package, package_manifest_path.parent)
    registry.add_package_skill(
        package_id=package.package_id,
        skill=load_skill_definition(package_manifest_path.parent / package.provides.skills[0].path),
        path=package_manifest_path.parent / package.provides.skills[0].path,
        root=package_manifest_path.parent,
    )
    registry.add_package_knowledge_from_manifest(package, package_manifest_path.parent)
    registry.add_local_manifest_assets(local_manifest_path.parent, local)
    registry.add_local_skill(
        skill=load_local_domain_skill(local_manifest_path.parent / local.mounts.skills[0].path),
        path=local_manifest_path.parent / local.mounts.skills[0].path,
        root=local_manifest_path.parent,
        local_id=local.local_id,
    )

    assert registry.packages.require("xrefkit.skills.xddp.design")
    assert registry.skills.require("xddp.design.change_design")
    assert registry.skills.require("project.order_change_design")
    assert "xid-project-current-spec" in registry.xids
    assert registry.xids.require_asset("xid-skill-xddp-design-change-design").asset_type == "skill"
    assert registry.xids.require_asset("xid-include-xddp-traceability-instruction").asset_type == "fragment"
    assert registry.xids.require_asset("xid-xddp-traceability-principles").asset_type == "knowledge"
    assert len(registry.knowledge.list()) == 3


def test_resolver_builds_entry_effective_skill_bundle(tmp_path: Path) -> None:
    package_manifest_path, local_manifest_path = _sample_workspace(tmp_path)
    registry = build_registry(package_manifests=[package_manifest_path], local_manifest_path=local_manifest_path)

    bundle = EffectiveSkillResolver(registry).resolve_entry("project.order_change_design")

    assert bundle.effective_skill_id == "project.order_change_design"
    assert bundle.resolution_mode == "entry"
    assert "applied_skills" in bundle.required_outputs
    assert "xid-project-current-spec" in bundle.references.knowledge
    assert [entry.xid for entry in bundle.loaded_texts.included] == [
        "xid-include-xddp-traceability-instruction",
        "xid-include-xddp-unknowns-instruction",
    ]
    assert bundle.loaded_texts.included[0].load_reason == "include_fragment"
    included_trace = {entry.xid: entry for entry in bundle.source_trace if entry.xid in {item.xid for item in bundle.loaded_texts.included}}
    assert bundle.loaded_texts.included[0].content_hash == included_trace["xid-include-xddp-traceability-instruction"].content_hash
    assert bundle.loaded_texts.included[1].content_hash == included_trace["xid-include-xddp-unknowns-instruction"].content_hash
    assert any(conflict.code == "include_skipped_duplicate" and conflict.severity == "info" for conflict in bundle.conflicts)
    assert bundle.loaded_texts.branch == []
    assert bundle.loaded_texts.knowledge == []
    available = {entry.xid: entry for entry in bundle.available_domain_knowledge}
    assert set(available) == {
        "xid-xddp-traceability-principles",
        "xid-project-current-spec",
        "xid-project-billing-spec",
    }
    assert available["xid-project-current-spec"].selected is True
    assert available["xid-project-current-spec"].selection_reason == "referenced_by_effective_skill"
    assert available["xid-project-billing-spec"].selected is False
    assert available["xid-project-billing-spec"].local_id == "project.order-system"
    assert {entry.xid for entry in bundle.loaded_texts.all_loaded()} <= {entry.xid for entry in bundle.source_trace}


def test_resolver_rejects_non_fragment_include_xid(tmp_path: Path) -> None:
    package_manifest_path, local_manifest_path = _sample_workspace(
        tmp_path,
        include_xids=["xid-xddp-traceability-principles"],
    )
    registry = build_registry(package_manifests=[package_manifest_path], local_manifest_path=local_manifest_path)

    with pytest.raises(ValueError, match="xid=xid-xddp-traceability-principles.*actual asset_type=knowledge"):
        EffectiveSkillResolver(registry).resolve_entry("project.order_change_design")


def test_resolver_rejects_skill_internal_fragment_include_xid(tmp_path: Path) -> None:
    package_manifest_path, local_manifest_path = _sample_workspace(
        tmp_path,
        include_xids=["xid-fragment-xddp-traceability-required"],
    )
    registry = build_registry(package_manifests=[package_manifest_path], local_manifest_path=local_manifest_path)

    with pytest.raises(ValueError, match="xid=xid-fragment-xddp-traceability-required.*actual asset_type=fragment"):
        EffectiveSkillResolver(registry).resolve_entry("project.order_change_design")


def test_cli_show_effective_skill_tree_and_resolved_json(tmp_path: Path, capsys: object) -> None:
    package_manifest_path, local_manifest_path = _sample_workspace(tmp_path)

    assert main([
        "show",
        "effective-skill",
        "project.order_change_design",
        "--mode",
        "tree",
        "--package-manifest",
        str(package_manifest_path),
        "--local-manifest",
        str(local_manifest_path),
    ]) == 0
    tree_output = capsys.readouterr().out
    assert "effective_skill: project.order_change_design" in tree_output

    assert main([
        "show",
        "effective-skill",
        "project.order_change_design",
        "--mode",
        "resolved-json",
        "--package-manifest",
        str(package_manifest_path),
        "--local-manifest",
        str(local_manifest_path),
    ]) == 0
    resolved_output = capsys.readouterr().out
    assert json.loads(resolved_output)["effective_skill_id"] == "project.order_change_design"


def test_jsonl_run_log_writer_and_aggregate_validator(tmp_path: Path) -> None:
    log_path = tmp_path / "run_log.jsonl"
    writer = JsonlRunLogWriter(log_path)
    events = TypeAdapter(list[RunLogEvent]).validate_python([
        {
            "run_id": "run-1",
            "event_type": "run.start",
            "timestamp": "2026-07-06T22:01:00+09:00",
            "requester": {"type": "client_ip", "client_ip": "192.168.1.25", "identity_assurance": "network_observed"},
            "request": {"operation": "skill.resolve_entry", "skill_id": "project.order_change_design"},
        },
        {
            "run_id": "run-1",
            "event_type": "xids.loaded",
            "timestamp": "2026-07-06T22:01:01+09:00",
            "loaded_xids": [{"xid": "xid-a", "content_hash": "sha256:" + "a" * 64, "load_reason": "skill_entry"}],
        },
        {
            "run_id": "run-1",
            "event_type": "xids.used",
            "timestamp": "2026-07-06T22:01:02+09:00",
            "used_xids": ["xid-a"],
        },
    ])
    for event in events:
        writer.append(event)

    aggregate = read_run_log_aggregate(log_path, "run-1")

    assert aggregate.used_xids <= aggregate.loaded_xids


def test_minimal_mcp_facade_resolves_entry(tmp_path: Path) -> None:
    package_manifest_path, local_manifest_path = _sample_workspace(tmp_path)

    assert startup_get_contract()["mode"] == "xrefkit_v2_mvp"
    resolved = skill_resolve_entry(
        skill_id="project.order_change_design",
        package_manifests=[str(package_manifest_path)],
        local_manifest=str(local_manifest_path),
    )
    effective = effective_skill_get(
        skill_id="project.order_change_design",
        package_manifests=[str(package_manifest_path)],
        local_manifest=str(local_manifest_path),
    )

    assert resolved["effective_skill_id"] == "project.order_change_design"
    assert effective["effective_skill_id"] == "project.order_change_design"


def test_repository_xddp_design_package_resolves_sample_local() -> None:
    registry = build_registry(
        package_manifests=[REPO_XDDP_PACKAGE_MANIFEST],
        local_manifest_path=REPO_SAMPLE_LOCAL_MANIFEST,
    )

    bundle = EffectiveSkillResolver(registry).resolve_entry("project.order_change_design")

    assert bundle.effective_skill_id == "project.order_change_design"
    assert "traceability" in bundle.required_outputs
    assert "unknowns" in bundle.required_outputs
    assert "assumptions" in bundle.required_outputs
    assert "used_xids" in bundle.required_outputs
    assert "change_design" in bundle.required_outputs
    assert "applied_skills" in bundle.required_outputs
    assert "xid-branch-xddp-design-db-schema-change" in bundle.references.branches
    assert "xid-branch-xddp-design-external-interface-change" in bundle.references.branches
    assert "xid-project-order-current-spec" in bundle.references.knowledge
    assert "xid-template-project-order-change-design-report" in bundle.references.templates
    assert [entry.xid for entry in bundle.loaded_texts.included] == ["xid-include-xddp-traceability-instruction"]
    assert any(conflict.code == "include_skipped_duplicate" for conflict in bundle.conflicts)
    assert {entry.xid for entry in bundle.loaded_texts.all_loaded()} <= {entry.xid for entry in bundle.source_trace}


def test_repository_sample_cli_tree_and_resolved_json(capsys: object) -> None:
    assert main([
        "show",
        "effective-skill",
        "project.order_change_design",
        "--mode",
        "tree",
        "--package-manifest",
        str(REPO_XDDP_PACKAGE_MANIFEST),
        "--local-manifest",
        str(REPO_SAMPLE_LOCAL_MANIFEST),
    ]) == 0
    tree_output = capsys.readouterr().out
    assert "effective_skill: project.order_change_design" in tree_output
    assert "xid-entry-xddp-design-change-design" in tree_output
    assert "included:" in tree_output
    assert "xid-include-xddp-traceability-instruction" in tree_output

    assert main([
        "show",
        "effective-skill",
        "project.order_change_design",
        "--mode",
        "resolved-json",
        "--package-manifest",
        str(REPO_XDDP_PACKAGE_MANIFEST),
        "--local-manifest",
        str(REPO_SAMPLE_LOCAL_MANIFEST),
    ]) == 0
    resolved = json.loads(capsys.readouterr().out)
    assert resolved["effective_skill_id"] == "project.order_change_design"
    assert resolved["loaded_texts"]["included"][0]["load_reason"] == "include_fragment"
    assert "used_xids" in resolved["required_outputs"]


def test_repository_csharp_package_loads_all_internal_skill_cuts() -> None:
    registry = build_registry(package_manifests=[REPO_CSHARP_PACKAGE_MANIFEST])

    assert registry.packages.require("xrefkit.skills.csharp")
    assert registry.skills.require("csharp.review")
    assert registry.skills.require("dotnet.change_analysis")
    assert registry.skills.require("csharp.error_policy_extraction")
    assert "xid-knowledge-csharp-review-spec" in registry.xids


def test_repository_csharp_package_resolves_local_csharp_review(tmp_path: Path) -> None:
    local_root = tmp_path / "xrefkit.local"
    _write(local_root / "knowledge" / "current_code_scope.md", "C# review scope\n")
    _write_yaml(local_root / "skills" / "project_csharp_review.skill.yaml", {
        "skill_id": "project.csharp_review",
        "xid": "xid-project-skill-csharp-review",
        "type": "domain_skill_wrapper",
        "xrefkit": {
            "extends": [
                {
                    "ref": "xrefkit.skills.csharp::csharp.review",
                    "xid": "xid-skill-csharp-review",
                    "version": ">=0.1.0 <1.0.0",
                    "mode": "contract_inheritance",
                }
            ],
            "injects": {"knowledge": ["xid-project-csharp-current-code-scope"]},
            "required_outputs": ["applied_skills"],
        },
    })
    local_manifest_path = local_root / "local_manifest.yaml"
    _write_yaml(local_manifest_path, {
        "local_id": "project.csharp-sample",
        "version": "0.1.0",
        "type": "project_local",
        "requires": {
            "xrefkit_core": ">=2.0.0 <3.0.0",
            "skill_packages": [{"package_id": "xrefkit.skills.csharp", "version": ">=0.1.0 <1.0.0"}],
        },
        "mounts": {
            "skills": [{"path": "skills/project_csharp_review.skill.yaml"}],
            "knowledge": [{"id": "project.csharp_current_code_scope", "xid": "xid-project-csharp-current-code-scope", "path": "knowledge/current_code_scope.md"}],
        },
        "merge_policy": {},
    })

    registry = build_registry(package_manifests=[REPO_CSHARP_PACKAGE_MANIFEST], local_manifest_path=local_manifest_path)
    bundle = EffectiveSkillResolver(registry).resolve_entry("project.csharp_review")

    assert bundle.effective_skill_id == "project.csharp_review"
    assert "findings" in bundle.required_outputs
    assert "evidence" in bundle.required_outputs
    assert "unknowns" in bundle.required_outputs
    assert "used_xids" in bundle.required_outputs
    assert "handoffs" in bundle.required_outputs
    assert "applied_skills" in bundle.required_outputs
    assert "xid-branch-csharp-review-async-synchronization" in bundle.references.branches
    assert "xid-project-csharp-current-code-scope" in bundle.references.knowledge
