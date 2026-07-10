from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from xrefkit.models import (
    EffectiveSkillBundle,
    LocalDomainSkill,
    PackageManifest,
    RunLogAggregate,
    RunLogEvent,
    SkillDefinition,
)


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def _package_manifest_data() -> dict:
    return {
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
                    "required_outputs": ["traceability", "unknowns"],
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


def _skill_definition_data() -> dict:
    return {
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
        "extension_policy": {},
    }


def _local_domain_skill_data() -> dict:
    return {
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
            "injects": {"knowledge": ["xid-project-current-spec"]},
            "required_outputs": ["applied_skills"],
        },
    }


def _bundle_data() -> dict:
    return {
        "effective_skill_id": "project.order_change_design",
        "resolution_mode": "entry",
        "base_contracts": ["xrefkit.core.startup_contract"],
        "loaded_texts": {
            "core": [
                {
                    "xid": "xid-core-unknown-protocol",
                    "content_hash": HASH_A,
                    "load_reason": "core_contract",
                }
            ],
            "inherited": [
                {
                    "xid": "xid-entry-xddp-design-change-design",
                    "content_hash": HASH_B,
                    "load_reason": "skill_entry",
                }
            ],
        },
        "references": {"knowledge": ["xid-project-current-spec"]},
        "required_outputs": ["traceability", "unknowns", "used_xids"],
        "load_policy_applied": "entry",
        "source_trace": [
            {
                "source_type": "core",
                "xid": "xid-core-unknown-protocol",
                "path": "core/protocols/unknown.md",
                "content_hash": HASH_A,
            },
            {
                "source_type": "package",
                "package_id": "xrefkit.skills.xddp.design",
                "xid": "xid-entry-xddp-design-change-design",
                "path": "skills/change_design/entry.md",
                "content_hash": HASH_B,
            },
        ],
    }


def _run_events_data() -> list[dict]:
    return [
        {
            "run_id": "run-1",
            "event_type": "run.start",
            "timestamp": "2026-07-06T22:01:00+09:00",
            "requester": {
                "type": "client_ip",
                "client_ip": "192.168.1.25",
                "identity_assurance": "network_observed",
            },
            "request": {
                "operation": "skill.resolve_entry",
                "skill_id": "project.order_change_design",
            },
        },
        {
            "run_id": "run-1",
            "event_type": "xids.loaded",
            "timestamp": "2026-07-06T22:01:01+09:00",
            "loaded_xids": [
                {
                    "xid": "xid-core-unknown-protocol",
                    "content_hash": HASH_A,
                    "load_reason": "core_contract",
                }
            ],
        },
        {
            "run_id": "run-1",
            "event_type": "xids.used",
            "timestamp": "2026-07-06T22:01:02+09:00",
            "used_xids": ["xid-core-unknown-protocol"],
        },
    ]


def _run_events(data: list[dict]) -> list[RunLogEvent]:
    return TypeAdapter(list[RunLogEvent]).validate_python(data)


def test_package_manifest_loads() -> None:
    manifest = PackageManifest.model_validate(_package_manifest_data())

    assert manifest.package_id == "xrefkit.skills.xddp.design"


def test_skill_definition_loads() -> None:
    skill = SkillDefinition.model_validate(_skill_definition_data())

    assert skill.entry.load_policy == "required_inline"


def test_local_domain_skill_loads_with_single_extends() -> None:
    skill = LocalDomainSkill.model_validate(_local_domain_skill_data())

    assert len(skill.xrefkit.extends) == 1


def test_effective_skill_bundle_loaded_xids_exist_in_source_trace() -> None:
    bundle = EffectiveSkillBundle.model_validate(_bundle_data())

    loaded = {item.xid for item in bundle.loaded_texts.all_loaded()}
    traced = {item.xid for item in bundle.source_trace}
    assert loaded <= traced


def test_run_log_aggregate_used_xids_subset_of_loaded_xids() -> None:
    aggregate = RunLogAggregate(run_id="run-1", events=_run_events(_run_events_data()))

    assert aggregate.used_xids <= aggregate.loaded_xids


def test_package_manifest_rejects_duplicate_xid() -> None:
    data = _package_manifest_data()
    data["provides"]["knowledge"][0]["xid"] = "xid-skill-xddp-design-change-design"

    with pytest.raises(ValidationError, match="duplicate XIDs"):
        PackageManifest.model_validate(data)


def test_xid_loaded_ref_rejects_invalid_content_hash() -> None:
    data = _bundle_data()
    data["loaded_texts"]["core"][0]["content_hash"] = "sha256:not-hex"

    with pytest.raises(ValidationError, match="content_hash"):
        EffectiveSkillBundle.model_validate(data)


def test_local_domain_skill_rejects_two_extends_entries() -> None:
    data = _local_domain_skill_data()
    data["xrefkit"]["extends"].append(dict(data["xrefkit"]["extends"][0]))

    with pytest.raises(ValidationError, match="exactly one extends"):
        LocalDomainSkill.model_validate(data)


def test_run_log_aggregate_rejects_used_xid_that_was_not_loaded() -> None:
    data = _run_events_data()
    data[2]["used_xids"] = ["xid-not-loaded"]

    with pytest.raises(ValidationError, match="used_xids must be a subset"):
        RunLogAggregate(run_id="run-1", events=_run_events(data))


def test_effective_skill_bundle_rejects_loaded_xid_without_source_trace() -> None:
    data = _bundle_data()
    data["source_trace"] = data["source_trace"][:1]

    with pytest.raises(ValidationError, match="loaded XIDs missing from source_trace"):
        EffectiveSkillBundle.model_validate(data)


def test_source_trace_package_requires_package_id() -> None:
    data = _bundle_data()
    del data["source_trace"][1]["package_id"]

    with pytest.raises(ValidationError, match="package_id"):
        EffectiveSkillBundle.model_validate(data)


def test_source_trace_local_requires_local_id() -> None:
    data = _bundle_data()
    data["source_trace"][1] = {
        "source_type": "local",
        "xid": "xid-entry-xddp-design-change-design",
        "path": "skills/order_change_design.skill.yaml",
        "content_hash": HASH_B,
    }

    with pytest.raises(ValidationError, match="local_id"):
        EffectiveSkillBundle.model_validate(data)
