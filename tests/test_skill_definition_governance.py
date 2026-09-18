import copy
import hashlib
import json

import pytest

from test_skill_definition import metadata, text_for
from test_subagent_startup import command
from xrefkit.skill_definition_catalog import build_definition_catalog
from xrefkit.skill_definition_governance import load_governance_record


def _write_definition(tmp_path, metadata):
    path = tmp_path / "SKILL.md"
    path.write_text(text_for(metadata), encoding="utf-8")
    return path


def _record(definition, metadata, *, maturity="stable", decision="approved"):
    target = maturity if decision == "approved" else "governed" if decision == "rejected" else None
    decided = decision != "not_requested"
    return {
        "schema_version": 1,
        "skill_id": metadata["skill_id"],
        "definition_xid": metadata["xid"],
        "definition_content_hash": hashlib.sha256(definition.read_bytes()).hexdigest(),
        "maturity": maturity,
        "observation_refs": ["observations/run.md"] if maturity in {"trial", "stable", "governed"} else [],
        "governance_refs": ["docs/policy.md#xid-123456ABCDEF"] if maturity == "governed" else [],
        "promotion": {
            "decision": decision,
            "target_maturity": target,
            "authority": "human:owner" if decided else None,
            "decided_at": "2026-09-18T12:00:00+09:00" if decided else None,
            "basis_refs": ["observations/run.md"] if decided else [],
        },
    }


def _write_record(tmp_path, value, name="governance.json"):
    path = tmp_path / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_governance_binds_exact_definition_and_projects_maturity(metadata, tmp_path):
    definition = _write_definition(tmp_path, metadata)
    record_path = _write_record(tmp_path, _record(definition, metadata))
    raw_hash = hashlib.sha256(record_path.read_bytes()).hexdigest()

    catalog = build_definition_catalog([definition], [record_path])
    entry = catalog["entries"][0]
    assert entry["maturity"] == "stable"
    assert entry["governance"]["record_ref"]["content_hash"] == raw_hash
    assert entry["governance"]["promotion"]["authority"] == "human:owner"
    assert "SECRET_METHOD_SENTINEL" not in json.dumps(catalog)


def test_missing_governance_is_unassessed(metadata, tmp_path):
    definition = _write_definition(tmp_path, metadata)
    entry = build_definition_catalog([definition])["entries"][0]
    assert entry["maturity"] == "unassessed"
    assert entry["governance"] is None


@pytest.mark.parametrize("mutation", [
    lambda value: value.update(extra=True),
    lambda value: value.update(skill_id="Bad-ID"),
    lambda value: value.update(definition_xid="bad"),
    lambda value: value.update(definition_content_hash="0"),
    lambda value: value.update(observation_refs=[""]),
    lambda value: value.update(observation_refs=["same", "same"]),
    lambda value: value["promotion"].update(target_maturity="trial"),
])
def test_invalid_governance_is_rejected(metadata, tmp_path, mutation):
    definition = _write_definition(tmp_path, metadata)
    value = _record(definition, metadata)
    mutation(value)
    with pytest.raises(ValueError):
        load_governance_record(_write_record(tmp_path, value))


def test_duplicate_json_key_is_rejected(tmp_path):
    path = tmp_path / "governance.json"
    path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_governance_record(path)


def test_identity_hash_unmatched_and_duplicate_records_are_rejected(metadata, tmp_path):
    definition = _write_definition(tmp_path, metadata)
    value = _record(definition, metadata)
    mismatch = copy.deepcopy(value)
    mismatch["definition_content_hash"] = "0" * 64
    with pytest.raises(ValueError, match="content_hash"):
        build_definition_catalog([definition], [_write_record(tmp_path, mismatch)])

    other = copy.deepcopy(value)
    other.update(skill_id="other", definition_xid="111111111111")
    with pytest.raises(ValueError, match="unmatched"):
        build_definition_catalog([definition], [_write_record(tmp_path, other)])

    record_path = _write_record(tmp_path, value)
    with pytest.raises(ValueError, match="duplicate governance record path"):
        build_definition_catalog([definition], [record_path, record_path])


def test_cli_reports_governance_and_unassessed(metadata, tmp_path):
    definition = _write_definition(tmp_path, metadata)
    record_path = _write_record(tmp_path, _record(definition, metadata))
    code, output = command("skill", "definition-check", "--path", str(definition), "--json")
    assert code == 0
    assert json.loads(output)["maturity"] == "unassessed"
    code, output = command(
        "skill", "definition-check", "--path", str(definition),
        "--governance", str(record_path), "--json",
    )
    assert code == 0, output
    payload = json.loads(output)
    assert payload["maturity"] == "stable"
    assert payload["governance"]["promotion"]["decision"] == "approved"
