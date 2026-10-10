"""Positive-proof-only read reconciliation; never sends or retries a delivery."""
from __future__ import annotations

import base64
import copy
import json
import re
from datetime import datetime
from pathlib import Path

from . import azure_import as importer
from . import azure_writer as writer
from .azure_connection import _SafeParser, _workspace, load_connection
from .work_management import MAX_RECORDS, plan_definition, read_json, writer_lock

OUTCOMES = {"confirmed_applied", "applied_remote_changed", "unresolved", "retained_non_success"}
PHASE_CODES = {"read_verified", "credential_unavailable", "fresh_read_failed", "authentication_rejected", "access_forbidden", "unavailable_or_not_visible", "rate_limited", "server_failure", "http_response_rejected", "redirect_rejected", "revision_response_invalid"}
IDENTITY_KEYS = {"item_id", "project", "type", "parent_id", "parent_relation", "canonical_project_id", "canonical_item_url", "canonical_parent_url"}
PROJECTION_KEYS = {"identity", "revision", "state", "summary_sha256", "protected_fields"}
RECORD_KEYS = {"schema_version", "kind", "workspace_id", "record_id", "recorded_at", "request", "request_sha256", "target", "original_outcome", "original_write_attempted", "intent_sha256", "terminal_sha256", "binding_sha256", "import_sha256", "source", "expected_applied_revision", "root_identity", "current", "applied", "historical_url", "phases", "outcome", "reason_codes", "network_attempted", "resume_ready", "verified_at", "record_sha256"}


class RecoveryError(ValueError):
    def __init__(self, code, *, network_attempted=False):
        super().__init__(code)
        self.network_attempted = network_attempted


def _fail(code, **truth):
    raise RecoveryError(code, **truth)


def _request(value):
    keys = {"schema_version", "reconciliation_id", "report_id", "connection_id", "source_connection_id", "binding_id", "expected_observation_revision", "approval_refs"}
    if not isinstance(value, dict) or set(value) != keys or type(value["schema_version"]) is not int or value["schema_version"] != 1 or any(not importer._id(value[k]) for k in ["reconciliation_id", "report_id", "connection_id", "source_connection_id", "binding_id"]) or not importer._number(value["expected_observation_revision"]):
        _fail("reconciliation_request_invalid")
    writer._refs(value["approval_refs"], required=True)


def _original(workspace, workspace_id, report_id, intents, terminals):
    intent = intents.get(report_id)
    terminal = terminals.get(report_id)
    if not intent and not terminal:
        _fail("original_report_missing")
    record = (intent or terminal)[1]
    request = record["request"]
    binding = importer._load_record(importer._directory(workspace, "bindings"), request["binding_id"], workspace_id, "azure_binding")
    if not binding:
        _fail("original_binding_missing")
    binding = binding[1]
    capture = importer._load_record(importer._directory(workspace, "imports"), binding["request"]["import_id"], workspace_id, "azure_import")
    if not capture or not capture[1]["complete"] or capture[1]["record_sha256"] != binding["import_record_sha256"]:
        _fail("original_import_invalid")
    capture = capture[1]
    expected_target = {k: capture["request"][k] for k in ["connection_id", "organization", "project", "pbi_id", "task_ids"]}
    expected_target["observed_items"] = [{k: row["observation"][k] for k in ["item_id", "revision", "type", "parent_id"]} for row in capture["items"]]
    expected_delivery = {"workspace_id": workspace_id, "organization": expected_target["organization"], "project": expected_target["project"], "environment": "test", "pbi_id": 10, "item_id": 21}
    if binding["target"] != expected_target or record["target"] != expected_delivery or expected_target["pbi_id"] != 10 or 21 not in expected_target["task_ids"] or request["source_connection_id"] != expected_target["connection_id"]:
        _fail("original_target_invalid")
    if intent:
        source = intent[1]["source"]
        if intent[1]["binding_sha256"] != binding["record_sha256"] or source["plan_definition_sha256"] != binding["source"]["plan_definition_sha256"] or (source["plan_id"], source["plan_revision"]) != (binding["request"]["plan_id"], binding["request"]["plan_revision"]):
            _fail("original_source_invalid")
        baseline = intent[1]["baseline"]
        if baseline["kind"] == "import":
            observed = next(r["observation"] for r in capture["items"] if r["item_id"] == 21)
            if baseline != {"kind": "import", "record_id": capture["record_id"], "record_sha256": capture["record_sha256"], "revision": observed["revision"], "state": observed["state"]}:
                _fail("original_baseline_invalid")
    return intent[1] if intent else None, terminal[1] if terminal else None, binding, capture


def _identity(observation):
    return {key: observation.get(key) for key in sorted(IDENTITY_KEYS)}


def _projection(value, observation):
    history = value["fields"].get("System.History")
    return {"identity": _identity(observation), "revision": observation["revision"], "state": observation["state"], "summary_sha256": importer._hash(history) if isinstance(history, str) else None, "protected_fields": writer._protected(value, observation)}


def _validate_identity(identity, context, item_id, root_guid):
    if not isinstance(identity, dict) or set(identity) != IDENTITY_KEYS:
        _fail("reconciliation_projection_invalid")
    observation = {**identity, "revision": 1, "state": "verified", "title": "verified", "description": None, "acceptance_criteria": None, "priority": None}
    importer._validate_observation(observation, context, item_id)
    if item_id == 21 and identity["canonical_project_id"] is not None and identity["canonical_project_id"] != root_guid:
        _fail("reconciliation_projection_invalid")


def _validate_projection(value, context, root_guid):
    if not isinstance(value, dict) or set(value) != PROJECTION_KEYS or not importer._number(value["revision"]) or not importer._text(value["state"]) or (value["summary_sha256"] is not None and not writer._digest(value["summary_sha256"])):
        _fail("reconciliation_projection_invalid")
    _validate_identity(value["identity"], context, 21, root_guid)
    protected = value["protected_fields"]
    required = {"System.Description", "System.AssignedTo", "Microsoft.VSTS.Scheduling.RemainingWork", "Microsoft.VSTS.CMMI.Blocked"}
    if not isinstance(protected, dict) or set(protected) != {"fields", "parent_sha256"} or not isinstance(protected["fields"], dict) or not required.issubset(protected["fields"]) or protected["parent_sha256"] != importer._hash({k: value["identity"][k] for k in ["parent_id", "parent_relation", "canonical_project_id", "canonical_parent_url"]}):
        _fail("reconciliation_projection_invalid")
    for key, field in protected["fields"].items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_.]{1,256}", key) or (key not in required and "duedate" not in key.lower()) or not isinstance(field, dict) or set(field) != {"present", "sha256"} or type(field["present"]) is not bool or (not writer._digest(field["sha256"]) if field["present"] else field["sha256"] is not None):
            _fail("reconciliation_projection_invalid")


def _decision(original, terminal, current, applied, expected):
    if terminal and terminal["outcome"] in {"hold", "conflict", "rejected"}:
        return "retained_non_success", ["original_disposition_retained"]
    if not original or applied is None or current is None:
        return "unresolved", ["positive_proof_unavailable"]
    if applied["revision"] != expected or applied["state"] != original["candidate"]["proposed_state"] or applied["summary_sha256"] != importer._hash(original["candidate"]["summary"]) or applied["protected_fields"] != original["protected_fields"]:
        return "unresolved", ["full_delivery_proof_mismatch"]
    if current != applied:
        return "applied_remote_changed", ["historical_applied_current_changed"]
    return "confirmed_applied", ["full_delivery_proof_current"]


def _resume_ready(original, terminal, outcome, target, intents, terminals, recoveries):
    if not original or (terminal and terminal["outcome"] != "unknown") or outcome != "confirmed_applied":
        return False
    discharged = {original["record_id"]} | ancestry_before(original, intents, terminals, recoveries)
    for identity, (_, intent) in intents.items():
        if intent["target"] != target:
            continue
        if identity not in discharged and (identity not in terminals or terminals[identity][1]["outcome"] == "unknown"):
            return False
        if intent["baseline"]["kind"] == "success" and intent["baseline"]["record_id"] == original["record_id"]:
            return False
        if intent["baseline"]["kind"] == "recovery" and recoveries[intent["baseline"]["record_id"]][1]["request"]["report_id"] == original["record_id"]:
            return False
    return True


def _validate(value, workspace, workspace_id, intents, terminals):
    if not isinstance(value, dict) or set(value) != RECORD_KEYS or type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["kind"] != "reconciliation" or value["workspace_id"] != workspace_id:
        _fail("reconciliation_record_invalid")
    _request(value["request"])
    request = value["request"]
    if value["record_id"] != request["reconciliation_id"] or value["request_sha256"] != importer._hash(request) or value["record_sha256"] != importer._hash({k: v for k, v in value.items() if k != "record_sha256"}):
        _fail("reconciliation_record_invalid")
    for key in ["recorded_at", "verified_at"]:
        if value[key] is not None:
            try:
                if datetime.fromisoformat(value[key]).utcoffset() is None:
                    _fail("reconciliation_record_invalid")
            except (TypeError, ValueError):
                _fail("reconciliation_record_invalid")
    if value["recorded_at"] is None:
        _fail("reconciliation_record_invalid")
    if value["original_write_attempted"] is not None and type(value["original_write_attempted"]) is not bool:
        _fail("reconciliation_record_invalid")
    original, terminal, binding, capture = _original(workspace, workspace_id, request["report_id"], intents, terminals)
    record = original or terminal
    if request["binding_id"] != binding["record_id"] or request["source_connection_id"] != record["request"]["connection_id"] or value["target"] != record["target"] or value["intent_sha256"] != (original["record_sha256"] if original else None) or value["terminal_sha256"] != (terminal["record_sha256"] if terminal else None) or value["binding_sha256"] != binding["record_sha256"] or value["import_sha256"] != capture["record_sha256"] or value["original_outcome"] != (terminal["outcome"] if terminal else "unknown") or value["original_write_attempted"] != (terminal["remote_write_attempted"] if terminal else None):
        _fail("reconciliation_original_mismatch")
    source = value["source"]
    if not isinstance(source, dict) or set(source) != {"plan_id", "plan_revision", "plan_definition_sha256", "plan_snapshot_sha256", "observation_revision"} or (source["plan_id"], source["plan_revision"]) != (binding["request"]["plan_id"], binding["request"]["plan_revision"]) or source["plan_definition_sha256"] != binding["source"]["plan_definition_sha256"] or not writer._digest(source["plan_snapshot_sha256"]) or type(source["observation_revision"]) is not int or source["observation_revision"] != request["expected_observation_revision"]:
        _fail("reconciliation_source_invalid")
    expected = terminal["after"]["revision"] if terminal and terminal["outcome"] == "success" else original["before"]["revision"] + 1 if original else None
    if value["expected_applied_revision"] != expected or (expected is not None and type(value["expected_applied_revision"]) is not int):
        _fail("reconciliation_revision_invalid")
    phases = value["phases"]
    if not isinstance(phases, list) or len(phases) > 3 or type(value["network_attempted"]) is not bool or type(value["resume_ready"]) is not bool:
        _fail("reconciliation_record_invalid")
    if not phases and value["original_outcome"] not in {"hold", "rejected", "conflict"}:
        _fail("reconciliation_phases_invalid")
    allowed_order = ["root", "current", "revision"]
    for index, phase in enumerate(phases):
        if not isinstance(phase, dict) or set(phase) != {"phase", "outcome", "diagnostic_code", "network_attempted"} or phase["phase"] != allowed_order[index] or phase["outcome"] not in {"read_verified", "failed", "not_attempted"} or phase["diagnostic_code"] not in PHASE_CODES or type(phase["network_attempted"]) is not bool or (phase["outcome"] == "not_attempted") != (not phase["network_attempted"]) or (phase["outcome"] == "read_verified") != (phase["diagnostic_code"] == "read_verified") or (phase["outcome"] == "not_attempted" and (index != 0 or phase["diagnostic_code"] != "credential_unavailable")) or (phase["outcome"] == "failed" and phase["diagnostic_code"] == "credential_unavailable") or (index and phases[index - 1]["outcome"] != "read_verified"):
            _fail("reconciliation_phases_invalid")
    if value["network_attempted"] != any(p["network_attempted"] for p in phases):
        _fail("reconciliation_phases_invalid")
    context = capture["request"]
    root_identity = value["root_identity"]
    if root_identity is not None:
        _validate_identity(root_identity, context, 10, None)
    root_guid = root_identity["canonical_project_id"] if root_identity else None
    for name in ["current", "applied"]:
        if value[name] is not None:
            if root_identity is None:
                _fail("reconciliation_projection_invalid")
            _validate_projection(value[name], context, root_guid)
    if (root_identity is not None) != (bool(phases) and phases[0]["outcome"] == "read_verified") or (value["current"] is not None) != (len(phases) >= 2 and phases[1]["outcome"] == "read_verified"):
        _fail("reconciliation_phases_invalid")
    if value["applied"] is not None:
        if value["current"]["revision"] == expected:
            if len(phases) != 2 or value["historical_url"] is not None or value["applied"] != value["current"]:
                _fail("reconciliation_revision_invalid")
        elif len(phases) != 3 or phases[2]["outcome"] != "read_verified" or value["historical_url"] != value["applied"]["identity"]["canonical_item_url"] + "/revisions/" + str(expected):
            _fail("reconciliation_revision_invalid")
    elif value["historical_url"] is not None or (len(phases) == 3 and phases[2]["outcome"] == "read_verified"):
        _fail("reconciliation_revision_invalid")
    outcome, reasons = _decision(original, terminal, value["current"], value["applied"], expected)
    if value["outcome"] != outcome or value["reason_codes"] != reasons or value["resume_ready"] and (outcome != "confirmed_applied" or not original or terminal and terminal["outcome"] != "unknown") or (value["verified_at"] is not None) != (outcome in {"confirmed_applied", "applied_remote_changed"}):
        _fail("reconciliation_decision_invalid")


def load_records(workspace, workspace_id, intents, terminals):
    directory = importer._directory(workspace, "deliveries") / "reconciliations"
    try:
        directory.resolve().relative_to(workspace)
        paths = list(directory.glob("*.json"))
        if len(paths) > MAX_RECORDS:
            _fail("reconciliation_record_limit_exceeded")
        rows = {}
        for path in paths:
            path.resolve().relative_to(directory.resolve())
            value = read_json(path)
            _validate(value, workspace, workspace_id, intents, terminals)
            if value["record_id"] in rows:
                _fail("reconciliation_identity_ambiguous")
            rows[value["record_id"]] = (path, value)
        return rows
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, UnicodeError, RecursionError):
        _fail("reconciliation_record_invalid")


def _result(record, path, replayed):
    return {"schema_version": 1, "reconciliation_id": record["record_id"], "report_id": record["request"]["report_id"], "outcome": record["outcome"], "reason_codes": record["reason_codes"], "replayed": replayed, "network_attempted": False if replayed else record["network_attempted"], "captured_network_attempted": record["network_attempted"], "remote_write_attempted": False, "original_outcome": record["original_outcome"], "original_write_attempted": record["original_write_attempted"], "resume_ready": record["resume_ready"], "verified_at": record["verified_at"], "captured_at": record["recorded_at"], "after": {k: record["applied"][k] for k in ["revision", "state"]} if record["outcome"] in {"confirmed_applied", "applied_remote_changed"} else None, "phases": record["phases"], "output": str(path), "record_sha256": record["record_sha256"]}


def _read(profile, token, resource, context, item_id, root_guid=None, revision=None):
    try:
        value = writer._transport(profile, token, resource, detailed_read_errors=True)
        historical_url = None
        if revision is not None:
            suffix = "/revisions/" + str(revision)
            raw_url = value.get("url")
            if not isinstance(raw_url, str) or not raw_url.endswith(suffix) or type(value.get("rev")) is not int or value["rev"] != revision:
                _fail("revision_response_invalid")
            guid, found_id, canonical = importer._url_identity(raw_url[:-len(suffix)], context)
            if found_id != item_id or guid is not None and guid != root_guid:
                _fail("revision_response_invalid")
            historical_url = canonical + suffix
            value = copy.deepcopy(value)
            value["url"] = canonical
        observation = writer._observation(value, context, item_id, token, root_guid)
        return value, observation, historical_url
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        code = str(exc) if isinstance(exc, (RecoveryError, writer.WriterError)) and str(exc) in PHASE_CODES else "fresh_read_failed"
        _fail(code, network_attempted=True)


def reconcile(root: Path, workspace_id: str, request: dict):
    _request(request)
    request = copy.deepcopy(request)
    root = root.resolve()
    workspace = _workspace(root, workspace_id)
    profile = load_connection(root, workspace_id, request["connection_id"])
    if profile["environment"] != "test" or "read_work_item" not in profile["allowed_operations"] or not {10, 21}.issubset(profile["allowed_item_ids"]):
        _fail("reconciliation_read_scope_rejected")
    base = importer._directory(workspace, "deliveries", create=True)
    directory = base / "reconciliations"
    try:
        directory.resolve().relative_to(workspace)
        directory.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError, RuntimeError):
        _fail("reconciliation_directory_unavailable")
    with writer_lock(workspace / "work/plans/.records.lock"), writer_lock(base / ".deliveries.lock"):
        intents = writer._rows(base / "intents", workspace_id, "intent")
        terminals = writer._rows(base / "receipts", workspace_id, "terminal")
        rows = load_records(workspace, workspace_id, intents, terminals)
        writer._pairs(intents, terminals, rows)
        original, terminal, binding, capture = _original(workspace, workspace_id, request["report_id"], intents, terminals)
        original_record = original or terminal
        context = capture["request"]
        if request["binding_id"] != binding["record_id"] or request["source_connection_id"] != original_record["request"]["connection_id"] or profile["organization"] != context["organization"] or profile["project"] != context["project"]:
            _fail("reconciliation_source_scope_rejected")
        for connection_id in [request["source_connection_id"], original_record["request"]["source_connection_id"]]:
            related_profile = load_connection(root, workspace_id, connection_id)
            if related_profile["environment"] != "test" or related_profile["organization"] != context["organization"] or related_profile["project"] != context["project"] or "read_work_item" not in related_profile["allowed_operations"] or not {10, 21}.issubset(related_profile["allowed_item_ids"]):
                _fail("reconciliation_original_profile_invalid")
        existing = rows.get(request["reconciliation_id"])
        if existing:
            if existing[1]["request"] != request:
                _fail("reconciliation_identity_conflict")
            return _result(existing[1], existing[0], True)
        if len(rows) >= MAX_RECORDS or importer._target(directory, request["reconciliation_id"]).exists():
            _fail("reconciliation_capacity_unavailable")
        plan = importer._plan(workspace, workspace_id, binding["request"]["plan_id"], binding["request"]["plan_revision"], request["expected_observation_revision"], root)
        if importer._hash(plan_definition(plan)) != binding["source"]["plan_definition_sha256"]:
            _fail("reconciliation_definition_conflict")
        importer._mapping(plan, capture, binding["request"])
        source = {"plan_id": plan["plan_id"], "plan_revision": plan["plan_revision"], "plan_definition_sha256": importer._hash(plan_definition(plan)), "plan_snapshot_sha256": importer._hash(plan), "observation_revision": plan["observation_revision"]}
        expected = terminal["after"]["revision"] if terminal and terminal["outcome"] == "success" else original["before"]["revision"] + 1 if original else None
        record = {"schema_version": 1, "kind": "reconciliation", "workspace_id": workspace_id, "record_id": request["reconciliation_id"], "recorded_at": writer._now(), "request": request, "request_sha256": importer._hash(request), "target": original_record["target"], "original_outcome": terminal["outcome"] if terminal else "unknown", "original_write_attempted": terminal["remote_write_attempted"] if terminal else None, "intent_sha256": original["record_sha256"] if original else None, "terminal_sha256": terminal["record_sha256"] if terminal else None, "binding_sha256": binding["record_sha256"], "import_sha256": capture["record_sha256"], "source": source, "expected_applied_revision": expected, "root_identity": None, "current": None, "applied": None, "historical_url": None, "phases": [], "outcome": "unresolved", "reason_codes": [], "network_attempted": False, "resume_ready": False, "verified_at": None}
        if not terminal or terminal["outcome"] not in {"hold", "conflict", "rejected"}:
            token = writer.os.environ.get(profile["auth"]["env_var"])
            if not token or not token.isascii() or len(token) > 4096 or any(ord(c) < 32 or ord(c) == 127 for c in token):
                record["phases"].append({"phase": "root", "outcome": "not_attempted", "diagnostic_code": "credential_unavailable", "network_attempted": False})
            else:
                encoded = base64.b64encode((":" + token).encode("ascii")).decode("ascii")
                if token in json.dumps(request, ensure_ascii=False) or encoded in json.dumps(request, ensure_ascii=False):
                    _fail("reconciliation_credential_echo_rejected")
                for phase, resource, item_id in [("root", "workitems/10", 10), ("current", "workitems/21", 21), ("revision", "workitems/21/revisions/" + str(expected), 21)]:
                    if phase == "revision" and record["current"]["revision"] == expected:
                        record["applied"] = record["current"]
                        break
                    record["network_attempted"] = True
                    try:
                        root_guid = record["root_identity"]["canonical_project_id"] if record["root_identity"] else None
                        value, observation, historical_url = _read(profile, token, resource, context, item_id, root_guid, expected if phase == "revision" else None)
                        if phase == "root":
                            record["root_identity"] = _identity(observation)
                        else:
                            record["current" if phase == "current" else "applied"] = _projection(value, observation)
                            if phase == "revision": record["historical_url"] = historical_url
                        record["phases"].append({"phase": phase, "outcome": "read_verified", "diagnostic_code": "read_verified", "network_attempted": True})
                    except (ValueError, TypeError, KeyError, RecursionError) as exc:
                        code = str(exc) if isinstance(exc, RecoveryError) and str(exc) in PHASE_CODES else "fresh_read_failed"
                        record["phases"].append({"phase": phase, "outcome": "failed", "diagnostic_code": code, "network_attempted": True})
                        break
        record["outcome"], record["reason_codes"] = _decision(original, terminal, record["current"], record["applied"], expected)
        record["resume_ready"] = _resume_ready(original, terminal, record["outcome"], record["target"], intents, terminals, rows)
        if record["outcome"] in {"confirmed_applied", "applied_remote_changed"}:
            record["verified_at"] = writer._now()
        record["recorded_at"] = writer._now()
        try:
            sealed = importer._seal(record)
            _validate(sealed, workspace, workspace_id, intents, terminals)
            path = importer._save(directory, sealed)
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            _fail("reconciliation_persistence_failed", network_attempted=record["network_attempted"])
        return _result(sealed, path, False)


def ancestry_before(intent, intents, terminals, recoveries):
    """Traverse every explicit success/recovery edge without selecting another chain."""
    resolved, visited = set(), set()
    while True:
        report_id = intent["record_id"]
        if report_id in visited or len(visited) >= MAX_RECORDS:
            _fail("delivery_ancestry_cycle")
        visited.add(report_id)
        baseline = intent["baseline"]
        if baseline["kind"] == "success":
            predecessor = baseline["record_id"]
            if predecessor not in intents or predecessor not in terminals or terminals[predecessor][1]["outcome"] != "success":
                _fail("delivery_ancestry_missing")
            intent = intents[predecessor][1]
        elif baseline["kind"] == "recovery":
            if baseline["record_id"] not in recoveries:
                _fail("delivery_ancestry_missing")
            proof = recoveries[baseline["record_id"]][1]
            origin = proof["request"]["report_id"]
            if origin not in intents:
                _fail("delivery_ancestry_missing")
            resolved.add(origin)
            intent = intents[origin][1]
        else:
            break
    return resolved


def ancestry(report_id, intents, terminals, recoveries):
    if report_id not in intents or report_id not in terminals or terminals[report_id][1]["outcome"] != "success":
        _fail("delivery_ancestry_missing")
    return ancestry_before(intents[report_id][1], intents, terminals, recoveries)


def eligible(proof, intents, terminals, recoveries):
    origin = proof["request"]["report_id"]
    original = intents.get(origin)
    terminal = terminals.get(origin)
    return proof["resume_ready"] and _resume_ready(original[1] if original else None, terminal[1] if terminal else None, proof["outcome"], proof["target"], intents, terminals, recoveries)


def inspect_status(root: Path, workspace_id: str, report_id: str):
    if not importer._id(report_id):
        _fail("report_identity_invalid")
    workspace = _workspace(root.resolve(), workspace_id)
    base = importer._directory(workspace, "deliveries")
    with writer_lock(base / ".deliveries.lock"):
        intents, terminals = writer._rows(base / "intents", workspace_id, "intent"), writer._rows(base / "receipts", workspace_id, "terminal")
        rows = load_records(workspace, workspace_id, intents, terminals)
        writer._pairs(intents, terminals, rows)
        original, terminal, _, _ = _original(workspace, workspace_id, report_id, intents, terminals)
        known = terminal["outcome"] if terminal else "unknown"
        last, receipt_recorded_at = None, None
        selected = report_id if known == "success" else (original or terminal)["request"].get("previous_report_id")
        if selected is not None:
            predecessor = terminals.get(selected)
            if not predecessor or predecessor[1]["outcome"] != "success":
                _fail("delivery_ancestry_missing")
            ancestry(selected, intents, terminals, rows)
            receipt_recorded_at = predecessor[1]["recorded_at"]
            last = {"report_id": selected, "verified_at": None, "receipt_recorded_at": receipt_recorded_at, **predecessor[1]["after"]}
        elif (original or terminal)["request"].get("previous_reconciliation_id") is not None:
            proof = rows[(original or terminal)["request"]["previous_reconciliation_id"]][1]
            last = {"report_id": proof["request"]["report_id"], "verified_at": proof["verified_at"], "receipt_recorded_at": None, **{k: proof["applied"][k] for k in ["revision", "state"]}}
        available = [{"reconciliation_id": identity, "outcome": row[1]["outcome"], "captured_resume_ready": row[1]["resume_ready"], "resume_ready": eligible(row[1], intents, terminals, rows), "verified_at": row[1]["verified_at"]} for identity, row in sorted(rows.items()) if row[1]["request"]["report_id"] == report_id]
        descendants = []
        for identity, (_, intent) in sorted(intents.items()):
            baseline = intent["baseline"]
            parent = baseline["record_id"] if baseline["kind"] == "success" else rows[baseline["record_id"]][1]["request"]["report_id"] if baseline["kind"] == "recovery" else None
            if parent == report_id:
                descendants.append({"report_id": identity, "outcome": terminals[identity][1]["outcome"] if identity in terminals else "unknown"})
        discharged = ancestry(report_id, intents, terminals, rows) if known == "success" else set()
        other_unknown = [identity for identity, (_, intent) in sorted(intents.items()) if intent["target"] == (original or terminal)["target"] and identity not in discharged and identity != report_id and (identity not in terminals or terminals[identity][1]["outcome"] == "unknown")]
        guidance = "inspect_explicit_descendant_report" if descendants else "investigate_other_unresolved_report" if other_unknown else "new_report_with_previous_report_id_and_new_observation" if known == "success" else "select_confirmed_reconciliation_and_new_observation" if any(p["resume_ready"] for p in available) else "user_conflict_investigation" if known in {"unknown", "conflict"} else "correct_preconditions_and_create_explicit_new_report"
        return {"schema_version": 1, "report_id": report_id, "original_outcome": known, "original_write_attempted": terminal["remote_write_attempted"] if terminal else None, "pending": known != "success", "needs_resolution": known in {"unknown", "conflict"} or bool(other_unknown), "last_success": last, "receipt_recorded_at": receipt_recorded_at, "reconciliations": available, "descendants": descendants, "other_unresolved_reports": other_unknown, "resume_guidance": guidance, "network_attempted": False, "remote_write_attempted": False}


def main(argv=None):
    parser = _SafeParser(description="Explicit read-only delivery status/reconciliation; never retries a PATCH")
    parser.add_argument("action", choices=["status", "reconcile"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--report-id")
    try:
        args = parser.parse_args(argv)
        if args.action == "status" and args.report_id and args.input is None:
            result = inspect_status(args.root, args.workspace_id, args.report_id)
        elif args.action == "reconcile" and args.input is not None and args.report_id is None:
            result = reconcile(args.root, args.workspace_id, read_json(args.input))
        else:
            _fail("arguments_invalid")
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RuntimeError, RecursionError) as exc:
        result = {"schema_version": 1, "outcome": "unresolved", "reason_codes": ["reconciliation_rejected"], "resume_ready": False, "network_attempted": getattr(exc, "network_attempted", False), "remote_write_attempted": False}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 1 if result.get("outcome") == "unresolved" else 0


if __name__ == "__main__":
    raise SystemExit(main())
