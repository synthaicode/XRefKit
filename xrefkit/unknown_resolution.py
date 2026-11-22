"""Structured UNKNOWN requests in the existing Decision Handoff journal."""

from contextlib import closing
from datetime import datetime, timezone
import json
import sqlite3

from xrefkit.decision_handoff import _digest, _references, _require_text, _within


JOURNAL = ".xrefkit-decision-handoff.sqlite"
REQUEST_TYPE = "UNKNOWN_RESOLUTION"
ROLES = {
    "MISSING_INFORMATION": "investigator",
    "MISSING_EVIDENCE": "verifier",
    "DESIGN_UNRESOLVED": None,
    "AUTHORITY_REQUIRED": "decision_authority",
    "ENVIRONMENT_BLOCKED": "environment_owner",
    "KNOWLEDGE_GAP": "knowledge_owner",
}
RESPONSES = {
    "EVIDENCE_PROVIDED", "INFORMATION_PROVIDED", "DESIGN_DIRECTION",
    "RISK_ACCEPTED", "REJECTED", "CANNOT_RESOLVE",
}


def is_request(request):
    return request.get("request_type") == REQUEST_TYPE


def _fields(value, names, label):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError(f"invalid UNKNOWN {label} fields")


def _time(value):
    timestamp = datetime.fromisoformat(_require_text(value, "UNKNOWN timestamp"))
    if timestamp.utcoffset() is None:
        raise ValueError("UNKNOWN timestamp requires an explicit timezone")
    return timestamp


def _files(root, files):
    from xrefkit.engineering_decision import _verified_file

    if not isinstance(files, list) or not files:
        raise ValueError("UNKNOWN response requires pinned human records")
    for file in files:
        _fields(file, "path sha256", "response evidence")
        _verified_file(root, file["path"], file["sha256"])


def check_request(request, entry):
    context = request["resolution"]
    _fields(context, "candidate reference_set_sha256 checklist_revision group items", "request")
    proposal = entry["proposal"]
    selection = entry["reference_set"]["checklist"]
    if (proposal["candidate"] is None or context["candidate"] != proposal["candidate"]
            or context["reference_set_sha256"] != proposal["reference_set_sha256"]
            or context["checklist_revision"] != selection["revision"]):
        raise ValueError("UNKNOWN request does not bind the evaluated candidate and checklist")
    group = context["group"]
    _fields(group, "cause owner environment authority", "group")
    for value in group.values():
        _require_text(value, "UNKNOWN group scope")
    items = context["items"]
    if not isinstance(items, dict) or set(items) != set(request["unknowns"]):
        raise ValueError("UNKNOWN request must list its original Check IDs")
    roles = set()
    for check_id, item in items.items():
        _fields(item, "classification question reason related_xids required_action expected_evidence acceptance_criteria", "item")
        result = proposal["checklist"]["results"].get(check_id, {})
        check = selection["checks"].get(check_id, {})
        if (result.get("result") != "UNKNOWN" or item["reason"] != result["reason"]
                or item["question"] != check["question"] or item["related_xids"] != result["references"]):
            raise ValueError(f"{check_id} must bind an actual UNKNOWN, question, reason and evaluated XIDs")
        role = ROLES.get(_require_text(item["classification"], "UNKNOWN classification"))
        if role is None:
            raise ValueError(f"{check_id} must be classified for external action; rework stays in Brownfield")
        roles.add(role)
        for field in item.keys() - {"related_xids"}:
            _require_text(item[field], "UNKNOWN item")
    if len(roles) != 1:
        raise ValueError("UNKNOWN requests require a common routing role")


def check_transition(root, operation, request_id, data, history, current):
    request = history["create"]["data"]
    context = request["resolution"]
    group = context["group"]
    if operation == "route":
        _fields(data, "owner role due_at blocked_scope restart_condition reason evidence", "route")
        role = ROLES[next(iter(context["items"].values()))["classification"]]
        if (data["owner"] != group["owner"] or data["owner"] != current.get("decision_owner")
                or data["role"] != role or data["blocked_scope"] != request["work_item_id"]):
            raise ValueError("UNKNOWN route must match the scoped Work Item, verified owner and routing role")
        _time(data["due_at"])
        _references(data["evidence"], "UNKNOWN route evidence")
        _require_text(data["reason"], "UNKNOWN route reason")
        _require_text(data["restart_condition"], "UNKNOWN restart condition")
    if operation in {"return", "acknowledge"}:
        response = data if operation == "return" else history["return"]["data"]
        _fields(response, "request_id candidate responses", "return")
        if response["request_id"] != request_id or response["candidate"] != context["candidate"]:
            raise ValueError("UNKNOWN return must bind the request and original candidate")
        items = response["responses"]
        if not isinstance(items, dict) or set(items) != set(request["unknowns"]):
            raise ValueError("UNKNOWN return must report each original Check ID")
        for item in items.values():
            _fields(item, "outcome actor authority responded_at action evidence unresolved", "response")
            for name in ("outcome", "actor", "authority", "action"):
                _require_text(item[name], f"UNKNOWN {name}")
            if item["outcome"] not in RESPONSES:
                raise ValueError("unsupported UNKNOWN response outcome")
            if item["outcome"] in {"DESIGN_DIRECTION", "RISK_ACCEPTED"} and (
                item["authority"] != group["authority"] or item["authority"] != current.get("resolution_authority")
            ):
                raise ValueError("UNKNOWN response lacks the requested decision authority")
            if _time(item["responded_at"]) > datetime.now(timezone.utc):
                raise ValueError("UNKNOWN response timestamp is in the future")
            _files(root, item["evidence"])
            _references(item["unresolved"], "UNKNOWN remaining issues",
                        allow_empty=item["outcome"] not in {"REJECTED", "CANNOT_RESOLVE", "RISK_ACCEPTED"})
        if current.get("human_response_sha256") != _digest(response):
            raise ValueError("UNKNOWN return requires exact host-verified human response")
    if operation == "acknowledge" and data:
        raise ValueError("acknowledge takes no transition data")
    if operation == "assess":
        _fields(data, "outcome evidence resolved_unknowns", "assessment")
        if data["outcome"] != "hold" or data["resolved_unknowns"] != {}:
            raise ValueError("UNKNOWN handoff assessment stays held pending an independent engineering evaluation")
        _references(data["evidence"], "UNKNOWN assessment evidence")


def _requests(db, work_item_id, revision):
    # The create receipt owns identity. Later receipts only advance its state.
    return db.execute("""
        SELECT first.request_id, first.receipt, last.receipt
        FROM decision_handoff_event AS first
        JOIN decision_handoff_event AS last ON last.request_id = first.request_id
        WHERE first.action = 'create'
          AND json_extract(first.receipt, '$.data.request_type') = ?
          AND json_extract(first.receipt, '$.data.work_item_id') = ?
          AND json_extract(first.receipt, '$.data.work_revision') = ?
          AND last.sequence = (SELECT MAX(sequence) FROM decision_handoff_event WHERE request_id = first.request_id)
        ORDER BY first.request_id
    """, (REQUEST_TYPE, work_item_id, revision))


def check_overlap(db, request):
    context = request["resolution"]
    for _, first, last in _requests(db, request["work_item_id"], request["work_revision"]):
        prior = json.loads(first)["data"]
        if json.loads(last)["state"] == "cancelled" or prior["engineering_decision_id"] != request["engineering_decision_id"]:
            continue
        if set(prior["unknowns"]).intersection(request["unknowns"]):
            raise ValueError("UNKNOWN Check ID already belongs to a request; reuse its request ID")
        previous = prior["resolution"]
        if (previous["group"] == context["group"]
                and next(iter(previous["items"].values()))["classification"]
                == next(iter(context["items"].values()))["classification"]):
            raise ValueError("UNKNOWN items with the same cause and routing scope must be grouped")


def reevaluation_inputs(root, work_item_id, revision):
    path = _within(root, JOURNAL)
    if not path.is_file():
        return {}
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db, db:
        db.execute("BEGIN")
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name = 'decision_handoff_event'").fetchone():
            return {}
        inputs = {}
        for request_id, first, last in _requests(db, work_item_id, revision):
            state = json.loads(last)["state"]
            if state == "cancelled":
                continue
            source = json.loads(first)["data"]["engineering_decision_id"]
            if state not in {"acknowledged", "assessed"}:
                inputs[request_id] = {"source_decision_id": source, "state": state}
                continue
            row, = db.execute("SELECT receipt FROM decision_handoff_event WHERE request_id = ? AND action = 'return'",
                              (request_id,)).fetchone()
            inputs[request_id] = {"source_decision_id": source, "return": json.loads(row)["data"]}
        return inputs


def check_reevaluation(root, prepared):
    context = prepared["context"]
    inputs = reevaluation_inputs(root, prepared["work_item_id"], context["work"]["revision"])
    if any("state" in item for item in inputs.values()):
        raise ValueError("UNKNOWN resolution is awaiting a return or source acknowledgment")
    if inputs and not prepared.get("checklist_enabled"):
        raise ValueError("UNKNOWN resolution requires checklist reevaluation")
    if inputs != prepared.get("unknown_resolution_inputs", {}):
        raise ValueError("UNKNOWN resolution input changed; prepare a new decision and reevaluate")
    for item in inputs.values():
        for response in item["return"]["responses"].values():
            _files(root, response["evidence"])
