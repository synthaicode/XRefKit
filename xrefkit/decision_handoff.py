"""Durable, offline decision handoff between two registered Prompt Flow runs."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from xrefkit.hashing import sha256_file
from xrefkit.skillrun import (
    _log_field, _observation_events, _parse_artifacts, _parse_work_items,
    _section_status, _validate_observation_log,
)


TRANSITIONS = {
    "create": (None, "prepared"),
    "send": ("prepared", "sent"),
    "receive": ("sent", "received"),
    "route": ("received", "waiting"),
    "return": ("waiting", "returned"),
    "acknowledge": ("returned", "acknowledged"),
    "assess": ("acknowledged", "assessed"),
}
PM_OPERATIONS = {"receive", "route", "return"}
REVISION_FIELDS = ("work_item_id", "work_revision", "policy_revision", "policy_sha256")
REQUEST_FIELDS = (
    *REVISION_FIELDS, "source_run_id", "pm_work_item_id", "pm_skill_id",
    "subject", "evidence", "source_artifact_id", "source_artifact_sha256", "unknowns",
)
RESUME_CHECKS = {
    "current_design", "required_approval", "impact_review",
    "current_acceptance", "hold_resolution", "work_start_authority",
}


def _json(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _require_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    return value


def _references(values, label, *, allow_empty=False):
    if not isinstance(values, list) or (not values and not allow_empty):
        raise ValueError(f"{label} must be a list of references")
    for value in values:
        _require_text(value, label)


def _within(root, value):
    path = (root / _require_text(value, "path")).resolve()
    if not path.is_relative_to(root):
        raise ValueError("decision handoff input must remain within --root")
    return path


def _opened(path):
    text, error = _validate_observation_log(path)
    if error:
        raise ValueError("; ".join(error.errors))
    return text


def _registered_run(root, parent_path, run_path):
    parent = _opened(_within(root, parent_path))
    path = _within(root, run_path)
    child = _opened(path)
    parent_id = _log_field(parent, "run_id")
    run = {key: _log_field(child, key) for key in
           ("run_id", "skill_id", "parent_run_id", "flow_id", "root_run_id", "work_item_id")}
    if (not all(run.values()) or run["parent_run_id"] != parent_id
            or run["flow_id"] != (_log_field(parent, "flow_id") or parent_id)
            or run["root_run_id"] != (_log_field(parent, "root_run_id") or parent_id)
            or run["work_item_id"] not in {item["item_id"] for item in _parse_work_items(parent)}
            or not any(
                event.get("event") == "child_run.started"
                and all(event.get(k) == run[k] for k in (
                    "parent_run_id", "flow_id", "root_run_id", "work_item_id", "skill_id",
                ))
                and event.get("child_run_id") == run["run_id"]
                and isinstance(event.get("child_log"), str)
                and _within(root, event["child_log"]) == path
                for event in _observation_events(parent)
            )):
        raise ValueError("decision handoff requires a registered child Run in this Prompt Flow")
    return run, child, parent


def _request(data, run, child, parent):
    fields = set(REQUEST_FIELDS)
    if "request_type" in data:
        fields.update({"request_type", "resolution", "engineering_decision_id"})
    elif "engineering_decision_id" in data:
        fields.add("engineering_decision_id")
    if set(data) != fields:
        raise ValueError("invalid decision request fields")
    for key in set(REQUEST_FIELDS) - {"evidence", "unknowns"}:
        _require_text(data[key], key)
    _references(data["evidence"], "evidence")
    _references(data["unknowns"], "unknowns")
    if len(set(data["unknowns"])) != len(data["unknowns"]):
        raise ValueError("unknown IDs must be unique")
    if not re.fullmatch("[a-f0-9]{64}", data["policy_sha256"]):
        raise ValueError("policy_sha256 must be a SHA-256 digest")
    if data["source_run_id"] != run["run_id"]:
        raise ValueError("decision request must come from its source Run")
    if (data["pm_work_item_id"] == run["work_item_id"]
            or data["pm_work_item_id"] not in {item["item_id"] for item in _parse_work_items(parent)}):
        raise ValueError("decision request requires a distinct receiving Work Item in the parent")
    if not any(item["item_id"] == data["work_item_id"] and item["criterion"]
               and item["status"] in {"pending", "in_progress", "blocked"}
               for item in _parse_work_items(child)):
        raise ValueError("decision request requires an affected open Work Item in the source Run")


def _check_finding(root, request, child):
    finding = next((artifact for artifact in _parse_artifacts(child)
                    if artifact["artifact_id"] == request["source_artifact_id"]
                    and artifact["item_id"] == request["work_item_id"]
                    and artifact["kind"] in {"output", "evidence"} and artifact["status"] == "done"), None)
    if finding is None:
        raise ValueError("decision request requires a recorded finding artifact for the Work Item")
    path = _within(root, finding["target"])
    if sha256_file(path).removeprefix("sha256:") != request["source_artifact_sha256"]:
        raise ValueError("finding artifact does not match the request digest")
    if "engineering_decision_id" in request:
        record = json.loads(path.read_text(encoding="utf-8-sig"))
        if (not isinstance(record, dict) or record.get("schema") != "brownfield.design_finding/v1"
                or any(record.get(key) != request[key] for key in (
                    "engineering_decision_id", "source_run_id", "work_item_id", "work_revision",
                ))):
            raise ValueError("finding must bind the engineering decision and source Work Item revision")


def _check_approval(request_id, request, decision, route, current):
    approval = current.get("approval")
    expected = {k: request[k] for k in REVISION_FIELDS}
    expected.update({
        "request_id": request_id, "decision_sha256": _digest(decision),
        "authority": route["owner"], "status": "approved",
        "reference": decision["approval_ref"],
    })
    if not route["owner"] or route["owner"] != current.get("decision_owner") or approval != expected:
        raise ValueError("decision lacks current, scoped approval from the routed authority")


def _transition_data(operation, request_id, data, history, current):
    if operation in {"send", "receive", "acknowledge"} and data:
        raise ValueError(f"{operation} takes no transition data")
    if operation == "cancel":
        if set(data) != {"reason"}:
            raise ValueError("cancel requires a reason")
        _require_text(data["reason"], "reason")
    if operation == "route":
        if set(data) != {"owner", "reason", "evidence"}:
            raise ValueError("route requires owner, reason and evidence")
        if data["owner"] is not None:
            _require_text(data["owner"], "owner")
        if data["owner"] != current.get("decision_owner"):
            raise ValueError("route owner does not match current authority")
        _require_text(data["reason"], "reason")
        _references(data["evidence"], "route evidence")
    if operation == "return":
        if data.get("disposition") == "held" and set(data) == {"disposition", "reason", "evidence"}:
            _require_text(data["reason"], "hold reason")
        elif data.get("disposition") == "decided" and set(data) == {
            "disposition", "decision", "approval_ref", "evidence",
        }:
            _require_text(data["decision"], "decision")
            _require_text(data["approval_ref"], "approval_ref")
            _check_approval(request_id, history["create"]["data"], data, history["route"]["data"], current)
        else:
            raise ValueError("return requires either a supported hold or a scoped approved decision")
        _references(data["evidence"], "return evidence")
    if operation in {"acknowledge", "assess"}:
        decision = history["return"]["data"]
        request = history["create"]["data"]
        if decision["disposition"] == "decided" and (operation == "acknowledge" or data.get("outcome") == "resume"):
            _check_approval(request_id, request, decision, history["route"]["data"], current)
        if operation == "assess":
            if (set(data) - {"engineering_decision_id"} != {"outcome", "evidence", "resolved_unknowns"}
                    or data["outcome"] not in ("resume", "hold")):
                raise ValueError("assessment requires outcome, evidence and resolved_unknowns")
            _references(data["evidence"], "assessment evidence")
            resolved = data["resolved_unknowns"]
            if not isinstance(resolved, dict) or set(resolved) - set(request["unknowns"]):
                raise ValueError("assessment references unknown IDs outside this request")
            for reference in resolved.values():
                _require_text(reference, "unknown resolution evidence")
            checks = current.get("resume_checks", {})
            if data["outcome"] == "resume" and (
                decision["disposition"] != "decided" or set(resolved) != set(request["unknowns"])
                or not isinstance(checks, dict) or any(checks.get(key) is not True for key in RESUME_CHECKS)
            ):
                raise ValueError("resume prerequisites are incomplete; record hold")


def apply_transition(root: Path, journal: Path, command: dict) -> dict:
    """Apply a host-verified transition; the host owns authority and current revisions."""
    from xrefkit import unknown_resolution

    root = root.resolve()
    journal = _within(root, str(journal))
    if (not isinstance(command, dict) or set(command) != {
        "schema_version", "request_id", "action", "parent_log", "run_log", "data", "current",
    } or type(command["schema_version"]) is not int or command["schema_version"] != 1):
        raise ValueError("unsupported decision handoff command schema")
    request_id = _require_text(command["request_id"], "request_id")
    operation = _require_text(command["action"], "action")
    if operation not in TRANSITIONS and operation != "cancel":
        raise ValueError("unsupported decision handoff action")
    data, current = command["data"], command["current"]
    if not isinstance(data, dict) or not isinstance(current, dict):
        raise ValueError("data and current must be objects")
    with closing(sqlite3.connect(journal, timeout=5)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS decision_handoff_event (
            request_id TEXT, sequence INTEGER, action TEXT, receipt TEXT,
            PRIMARY KEY (request_id, sequence), UNIQUE (request_id, action)
        )""")
        events = [json.loads(row[0]) for row in db.execute(
            "SELECT receipt FROM decision_handoff_event WHERE request_id = ? ORDER BY sequence", (request_id,),
        )]
        history = {event["action"]: event for event in events}
        run, child, parent = _registered_run(root, command["parent_log"], command["run_log"])
        request = history["create"]["data"] if history else data
        unknown = unknown_resolution.is_request(request)
        if operation == "create" and "request_type" in request and not unknown:
            raise ValueError("unsupported decision request type")
        if unknown and journal != _within(root, unknown_resolution.JOURNAL):
            raise ValueError("UNKNOWN resolution requires the canonical Decision Handoff journal")
        if operation != "cancel" and history and any(current.get(k) != request[k] for k in REVISION_FIELDS):
            raise ValueError("request does not match current Work Item and design policy revisions")
        if operation in history:
            prior = history[operation]
            if prior["run"] != run or _json(prior["data"]) != _json(data):
                raise ValueError("same request/action has conflicting contents or participant")
            return {"receipt": prior, "state": events[-1]["state"], "reused": True}

        state = events[-1]["state"] if events else None
        required, next_state = TRANSITIONS.get(operation, (state, "cancelled"))
        if state != required or (operation == "cancel" and state not in {"prepared", "sent", "received", "waiting"}):
            raise ValueError(f"cannot {operation} from {state}")
        if operation != "cancel" and _section_status(child, "Closure Gate") != "pending":
            raise ValueError("decision handoff requires an open participant Run")
        if operation == "create":
            _request(data, run, child, parent)
        source = history["create"]["run"] if history else run
        if operation == "create" and any(current.get(k) != request[k] for k in REVISION_FIELDS):
            raise ValueError("request does not match current Work Item and design policy revisions")
        if operation in PM_OPERATIONS:
            if (run["flow_id"] != source["flow_id"] or run["root_run_id"] != source["root_run_id"]
                    or run["parent_run_id"] != source["parent_run_id"] or run["run_id"] == source["run_id"]
                    or run["work_item_id"] != request["pm_work_item_id"] or run["skill_id"] != request["pm_skill_id"]
                    or (operation != "receive" and run != history["receive"]["run"])):
                raise ValueError("transition must come from the designated PM recipient Run")
        elif run != source:
            raise ValueError("transition must come from the original source Run")
        if operation in {"create", "send"}:
            from xrefkit.engineering_decision import require_handoff_decision, require_unknown_decision

            _check_finding(root, request, child)
            if unknown:
                require_unknown_decision(root, request)
                if operation == "create":
                    unknown_resolution.check_overlap(db, request)
            else:
                require_handoff_decision(root, request["work_item_id"], request["work_revision"], request["source_run_id"],
                                         request.get("engineering_decision_id"))
        if unknown and operation in {"route", "return", "acknowledge", "assess"}:
            unknown_resolution.check_transition(root, operation, request_id, data, history, current)
        else:
            _transition_data(operation, request_id, data, history, current)
        if operation == "assess" and data["outcome"] == "resume":
            from xrefkit.engineering_decision import require_handoff_resume

            require_handoff_resume(root, request["work_item_id"], request["work_revision"],
                                   request_id, data.get("engineering_decision_id"))
        receipt = {
            "schema_version": 1, "request_id": request_id, "action": operation,
            "state": next_state, "sequence": len(events) + 1, "run": run,
            "data": data, "verified_context": current, "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        db.execute("INSERT INTO decision_handoff_event VALUES (?, ?, ?, ?)",
                   (request_id, receipt["sequence"], operation, _json(receipt)))
    return {"receipt": receipt, "state": next_state, "reused": False}


def cmd_decision_handoff(args) -> int:
    root = Path(args.root).resolve()
    try:
        journal = _within(root, args.journal)
        if args.inspect:
            with closing(sqlite3.connect(journal.as_uri() + "?mode=ro", uri=True)) as db:
                receipts = [json.loads(row[0]) for row in db.execute(
                    "SELECT receipt FROM decision_handoff_event WHERE request_id = ? ORDER BY sequence",
                    (args.inspect,),
                )]
            if not receipts:
                raise ValueError("decision request not found")
            result = {"state": receipts[-1]["state"], "receipts": receipts}
        else:
            command = json.loads(_within(root, args.input).read_text(encoding="utf-8-sig"))
            result = apply_transition(root, journal, command)
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0
