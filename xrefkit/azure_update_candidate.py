"""Pure deterministic offline previews; no credentials, transport or persistence."""
from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from xrefkit.work_management import read_json, validate_plan_v2

MAX_REFERENCES = 200
MAX_SUMMARY_BYTES = 32 * 1024
IDENTIFIER = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z")
KNOWN_STATUSES = {"pending", "in_progress", "done", "blocked", "unknown", "escalated"}
PREREQUISITES = ["task19_binding_import", "task20_local_first_evidence_policy", "current_local_observation_recheck", "current_remote_revision_metadata_permission_recheck", "authorized_writer_implementation"]


class InputError(ValueError):
    pass


def _object(value, keys, required=None):
    if not isinstance(value, dict) or set(value) - keys or not (keys if required is None else required).issubset(value):
        raise InputError("input_schema_invalid")


def _identifier(value):
    if not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None:
        raise InputError("identifier_invalid")


def _text(value, limit=256):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for char in value):
        raise InputError("text_invalid")


def _positive(value):
    if type(value) is not int or value <= 0:
        raise InputError("revision_or_item_invalid")


def _array(value, limit=MAX_REFERENCES):
    if not isinstance(value, list) or len(value) > limit:
        raise InputError("array_invalid")


def _references(value):
    _array(value)
    for ref in value:
        _text(ref, 2048)


def _snapshot(value):
    _object(value, {"organization", "project", "item_id", "work_item_type", "revision", "state", "observed_at"})
    _positive(value["item_id"])
    _positive(value["revision"])
    for key in ("organization", "project", "state", "observed_at"):
        _text(value[key])
    if value["work_item_type"] != "Task":
        raise InputError("work_item_type_invalid")
    try:
        stamp = datetime.fromisoformat(value["observed_at"])
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError
    except ValueError:
        raise InputError("observation_timestamp_invalid") from None


def _validate(envelope):
    keys = {"schema_version", "report_id", "target", "binding", "local_snapshot", "expected_observation_revision", "completion", "work_authorization", "remote_snapshot", "baseline", "metadata", "artifacts"}
    _object(envelope, keys, keys - {"artifacts"})
    if type(envelope["schema_version"]) is not int or envelope["schema_version"] != 1:
        raise InputError("schema_version_invalid")
    _identifier(envelope["report_id"])
    target = envelope["target"]
    _object(target, {"workspace_id", "connection_id", "organization", "project", "item_id"})
    for key in ("workspace_id", "connection_id"):
        _identifier(target[key])
    for key in ("organization", "project"):
        _text(target[key])
        if any(char in "/\\?#" for char in target[key]) or target[key] in {".", ".."}:
            raise InputError("target_segment_invalid")
    _positive(target["item_id"])
    binding = envelope["binding"]
    _object(binding, {"plan_id", "plan_revision", "included_step_ids", "completion_criterion", "initial_binding"})
    for key in ("plan_id", "plan_revision"):
        _identifier(binding[key])
    _text(binding["completion_criterion"], 2048)
    if type(binding["initial_binding"]) is not bool:
        raise InputError("authority_boolean_invalid")
    _array(binding["included_step_ids"])
    for step_id in binding["included_step_ids"]:
        _identifier(step_id)
    if not binding["included_step_ids"] or len(set(binding["included_step_ids"])) != len(binding["included_step_ids"]):
        raise InputError("binding_steps_invalid")
    local = envelope["local_snapshot"]
    if validate_plan_v2(local, stored=True):
        raise InputError("local_snapshot_invalid")
    if (local["workspace_id"], local["plan_id"], local["plan_revision"]) != (target["workspace_id"], binding["plan_id"], binding["plan_revision"]):
        raise InputError("source_identity_mismatch")
    _positive(envelope["expected_observation_revision"])
    steps = {step["step_id"]: step for step in local["steps"]}
    if any(step_id not in steps for step_id in binding["included_step_ids"]):
        raise InputError("included_step_missing")
    for key, flags in (("completion", {"confirmed"}), ("work_authorization", {"active", "rework"})):
        record = envelope[key]
        _object(record, flags | {"evidence_refs"})
        if any(type(record[flag]) is not bool for flag in flags):
            raise InputError("authority_boolean_invalid")
        _references(record["evidence_refs"])
        if any(record[flag] for flag in flags) and not record["evidence_refs"]:
            raise InputError("authority_reference_missing")
    if envelope["work_authorization"]["rework"] and not envelope["work_authorization"]["active"]:
        raise InputError("rework_requires_active_authorization")
    for key in ("remote_snapshot", "baseline"):
        snapshot = envelope[key]
        _snapshot(snapshot)
        if any(snapshot[field] != target[field] for field in ("organization", "project", "item_id")):
            raise InputError("remote_identity_mismatch")
    metadata = envelope["metadata"]
    _object(metadata, {"work_item_type", "states", "transitions"})
    if metadata["work_item_type"] != "Task":
        raise InputError("work_item_type_invalid")
    _array(metadata["states"])
    for state in metadata["states"]:
        _text(state, 128)
    if not metadata["states"] or len(set(metadata["states"])) != len(metadata["states"]):
        raise InputError("metadata_states_invalid")
    if not isinstance(metadata["transitions"], dict) or set(metadata["transitions"]) - set(metadata["states"]):
        raise InputError("metadata_transitions_invalid")
    for possible in metadata["transitions"].values():
        _array(possible)
        for state in possible:
            _text(state, 128)
        if len(set(possible)) != len(possible) or set(possible) - set(metadata["states"]):
            raise InputError("metadata_transitions_invalid")
    if any(envelope[key]["state"] not in metadata["states"] for key in ("remote_snapshot", "baseline")):
        raise InputError("remote_state_unrecognized")
    _array(envelope.get("artifacts", []))
    artifact_ids = []
    for artifact in envelope.get("artifacts", []):
        _object(artifact, {"artifact_id", "version", "availability"})
        _identifier(artifact["artifact_id"])
        _identifier(artifact["version"])
        if artifact["availability"] != "local_only":
            raise InputError("artifact_availability_invalid")
        artifact_ids.append((artifact["artifact_id"], artifact["version"]))
    if len(artifact_ids) != len(set(artifact_ids)):
        raise InputError("artifact_identity_ambiguous")
    return [steps[step_id] for step_id in binding["included_step_ids"]]


def _decision(envelope, steps):
    local, remote, baseline = (envelope[key] for key in ("local_snapshot", "remote_snapshot", "baseline"))
    if envelope["expected_observation_revision"] != local["observation_revision"]:
        return "hold", ["stale_local_snapshot"], None
    if remote["revision"] != baseline["revision"] or remote["state"] != baseline["state"]:
        return "conflict", ["remote_changed"], None
    if remote["state"] == "Removed":
        return "conflict", ["removed"], None
    statuses = [step.get("status") for step in steps]
    reasons = []
    for condition, code in ((any(value is None for value in statuses), "local_status_missing"), ("unknown" in statuses, "local_status_unknown"), (any(value is not None and value not in KNOWN_STATUSES for value in statuses), "local_status_unrecognized"), ("blocked" in statuses, "local_blocked"), ("escalated" in statuses, "local_escalated")):
        if condition:
            reasons.append(code)
    if reasons:
        return "hold", reasons, None
    authority = envelope["work_authorization"]
    revalidation = any(step.get("revalidation_needed") is True for step in steps)
    rework_active = authority["active"] and authority["rework"] and "in_progress" in statuses
    if revalidation and not rework_active:
        return "hold", ["revalidation_pending"], None
    if all(value == "done" for value in statuses):
        if not envelope["completion"]["confirmed"]:
            return "hold", ["criterion_unconfirmed"], None
        proposed, reasons = "Done", ["external_criterion_confirmed"]
    elif "in_progress" in statuses:
        if not authority["active"]:
            return "hold", ["active_work_not_authorized"], None
        if remote["state"] == "Done" and not authority["rework"]:
            return "hold", ["rework_not_authorized"], None
        proposed, reasons = "In Progress", ["authorized_rework" if rework_active else "authorized_active_work"]
        if revalidation:
            reasons.append("revalidation_pending")
    elif all(value == "pending" for value in statuses):
        if not envelope["binding"]["initial_binding"] or remote["state"] != "To Do":
            return "hold", ["no_forward_transition"], None
        proposed, reasons = "To Do", ["initial_binding"]
    else:
        return "hold", ["no_active_work"], None
    metadata = envelope["metadata"]
    if proposed not in metadata["states"] or proposed not in metadata["transitions"].get(remote["state"], []):
        return "hold", ["transition_unavailable"], None
    return "candidate", reasons, proposed


def _empty():
    return {"schema_version": 1, "outcome": "invalid", "reason_codes": [], "proposed_state": None, "summary": "", "patch_preview": [], "delivery_status": "not_sent", "network_performed": False, "remote_freshness_verified": False, "write_permission_verified": False, "publish_ready": False, "publication_prerequisites": list(PREREQUISITES)}


def build_candidate(envelope: object) -> dict:
    result = _empty()
    try:
        steps = _validate(envelope)
    except (InputError, ValueError, TypeError, RecursionError):
        result["reason_codes"] = ["input_invalid"]
        return result
    outcome, reasons, proposed = _decision(envelope, steps)
    source = {"workspace_id": envelope["target"]["workspace_id"], "plan_id": envelope["binding"]["plan_id"], "plan_revision": envelope["binding"]["plan_revision"], "observation_revision": envelope["local_snapshot"]["observation_revision"], "included_step_ids": list(envelope["binding"]["included_step_ids"])}
    summary = f"Offline preview; report={envelope['report_id']}; source={source['workspace_id']}/{source['plan_id']}@{source['plan_revision']}; observation={source['observation_revision']}; outcome={outcome}; reasons={','.join(reasons)}. "
    summary += "Steps: " + "; ".join(f"{step['step_id']}={step.get('status') if step.get('status') in KNOWN_STATUSES else 'missing' if step.get('status') is None else 'unrecognized'}; revalidation={'required' if step.get('revalidation_needed') is True else 'not_required' if step.get('revalidation_needed') is False else 'unrecorded'}" for step in steps)
    if envelope.get("artifacts"):
        summary += ". Artifacts (local only, accessibility unverified): " + "; ".join(f"{artifact['artifact_id']}@{artifact['version']}" for artifact in sorted(envelope["artifacts"], key=lambda item: (item["artifact_id"], item["version"])))
    summary = html.escape(summary, quote=True)
    if len(summary.encode("utf-8")) > MAX_SUMMARY_BYTES:
        result["reason_codes"] = ["summary_size_exceeded"]
        return result
    result.update(report_id=envelope["report_id"], outcome=outcome, reason_codes=reasons, target=dict(envelope["target"]), source=source, expected_remote_revision=envelope["remote_snapshot"]["revision"], proposed_state=proposed, summary=summary)
    if outcome == "candidate":
        result["patch_preview"] = [{"op": "test", "path": "/rev", "value": result["expected_remote_revision"]}]
        if proposed != envelope["remote_snapshot"]["state"]:
            result["patch_preview"].append({"op": "add", "path": "/fields/System.State", "value": proposed})
        result["patch_preview"].append({"op": "add", "path": "/fields/System.History", "value": summary})
    return result


class _SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError("arguments_invalid")


def main(argv=None):
    parser = _SafeParser(description="Generate an offline update preview; never sends or modifies records")
    parser.add_argument("--input", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        result = build_candidate(read_json(args.input))
    except (OSError, ValueError, UnicodeError, RuntimeError, RecursionError):
        result = _empty()
        result["reason_codes"] = ["input_invalid"]
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0 if result["outcome"] != "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
