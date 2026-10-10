"""One-shot, explicitly scoped Task21 State/History delivery with durable proof."""
from __future__ import annotations

import base64
import copy
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import ProxyHandler, Request, build_opener

from . import azure_import as importer
from .azure_connection import TIMEOUT_SECONDS, _NoRedirect, _SafeParser, _workspace, load_connection
from .azure_update_candidate import build_candidate, MAX_SUMMARY_BYTES
from .work_management import MAX_BYTES, MAX_RECORDS, _unique, plan_definition, read_json, writer_lock

OUTCOMES = {"success", "hold", "conflict", "rejected", "unknown"}
DIAGNOSTICS = {"delivered_verified", "credential_unavailable", "fresh_read_failed", "metadata_invalid", "candidate_hold", "candidate_conflict", "candidate_invalid", "http_rejected", "revision_rejected", "http_rate_limited", "dispatch_unconfirmed", "readback_unconfirmed", "protected_fields_changed", "receipt_persistence_failed", "intent_unresolved", "pre_dispatch_source_changed"}
COMMON = {"schema_version", "kind", "workspace_id", "record_id", "recorded_at", "request", "request_sha256", "target", "record_sha256"}
INTENT_FIELDS = COMMON | {"binding_sha256", "source", "baseline", "before", "metadata", "candidate", "patch", "protected_fields"}
TERMINAL_FIELDS = COMMON | {"intent_sha256", "outcome", "diagnostic_code", "network_attempted", "remote_write_attempted", "sent_confirmed", "after", "summary_verified", "protected_fields_unchanged"}


class WriterError(ValueError):
    """Fixed diagnostics, never caller, HTTP or credential text."""

    def __init__(self, code, *, network_attempted=False, remote_write_attempted=False, possibly_sent=False):
        super().__init__(code)
        self.network_attempted = network_attempted
        self.remote_write_attempted = remote_write_attempted
        self.possibly_sent = possibly_sent


def _fail(code, **truth):
    raise WriterError(code, **truth)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _request(value):
    required = {"schema_version", "report_id", "connection_id", "source_connection_id", "write_approval_refs", "binding_id", "item_id", "expected_observation_revision", "completion", "work_authorization"}
    if not isinstance(value, dict) or not required.issubset(value) or set(value) - required - {"previous_report_id", "artifacts"} or type(value["schema_version"]) is not int or value["schema_version"] != 1:
        _fail("writer_request_invalid")
    if value.get("previous_report_id") is not None and not importer._id(value["previous_report_id"]):
        _fail("writer_identity_invalid")
    if any(not importer._id(value[k]) for k in ["report_id", "connection_id", "source_connection_id", "binding_id"]):
        _fail("writer_identity_invalid")
    if not importer._number(value["item_id"]) or not importer._number(value["expected_observation_revision"]):
        _fail("writer_revision_invalid")
    for key, flags in [("completion", {"confirmed"}), ("work_authorization", {"active", "rework"})]:
        obj = value[key]
        if not isinstance(obj, dict) or set(obj) != flags | {"evidence_refs"} or any(type(obj[f]) is not bool for f in flags):
            _fail("writer_authority_invalid")
        _refs(obj["evidence_refs"], required=any(obj[f] for f in flags))
    _refs(value["write_approval_refs"], required=True)
    artifacts = value.get("artifacts", [])
    if not isinstance(artifacts, list) or len(artifacts) > MAX_RECORDS:
        _fail("writer_artifacts_invalid")
    pairs = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {"artifact_id", "version", "availability"} or any(not importer._id(artifact[k]) for k in ["artifact_id", "version"]) or artifact["availability"] != "local_only":
            _fail("writer_artifacts_invalid")
        pair = artifact["artifact_id"], artifact["version"]
        if pair in pairs:
            _fail("writer_artifacts_invalid")
        pairs.add(pair)


def _refs(value, required):
    if not isinstance(value, list) or len(value) > MAX_RECORDS or (required and not value) or any(not importer._text(r, 2048) for r in value) or len(set(value)) != len(value):
        _fail("writer_evidence_invalid")


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _metadata(value):
    if not isinstance(value, dict) or value.get("name") != "Task" or value.get("referenceName") != "Microsoft.VSTS.WorkItemTypes.Task" or value.get("isDisabled") is not False:
        _fail("metadata_invalid")
    states, transitions, fields = value.get("states"), value.get("transitions"), value.get("fields")
    if not isinstance(states, list) or not states or len(states) > MAX_RECORDS or any(not isinstance(s, dict) or not importer._text(s.get("name")) for s in states):
        _fail("metadata_invalid")
    names = [s["name"] for s in states]
    if len(set(names)) != len(names) or not isinstance(transitions, dict) or len(transitions) > MAX_RECORDS or not isinstance(fields, list) or len(fields) > 1000:
        _fail("metadata_invalid")
    if not {"System.State", "System.History"}.issubset({f.get("referenceName") for f in fields if isinstance(f, dict)}):
        _fail("metadata_invalid")
    projected = {}
    for source, destinations in transitions.items():
        if (source != "" and source not in names) or not isinstance(destinations, list) or len(destinations) > MAX_RECORDS:
            _fail("metadata_invalid")
        targets = []
        for dest in destinations:
            if not isinstance(dest, dict) or set(dest) != {"to", "actions"} or dest["to"] not in names or (dest["actions"] is not None and (not isinstance(dest["actions"], list) or len(dest["actions"]) > MAX_RECORDS or any(not importer._text(a, 256) for a in dest["actions"]))):
                _fail("metadata_invalid")
            targets.append(dest["to"])
        if len(set(targets)) != len(targets):
            _fail("metadata_invalid")
        if source:
            projected[source] = targets
    return {"work_item_type": "Task", "states": names, "transitions": projected}


def _transport(profile, token, resource, *, method="GET", patch=None):
    encoded = base64.b64encode((":" + token).encode("ascii")).decode("ascii")
    query = {"api-version": "7.1"}
    if method == "GET" and resource.startswith("workitems/"):
        query["$expand"] = "Relations"
    if method == "PATCH":
        query.update(bypassRules="false", validateOnly="false")
    target = "https://dev.azure.com/" + quote(profile["organization"], safe="") + "/" + quote(profile["project"], safe="") + "/_apis/wit/" + resource + "?" + urlencode(query)
    headers = {"Authorization": "Basic " + encoded, "Accept": "application/json"}
    body = None
    if patch is not None:
        body = json.dumps(patch, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        headers["Content-Type"] = "application/json-patch+json"
    request = Request(target, data=body, headers=headers, method=method)
    try:
        with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != target or response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json" or any(k.lower() in {"x-ms-continuationtoken", "x-ms-continuation-token"} for k in response.headers):
                _fail("dispatch_unconfirmed" if method == "PATCH" else "fresh_read_failed")
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                _fail("dispatch_unconfirmed" if method == "PATCH" else "fresh_read_failed")
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
            serialized = json.dumps(value, ensure_ascii=False)
            if token in serialized or encoded in serialized or not isinstance(value, dict) or any(k in value for k in {"value", "count", "continuationToken", "continuation_token", "nextLink", "@odata.nextLink", "next_link"}):
                _fail("dispatch_unconfirmed" if method == "PATCH" else "fresh_read_failed")
            return value
    except HTTPError as exc:
        code = exc.code
        exc.close()
        if method == "PATCH":
            if code in {409, 412}:
                _fail("revision_rejected")
            if code in {400, 401, 403, 404, 422}:
                _fail("http_rejected")
            if code == 429:
                _fail("http_rate_limited")
        _fail("dispatch_unconfirmed" if method == "PATCH" else "fresh_read_failed")
    except (URLError, TimeoutError, OSError, ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, WriterError):
            raise
        _fail("dispatch_unconfirmed" if method == "PATCH" else "fresh_read_failed")


def _observation(value, context, item_id, token, anchor=None):
    encoded = base64.b64encode((":" + token).encode("ascii")).decode("ascii")
    try:
        return importer._project(value, context, item_id, token, encoded, anchor)
    except (ValueError, TypeError, KeyError, RecursionError):
        _fail("fresh_read_failed")


def _protected(value, observation):
    fields = value.get("fields")
    if not isinstance(fields, dict):
        _fail("fresh_read_failed")
    keys = {"System.Description", "System.AssignedTo", "Microsoft.VSTS.Scheduling.RemainingWork", "Microsoft.VSTS.CMMI.Blocked"}
    keys.update(k for k in fields if "duedate" in k.lower())
    if any(not isinstance(k, str) or re.fullmatch(r"[A-Za-z0-9_.]{1,256}", k) is None for k in keys):
        _fail("fresh_read_failed")
    return {"fields": {k: {"present": k in fields, "sha256": importer._hash(fields[k]) if k in fields else None} for k in sorted(keys)}, "parent_sha256": importer._hash({k: observation.get(k) for k in ["parent_id", "parent_relation", "canonical_project_id", "canonical_parent_url"]})}


def _summary(request, plan, group):
    steps = {s["step_id"]: s for s in plan["steps"]}
    text = f"XRefKit report={request['report_id']}; source={plan['workspace_id']}/{plan['plan_id']}@{plan['plan_revision']}; observation={plan['observation_revision']}. Steps: "
    text += "; ".join(f"{identity}={steps[identity].get('status')}; revalidation={'required' if steps[identity].get('revalidation_needed') is True else 'not_required' if steps[identity].get('revalidation_needed') is False else 'unrecorded'}" for identity in group["included_step_ids"])
    if request.get("artifacts"):
        text += ". Artifacts (local_only; accessibility unverified): " + "; ".join(f"{a['artifact_id']}@{a['version']}" for a in sorted(request["artifacts"], key=lambda a: (a["artifact_id"], a["version"])))
    result = html.escape(text, quote=True)
    if len(result.encode("utf-8")) > MAX_SUMMARY_BYTES:
        _fail("writer_summary_size_exceeded", network_attempted=True)
    return result


def _patch(before, proposed, summary):
    result = [{"op": "test", "path": "/rev", "value": before["revision"]}]
    if proposed != before["state"]:
        result.append({"op": "add", "path": "/fields/System.State", "value": proposed})
    result.append({"op": "add", "path": "/fields/System.History", "value": summary})
    return result


def _common(kind, workspace_id, request, target):
    return {"schema_version": 1, "kind": kind, "workspace_id": workspace_id, "record_id": request["report_id"], "recorded_at": _now(), "request": request, "request_sha256": importer._hash(request), "target": target}


def _validate(value, workspace_id, kind):
    if not isinstance(value, dict) or set(value) != (INTENT_FIELDS if kind == "intent" else TERMINAL_FIELDS) or type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["kind"] != kind or value["workspace_id"] != workspace_id:
        _fail("delivery_record_invalid")
    _request(value["request"])
    if value["record_id"] != value["request"]["report_id"] or value["request_sha256"] != importer._hash(value["request"]) or value["record_sha256"] != importer._hash({k: v for k, v in value.items() if k != "record_sha256"}):
        _fail("delivery_record_invalid")
    try:
        if datetime.fromisoformat(value["recorded_at"]).utcoffset() is None:
            _fail("delivery_record_invalid")
    except (ValueError, TypeError):
        _fail("delivery_record_invalid")
    target = value["target"]
    if not isinstance(target, dict) or set(target) != {"workspace_id", "organization", "project", "environment", "pbi_id", "item_id"} or target["workspace_id"] != workspace_id or target["environment"] != "test" or type(target["pbi_id"]) is not int or target["pbi_id"] != 10 or type(target["item_id"]) is not int or target["item_id"] != 21 or value["request"]["item_id"] != 21 or any(not importer._text(target[k]) for k in ["organization", "project"]):
        _fail("delivery_record_invalid")
    if kind == "intent":
        source, baseline, before, metadata = value["source"], value["baseline"], value["before"], value["metadata"]
        if not _digest(value["binding_sha256"]) or not isinstance(source, dict) or set(source) != {"plan_id", "plan_revision", "plan_definition_sha256", "plan_snapshot_sha256", "observation_revision"} or any(not importer._id(source[k]) for k in ["plan_id", "plan_revision"]) or any(not _digest(source[k]) for k in ["plan_definition_sha256", "plan_snapshot_sha256"]) or type(source["observation_revision"]) is not int or source["observation_revision"] != value["request"]["expected_observation_revision"]:
            _fail("delivery_record_invalid")
        if not isinstance(baseline, dict) or set(baseline) != {"kind", "record_id", "record_sha256", "revision", "state"} or baseline["kind"] not in {"import", "success"} or not importer._id(baseline["record_id"]) or not _digest(baseline["record_sha256"]) or not importer._number(baseline["revision"]) or not importer._text(baseline["state"]) or (baseline["kind"] == "success") != (value["request"].get("previous_report_id") is not None) or (baseline["kind"] == "success" and baseline["record_id"] != value["request"]["previous_report_id"]):
            _fail("delivery_record_invalid")
        if not isinstance(before, dict) or set(before) != {"revision", "state"} or before != {k: baseline[k] for k in ["revision", "state"]}:
            _fail("delivery_record_invalid")
        if not isinstance(metadata, dict) or set(metadata) != {"work_item_type", "states", "transitions"}:
            _fail("delivery_record_invalid")
        _metadata({"name": "Task", "referenceName": "Microsoft.VSTS.WorkItemTypes.Task", "isDisabled": False, "states": [{"name": n} for n in metadata["states"]], "transitions": {k: [{"to": n, "actions": None} for n in v] for k, v in metadata["transitions"].items()}, "fields": [{"referenceName": k} for k in ["System.State", "System.History"]]})
        candidate = value["candidate"]
        if not isinstance(candidate, dict) or set(candidate) != {"proposed_state", "reason_codes", "summary"} or candidate["proposed_state"] not in metadata["transitions"].get(before["state"], []) or not isinstance(candidate["reason_codes"], list) or not candidate["reason_codes"] or any(not importer._id(code) for code in candidate["reason_codes"]) or not isinstance(candidate["summary"], str) or not candidate["summary"].startswith("XRefKit report=" + value["record_id"] + ";") or len(candidate["summary"].encode("utf-8")) > MAX_SUMMARY_BYTES or value["patch"] != _patch(before, candidate["proposed_state"], candidate["summary"]):
            _fail("delivery_record_invalid")
        protected = value["protected_fields"]
        required_protected = {"System.Description", "System.AssignedTo", "Microsoft.VSTS.Scheduling.RemainingWork", "Microsoft.VSTS.CMMI.Blocked"}
        if not isinstance(protected, dict) or set(protected) != {"fields", "parent_sha256"} or not _digest(protected["parent_sha256"]) or not isinstance(protected["fields"], dict) or not required_protected.issubset(protected["fields"]):
            _fail("delivery_record_invalid")
        for key, field in protected["fields"].items():
            if not isinstance(key, str) or re.fullmatch(r"[A-Za-z0-9_.]{1,256}", key) is None or (key not in required_protected and "duedate" not in key.lower()) or not isinstance(field, dict) or set(field) != {"present", "sha256"} or type(field["present"]) is not bool or (not _digest(field["sha256"]) if field["present"] else field["sha256"] is not None):
                _fail("delivery_record_invalid")
    else:
        if value["outcome"] not in OUTCOMES or value["diagnostic_code"] not in DIAGNOSTICS or any(type(value[k]) is not bool for k in ["network_attempted", "remote_write_attempted", "sent_confirmed", "summary_verified", "protected_fields_unchanged"]):
            _fail("delivery_record_invalid")
        if value["intent_sha256"] is not None and not _digest(value["intent_sha256"]):
            _fail("delivery_record_invalid")
        allowed = {
            ("hold", "credential_unavailable", False, False),
            ("hold", "fresh_read_failed", True, False),
            ("hold", "metadata_invalid", True, False),
            ("hold", "candidate_hold", True, False),
            ("hold", "candidate_invalid", True, False),
            ("conflict", "candidate_conflict", True, False),
            ("success", "delivered_verified", True, True),
            ("conflict", "revision_rejected", True, True),
            ("rejected", "http_rejected", True, True),
            ("rejected", "http_rate_limited", True, True),
            ("unknown", "dispatch_unconfirmed", True, True),
            ("unknown", "readback_unconfirmed", True, True),
            ("unknown", "protected_fields_changed", True, True),
            ("unknown", "pre_dispatch_source_changed", True, True),
        }
        if (value["outcome"], value["diagnostic_code"], value["network_attempted"], value["intent_sha256"] is not None) not in allowed:
            _fail("delivery_record_invalid")
        success = value["outcome"] == "success"
        attempted = value["intent_sha256"] is not None and value["diagnostic_code"] != "pre_dispatch_source_changed"
        if value["remote_write_attempted"] != attempted or value["sent_confirmed"] != success or (value["remote_write_attempted"] and not value["network_attempted"]) or (success and (value["diagnostic_code"] != "delivered_verified" or not value["summary_verified"] or not value["protected_fields_unchanged"])):
            _fail("delivery_record_invalid")
        after = value["after"]
        if success:
            if not isinstance(after, dict) or set(after) != {"revision", "state"} or not importer._number(after["revision"]) or not importer._text(after["state"]):
                _fail("delivery_record_invalid")
        elif after is not None or value["summary_verified"] or value["protected_fields_unchanged"]:
            _fail("delivery_record_invalid")


def _rows(directory, workspace_id, kind):
    paths = list(directory.glob("*.json"))
    if len(paths) > MAX_RECORDS:
        _fail("delivery_record_limit_exceeded")
    values = {}
    for path in paths:
        try:
            path.resolve().relative_to(directory.resolve())
            value = read_json(path)
            _validate(value, workspace_id, kind)
        except (OSError, ValueError, TypeError, KeyError, UnicodeError, RuntimeError, RecursionError):
            _fail("delivery_record_invalid")
        if value["record_id"] in values:
            _fail("delivery_identity_ambiguous")
        values[value["record_id"]] = (path, value)
    return values


def _pairs(intents, terminals):
    successors, observations = set(), set()
    for _, intent in intents.values():
        observation = (importer._hash(intent["target"]), intent["source"]["plan_id"], intent["source"]["plan_revision"], intent["source"]["observation_revision"])
        if observation in observations:
            _fail("delivery_observation_ambiguous")
        observations.add(observation)
        baseline = intent["baseline"]
        if baseline["kind"] == "success":
            if baseline["record_id"] in successors:
                _fail("delivery_successor_ambiguous")
            successors.add(baseline["record_id"])
            predecessor = terminals.get(baseline["record_id"])
            if not predecessor or predecessor[1]["outcome"] != "success" or predecessor[1]["record_sha256"] != baseline["record_sha256"] or predecessor[1]["after"] != {k: baseline[k] for k in ["revision", "state"]} or predecessor[1]["target"] != intent["target"] or predecessor[1]["request"]["binding_id"] != intent["request"]["binding_id"] or predecessor[1]["request"]["expected_observation_revision"] >= intent["source"]["observation_revision"]:
                _fail("delivery_baseline_provenance_invalid")
    for identity, (_, terminal) in terminals.items():
        intent = intents.get(identity)
        if terminal["intent_sha256"] is not None:
            if not intent or terminal["intent_sha256"] != intent[1]["record_sha256"] or terminal["request"] != intent[1]["request"] or terminal["target"] != intent[1]["target"]:
                _fail("delivery_pair_invalid")
            if terminal["outcome"] == "success" and (terminal["after"]["state"] != intent[1]["candidate"]["proposed_state"] or terminal["after"]["revision"] <= intent[1]["before"]["revision"]):
                _fail("delivery_pair_invalid")
        elif intent:
            _fail("delivery_pair_invalid")


def _result(value, path, replayed=False):
    intent = value["kind"] == "intent"
    return {"schema_version": 1, "report_id": value["record_id"], "outcome": "unknown" if intent else value["outcome"], "diagnostic_code": "intent_unresolved" if intent else value["diagnostic_code"], "replayed": replayed, "network_attempted": False if replayed else value.get("network_attempted", True), "remote_write_attempted": False if replayed else value.get("remote_write_attempted", False), "captured_remote_write_attempted": value.get("remote_write_attempted"), "sent_confirmed": value.get("sent_confirmed", False), "possibly_sent": intent or value.get("outcome") == "unknown" and value["diagnostic_code"] != "pre_dispatch_source_changed", "needs_resolution": intent or value.get("outcome") in {"unknown", "conflict"}, "record_sha256": value["record_sha256"], "output": str(path), "after": value.get("after")}


def publish(root: Path, workspace_id: str, request: dict) -> dict:
    """Deliver once; replays and unresolved targets perform no credential/network work."""
    _request(request)
    request = copy.deepcopy(request)
    root = root.resolve()
    workspace = _workspace(root, workspace_id)
    profile = load_connection(root, workspace_id, request["connection_id"])
    if profile["environment"] != "test" or set(profile["allowed_operations"]) != {"read_work_item", "update_task_state_history"} or set(profile["allowed_item_ids"]) != {10, 21} or request["item_id"] != 21:
        _fail("writer_trial_scope_rejected")
    binding_pair = importer._load_record(importer._directory(workspace, "bindings"), request["binding_id"], workspace_id, "azure_binding")
    if not binding_pair:
        _fail("writer_binding_missing")
    binding = binding_pair[1]
    capture_pair = importer._load_record(importer._directory(workspace, "imports"), binding["request"]["import_id"], workspace_id, "azure_import")
    if not capture_pair or not capture_pair[1]["complete"] or capture_pair[1]["record_sha256"] != binding["import_record_sha256"]:
        _fail("writer_import_invalid")
    capture = capture_pair[1]
    context = capture["request"]
    captured_target = {k: context[k] for k in ["connection_id", "organization", "project", "pbi_id", "task_ids"]}
    captured_target["observed_items"] = [{k: row["observation"][k] for k in ["item_id", "revision", "type", "parent_id"]} for row in capture["items"]]
    if binding["target"] != captured_target:
        _fail("writer_binding_capture_mismatch")
    if request["source_connection_id"] != context["connection_id"] or binding["target"]["connection_id"] != request["source_connection_id"] or profile["organization"] != context["organization"] or profile["project"] != context["project"] or context["pbi_id"] != 10 or 21 not in context["task_ids"]:
        _fail("writer_binding_scope_rejected")
    source_profile = load_connection(root, workspace_id, request["source_connection_id"])
    if source_profile["environment"] != "test" or "read_work_item" not in source_profile["allowed_operations"] or source_profile["organization"] != context["organization"] or source_profile["project"] != context["project"] or not {10, 21}.issubset(source_profile["allowed_item_ids"]):
        _fail("writer_source_profile_rejected")
    group = next((g for g in binding["request"]["mapping"] if g["item_id"] == 21), None)
    if group is None:
        _fail("writer_mapping_missing")
    target = {"workspace_id": workspace_id, "organization": context["organization"], "project": context["project"], "environment": "test", "pbi_id": 10, "item_id": 21}
    base_dir = importer._directory(workspace, "deliveries", create=True)
    intent_dir, terminal_dir = base_dir / "intents", base_dir / "receipts"
    for directory in [intent_dir, terminal_dir]:
        try:
            directory.resolve().relative_to(workspace)
            directory.mkdir(parents=True, exist_ok=True)
        except (ValueError, OSError, RuntimeError):
            _fail("delivery_directory_unavailable")
    with writer_lock(workspace / "work/plans/.records.lock"), writer_lock(base_dir / ".deliveries.lock"):
        intents, terminals = _rows(intent_dir, workspace_id, "intent"), _rows(terminal_dir, workspace_id, "terminal")
        _pairs(intents, terminals)
        for _, intent in intents.values():
            if intent["request"]["binding_id"] == binding["record_id"] and (intent["binding_sha256"] != binding["record_sha256"] or intent["source"]["plan_definition_sha256"] != binding["source"]["plan_definition_sha256"] or (intent["source"]["plan_id"], intent["source"]["plan_revision"]) != (binding["request"]["plan_id"], binding["request"]["plan_revision"])):
                _fail("delivery_binding_provenance_invalid")
            if intent["request"]["binding_id"] == binding["record_id"] and intent["baseline"]["kind"] == "import":
                observed = next(r["observation"] for r in capture["items"] if r["item_id"] == 21)
                if intent["baseline"] != {"kind": "import", "record_id": capture["record_id"], "record_sha256": capture["record_sha256"], "revision": observed["revision"], "state": observed["state"]}:
                    _fail("delivery_baseline_provenance_invalid")
        identity = request["report_id"]
        old = terminals.get(identity) or intents.get(identity)
        if old:
            if old[1]["request"] != request or old[1]["target"] != target:
                _fail("writer_report_identity_conflict")
            return _result(old[1], old[0], True)
        for other_id, (_, intent) in intents.items():
            if intent["target"] == target:
                terminal = terminals.get(other_id)
                if terminal is None or terminal[1]["outcome"] == "unknown":
                    _fail("writer_target_unresolved")
                if (intent["source"]["plan_id"], intent["source"]["plan_revision"]) == (binding["request"]["plan_id"], binding["request"]["plan_revision"]) and intent["request"]["expected_observation_revision"] == request["expected_observation_revision"]:
                    _fail("writer_observation_already_dispatched")
        successes = [v for _, v in terminals.values() if v["target"] == target and v["outcome"] == "success"]
        previous = request.get("previous_report_id")
        selected = next(r["observation"] for r in capture["items"] if r["item_id"] == 21)
        baseline = {"kind": "import", "record_id": capture["record_id"], "record_sha256": capture["record_sha256"], "revision": selected["revision"], "state": selected["state"]}
        if previous is None:
            if successes:
                _fail("writer_success_predecessor_required")
        else:
            predecessor = terminals.get(previous)
            if not predecessor or predecessor[1]["outcome"] != "success" or predecessor[1]["target"] != target or predecessor[1]["request"]["binding_id"] != request["binding_id"] or request["expected_observation_revision"] <= predecessor[1]["request"]["expected_observation_revision"]:
                _fail("writer_success_predecessor_invalid")
            if any(v["request"].get("previous_report_id") == previous for _, v in intents.values()):
                _fail("writer_success_predecessor_consumed")
            baseline = {"kind": "success", "record_id": previous, "record_sha256": predecessor[1]["record_sha256"], **predecessor[1]["after"]}
        if len(intents) >= MAX_RECORDS or len(terminals) >= MAX_RECORDS or any(importer._target(d, identity).exists() for d in [intent_dir, terminal_dir]):
            _fail("delivery_capacity_unavailable")
        plan = importer._plan(workspace, workspace_id, binding["request"]["plan_id"], binding["request"]["plan_revision"], request["expected_observation_revision"], root)
        if importer._hash(plan_definition(plan)) != binding["source"]["plan_definition_sha256"]:
            _fail("writer_plan_definition_conflict")
        importer._mapping(plan, capture, binding["request"])
        terminal = {**_common("terminal", workspace_id, request, target), "intent_sha256": None, "outcome": "hold", "diagnostic_code": "credential_unavailable", "network_attempted": False, "remote_write_attempted": False, "sent_confirmed": False, "after": None, "summary_verified": False, "protected_fields_unchanged": False}

        def finish():
            sealed = importer._seal(terminal)
            try:
                _validate(sealed, workspace_id, "terminal")
                path = importer._save(terminal_dir, sealed)
            except (OSError, ValueError):
                if terminal["intent_sha256"] is not None:
                    return {"schema_version": 1, "report_id": identity, "outcome": "unknown", "diagnostic_code": "receipt_persistence_failed", "replayed": False, "network_attempted": True, "remote_write_attempted": terminal["remote_write_attempted"], "sent_confirmed": False, "possibly_sent": terminal["remote_write_attempted"], "needs_resolution": True, "output": str(importer._target(intent_dir, identity)), "after": None}
                _fail("writer_receipt_persistence_failed", network_attempted=terminal["network_attempted"])
            return _result(sealed, path)

        token = os.environ.get(profile["auth"]["env_var"])
        if not token or not token.isascii() or len(token) > 4096 or any(ord(c) < 32 or ord(c) == 127 for c in token):
            return finish()
        encoded = base64.b64encode((":" + token).encode("ascii")).decode("ascii")
        if token in json.dumps(request, ensure_ascii=False) or encoded in json.dumps(request, ensure_ascii=False):
            _fail("writer_credential_echo_rejected")
        terminal["network_attempted"] = True
        try:
            root_value = _transport(profile, token, "workitems/10")
            root_observation = _observation(root_value, context, 10, token)
            anchor = root_observation.get("canonical_project_id")
            before_value = _transport(profile, token, "workitems/21")
            observation = _observation(before_value, context, 21, token, anchor)
            metadata = _metadata(_transport(profile, token, "workitemtypes/Task"))
            protected = _protected(before_value, observation)
        except (WriterError, ValueError, TypeError, KeyError, RecursionError) as exc:
            terminal["diagnostic_code"] = "metadata_invalid" if str(exc) == "metadata_invalid" else "fresh_read_failed"
            return finish()
        stamp = _now()
        snapshot = {"organization": context["organization"], "project": context["project"], "item_id": 21, "work_item_type": "Task", "revision": observation["revision"], "state": observation["state"], "observed_at": stamp}
        envelope = {"schema_version": 1, "report_id": identity, "target": {"workspace_id": workspace_id, "connection_id": profile["connection_id"], "organization": context["organization"], "project": context["project"], "item_id": 21}, "binding": {"plan_id": plan["plan_id"], "plan_revision": plan["plan_revision"], "included_step_ids": group["included_step_ids"], "completion_criterion": group["completion_criterion"], "initial_binding": previous is None}, "local_snapshot": plan, "expected_observation_revision": request["expected_observation_revision"], "completion": request["completion"], "work_authorization": request["work_authorization"], "remote_snapshot": snapshot, "baseline": {**snapshot, "revision": baseline["revision"], "state": baseline["state"]}, "metadata": metadata, "artifacts": request.get("artifacts", [])}
        candidate = build_candidate(envelope)
        if candidate["outcome"] != "candidate":
            terminal.update(outcome="conflict" if candidate["outcome"] == "conflict" else "hold", diagnostic_code="candidate_" + candidate["outcome"])
            return finish()
        try:
            summary = _summary(request, plan, group)
            before = {"revision": observation["revision"], "state": observation["state"]}
            patch = _patch(before, candidate["proposed_state"], summary)
            source = {"plan_id": plan["plan_id"], "plan_revision": plan["plan_revision"], "plan_definition_sha256": importer._hash(plan_definition(plan)), "plan_snapshot_sha256": importer._hash(plan), "observation_revision": plan["observation_revision"]}
            intent = importer._seal({**_common("intent", workspace_id, request, target), "binding_sha256": binding["record_sha256"], "source": source, "baseline": baseline, "before": before, "metadata": metadata, "candidate": {"proposed_state": candidate["proposed_state"], "reason_codes": candidate["reason_codes"], "summary": summary}, "patch": patch, "protected_fields": protected})
            _validate(intent, workspace_id, "intent")
            importer._save(intent_dir, intent)
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            exists = importer._target(intent_dir, identity).exists()
            _fail("writer_intent_persistence_failed", network_attempted=True, possibly_sent=exists)
        terminal.update(intent_sha256=intent["record_sha256"], outcome="unknown", diagnostic_code="pre_dispatch_source_changed")
        try:
            current = importer._plan(workspace, workspace_id, plan["plan_id"], plan["plan_revision"], request["expected_observation_revision"], root)
            if importer._hash(current) != source["plan_snapshot_sha256"]:
                _fail("pre_dispatch_source_changed")
            terminal.update(diagnostic_code="dispatch_unconfirmed", remote_write_attempted=True)
            updated_value = _transport(profile, token, "workitems/21", method="PATCH", patch=patch)
            updated = _observation(updated_value, context, 21, token, anchor)
            if updated["revision"] <= before["revision"] or updated["state"] != candidate["proposed_state"] or updated_value["fields"].get("System.History") != summary:
                _fail("dispatch_unconfirmed")
            if _protected(updated_value, updated) != protected:
                _fail("protected_fields_changed")
            readback_value = _transport(profile, token, "workitems/21")
            readback = _observation(readback_value, context, 21, token, anchor)
            if readback["revision"] != updated["revision"] or readback["state"] != candidate["proposed_state"] or readback_value["fields"].get("System.History") != summary:
                _fail("readback_unconfirmed")
            if _protected(readback_value, readback) != protected:
                _fail("protected_fields_changed")
            terminal.update(outcome="success", diagnostic_code="delivered_verified", sent_confirmed=True, after={"revision": readback["revision"], "state": readback["state"]}, summary_verified=True, protected_fields_unchanged=True)
        except (ValueError, OSError, TypeError, KeyError, RecursionError) as exc:
            diagnostic = str(exc) if isinstance(exc, WriterError) and str(exc) in DIAGNOSTICS else "dispatch_unconfirmed" if terminal["remote_write_attempted"] else "pre_dispatch_source_changed"
            outcome = "conflict" if diagnostic == "revision_rejected" else "rejected" if diagnostic in {"http_rejected", "http_rate_limited"} else "unknown"
            terminal.update(outcome=outcome, diagnostic_code=diagnostic)
        return finish()


def main(argv=None):
    parser = _SafeParser(description="Explicit test Task21 State/History delivery; no automatic retry")
    parser.add_argument("action", choices=["publish"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--input", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        result = publish(args.root, args.workspace_id, read_json(args.input))
    except (OSError, ValueError, TypeError, UnicodeError, RuntimeError, RecursionError) as exc:
        possible = getattr(exc, "possibly_sent", False)
        result = {"schema_version": 1, "outcome": "unknown" if possible else "hold", "diagnostic_code": "writer_request_rejected", "network_attempted": getattr(exc, "network_attempted", False), "remote_write_attempted": getattr(exc, "remote_write_attempted", False), "sent_confirmed": False, "possibly_sent": possible, "needs_resolution": possible}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0 if result["outcome"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
