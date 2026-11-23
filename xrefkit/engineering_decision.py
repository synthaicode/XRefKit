"""Version-bound engineering decisions within a trust-managed local project root."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from xrefkit import decision_checklist, principle_discovery
from xrefkit.xref import _extract_xid


POLICY_FILE = "engineering-decision-policy.json"
JOURNAL_FILE = ".xrefkit-engineering-decisions.sqlite"
BOUND_EVENT = "engineering_decision.bound"
PROTECTED_ACTIONS = {"manufacturing", "test_design", "retry"}
CLASSIFICATIONS = {"DETERMINED", "CONDITIONAL", "BLOCKED", "ESCALATION_REQUIRED"}


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _digest(value):
    return hashlib.sha256(_encode(value).encode("utf-8")).hexdigest()


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    return value


def _object(value, fields, name):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"invalid {name} fields")
    return value


def _keys(value, name):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a nonempty list")
    if len({_text(item, name) for item in value}) != len(value):
        raise ValueError(f"{name} must be unique")
    return value


def _path(root, value):
    path = (root / _text(value, "path")).resolve()
    if not path.is_relative_to(root):
        raise ValueError("engineering decision input must remain within --root")
    return path


def _read_json(path):
    def pairs(entries):
        result = dict(entries)
        if len(result) != len(entries):
            raise ValueError("duplicate JSON key")
        return result

    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=pairs)


def _policy(root, *, required=True):
    path = _path(root, POLICY_FILE)
    if not path.exists() and not required:
        return None
    policy = _read_json(path)
    fields = {"schema_version", "work_items", "catalog", "reviews", "approvals"}
    if isinstance(policy, dict):
        for name in ("discovery", "checklist"):
            if name in policy:
                fields.add(name)
                if type(policy[name]) is not bool:
                    raise ValueError(f"engineering {name} policy must be true or false")
    _object(policy, fields, "engineering policy")
    if type(policy["schema_version"]) is not int or policy["schema_version"] != 1:
        raise ValueError("unsupported engineering decision policy version")
    if any(not isinstance(policy[k], dict) for k in ("work_items", "catalog", "reviews", "approvals")):
        raise ValueError("engineering policy indexes must be JSON objects")
    if policy.get("checklist") and not policy.get("discovery"):
        raise ValueError("engineering checklist requires principle discovery")
    return policy


def _work(policy, work_item_id):
    work = _object(policy["work_items"].get(work_item_id), {
        "revision", "actions", "required_xids", "required_checks", "reviewers", "approver",
    }, "registered engineering Work Item")
    _text(work["revision"], "Work Item revision")
    if set(_keys(work["actions"], "actions")) - (PROTECTED_ACTIONS | {"draft"}):
        raise ValueError("unsupported engineering action")
    for name in ("required_xids", "required_checks", "reviewers"):
        _keys(work[name], name)
    if work["approver"] is not None:
        _text(work["approver"], "approver")
    return work


def _verified_file(root, path, expected):
    actual_path = _path(root, path)
    raw = actual_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"engineering evidence digest mismatch: {path}")
    return raw


def _context(root, policy, work_item_id, discovery=None):
    work = _work(policy, work_item_id)
    references = {}
    unresolved = {}
    for xid in work["required_xids"] if discovery is None else discovery["matches"]:
        if xid not in policy["catalog"]:
            unresolved[xid] = "XID is absent from the current catalog"
            continue
        entry = policy["catalog"][xid]
        fields = {"kind", "path", "revision", "sha256"}
        if isinstance(entry, dict) and "discovery" in entry:
            fields.add("discovery")
        ref = _object(entry, fields, "XID reference")
        _text(ref["revision"], "XID revision")
        if ref["kind"] not in ("global", "project"):
            raise ValueError("engineering references must be global or project")
        try:
            raw = _verified_file(root, ref["path"], ref["sha256"])
            if _extract_xid(raw.decode("utf-8-sig")) != xid:
                raise ValueError("reference does not resolve to the expected XID")
        except (OSError, ValueError) as exc:
            unresolved[xid] = str(exc)
            continue
        references[xid] = ref if discovery is not None else {k: v for k, v in ref.items() if k != "discovery"}
    return {"work": work, "references": references, "unresolved_xids": unresolved}


def _store(root, *, readonly=False):
    path = _path(root, JOURNAL_FILE)
    database = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) if readonly else sqlite3.connect(path)
    database.row_factory = sqlite3.Row
    return database


def _read_decision(db, decision_id):
    row = db.execute("SELECT * FROM engineering_decision WHERE id = ?", (decision_id,)).fetchone()
    if row is None:
        raise ValueError("engineering decision has not been prepared")
    entry = {key: json.loads(row[key]) if row[key] is not None else None
             for key in ("prepared", "proposal")}
    if db.execute("SELECT 1 FROM sqlite_master WHERE name = 'engineering_reference_set' AND type = 'table'").fetchone():
        state = db.execute("SELECT * FROM engineering_reference_set WHERE id = ?", (decision_id,)).fetchone()
        if state is not None:
            entry.update(searched_at=state["searched_at"], superseded_by=state["superseded_by"],
                         reference_set=json.loads(state["resolution"]) if state["resolution"] else None)
    return entry


def _prepare(root, policy, command, db):
    from xrefkit.unknown_resolution import reevaluation_inputs, check_reevaluation
    from xrefkit.skillrun import _log_field, _validate_observation_log

    fields = {"action", "decision_id", "work_item_id", "run_log", "question", "proposer"}
    if "handoff_request_id" in command:
        fields.add("handoff_request_id")
        _text(command["handoff_request_id"], "Handoff request ID")
    if policy.get("discovery", False):
        fields.add("decision_context")
        if "supersedes" in command:
            fields.add("supersedes")
            _text(command["supersedes"], "superseded decision ID")
    _object(command, fields, "prepare command")
    work_item_id = _text(command["work_item_id"], "Work Item ID")
    _text(command["question"], "decision question")
    _text(command["proposer"], "proposer")
    path = _path(root, command["run_log"])
    run, error = _validate_observation_log(path)
    if error is not None:
        raise ValueError("; ".join(error.errors))
    work = _work(policy, work_item_id)
    binding = bound_decision(run)
    if (not binding or binding["action"] != "draft" or binding["work_item_id"] != work_item_id
            or binding["root"] != str(root) or binding["work_revision"] != work["revision"]):
        raise ValueError("preparation requires a current draft Run for this Work Item")
    run_id = _text(_log_field(run, "run_id"), "source Run ID")
    discovery = None
    if policy.get("discovery", False):
        inputs = command["decision_context"]
        principle_discovery.validate_context(inputs)
        prior = {}
        for decision_id in inputs["related_decision_ids"]:
            if decision_id == command["decision_id"]:
                raise ValueError("decision cannot refer to itself")
            earlier = _read_decision(db, decision_id)
            if earlier["prepared"]["work_item_id"] != work_item_id or earlier["proposal"] is None:
                raise ValueError("related decisions must be finalized for this Work Item")
            prior[decision_id] = sorted(earlier["prepared"]["context"]["references"])
        if inputs["candidate"] is not None:
            candidate = _object(inputs["candidate"], {"path", "sha256"}, "discovery candidate")
            _verified_file(root, candidate["path"], candidate["sha256"])
        discovery = principle_discovery.discover(inputs, work["required_xids"], policy["catalog"], prior)
    prepared = {**command, "run_log": path.relative_to(root).as_posix(), "source_run_id": run_id,
            "context": _context(root, policy, work_item_id, discovery),
            **({"principle_discovery": discovery} if discovery is not None else {}),
            **({"checklist_enabled": True} if policy.get("checklist") else {})}
    inputs = reevaluation_inputs(root, work_item_id, work["revision"])
    if inputs:
        prepared["unknown_resolution_inputs"] = inputs
        check_reevaluation(root, prepared)
        for response in inputs.values():
            previous = _read_decision(db, response["source_decision_id"])
            if previous["prepared"]["source_run_id"] == run_id or response["source_decision_id"] == command["decision_id"]:
                raise ValueError("UNKNOWN resolution requires a new decision ID and draft Run")
    return prepared


def _current_context(root, policy, entry):
    if entry.get("superseded_by"):
        raise ValueError("engineering decision has been superseded")
    prepared = entry["prepared"]
    if policy.get("checklist", False) != prepared.get("checklist_enabled", False):
        raise ValueError("engineering checklist policy changed; prepare and resolve a new decision")
    discovery = prepared.get("principle_discovery")
    if policy.get("discovery", False) != (discovery is not None):
        raise ValueError("engineering discovery policy changed; prepare a new decision")
    if discovery is not None:
        prior = {}
        for xid, reasons in discovery["matches"].items():
            for reason in reasons:
                if reason.startswith("existing_decision:"):
                    prior.setdefault(reason.split(":", 1)[1], []).append(xid)
        work = _work(policy, prepared["work_item_id"])
        live_discovery = principle_discovery.discover(prepared["decision_context"], work["required_xids"],
                                                      policy["catalog"], prior)
        if live_discovery != discovery:
            raise ValueError("approved principle discovery coverage changed; prepare a new decision")
    current = _context(root, policy, prepared["work_item_id"], discovery)
    if current != prepared["context"]:
        raise ValueError("engineering decision context changed; prepare a new decision")
    return current


def _check_proposal(root, policy, entry, proposal, *, require_authority=True):
    prepared = entry["prepared"]
    context = _current_context(root, policy, entry)
    discovery = prepared.get("principle_discovery")
    fields = {"classification", "rationale", "basis", "verification", "candidate", "actions"}
    if discovery is not None:
        fields.update({"reference_set_sha256", "alternatives"})
    if prepared.get("checklist_enabled"):
        fields.add("checklist")
    _object(proposal, fields, "proposal")
    classification = _text(proposal["classification"], "classification")
    if classification not in CLASSIFICATIONS:
        raise ValueError("unknown engineering decision classification")
    _text(proposal["rationale"], "rationale")
    work = context["work"]

    allowed_basis = context["references"].keys()
    if discovery is not None:
        resolution = entry.get("reference_set")
        if resolution is None:
            raise ValueError("principle reference set must be resolved before review or finalization")
        if proposal["reference_set_sha256"] != _digest(resolution) or proposal["basis"] != resolution["basis"]:
            raise ValueError("proposal must preserve the resolved principle reference set")
        allowed_basis = discovery["matches"].keys()
        alternatives = proposal["alternatives"]
        if not isinstance(alternatives, list) or not alternatives:
            raise ValueError("record technically considered alternatives")
        for alternative in alternatives:
            _object(alternative, {"option", "assessment"}, "technical alternative")
            _text(alternative["option"], "technical option")
            _text(alternative["assessment"], "technical assessment")
        pinned = prepared["decision_context"]["candidate"]
        if pinned is not None and pinned != proposal["candidate"]:
            raise ValueError("engineering candidate changed; prepare and resolve a new decision")
    if not isinstance(proposal["basis"], dict) or set(proposal["basis"]) - allowed_basis:
        raise ValueError("proposal basis must refer to prepared XIDs")
    for use in proposal["basis"].values():
        _object(use, {"applicability", "reason"}, "applicability")
        if use["applicability"] not in ("applies", "not_applicable", "unresolved"):
            raise ValueError("invalid applicability")
        _text(use["reason"], "applicability reason")
    if not isinstance(proposal["verification"], dict) or set(proposal["verification"]) - set(work["required_checks"]):
        raise ValueError("proposal verification must name configured checks")
    for check in proposal["verification"].values():
        _object(check, {"status", "path", "sha256"}, "verification")
        if check["status"] not in ("pass", "fail", "unknown"):
            raise ValueError("invalid verification status")
        _verified_file(root, check["path"], check["sha256"])
    if proposal["candidate"] is not None:
        candidate = _object(proposal["candidate"], {"path", "sha256"}, "candidate")
        _verified_file(root, candidate["path"], candidate["sha256"])

    evaluators = set()
    if prepared.get("checklist_enabled"):
        if decision_checklist.select(prepared, resolution) != resolution["checklist"]:
            raise ValueError("engineering checklist definition changed; prepare and resolve a new decision")
        evaluators = decision_checklist.validate(
            prepared, resolution, proposal, lambda path, digest: _verified_file(root, path, digest),
            _digest(resolution),
        )

    if classification != "DETERMINED":
        if proposal["actions"] != []:
            raise ValueError("unresolved engineering decisions cannot grant protected actions")
        return
    from xrefkit.unknown_resolution import check_reevaluation

    check_reevaluation(root, prepared)
    actions = set(_keys(proposal["actions"], "authorized actions"))
    if actions - PROTECTED_ACTIONS or actions - set(work["actions"]) or proposal["candidate"] is None:
        raise ValueError("engineering decision requires an exact candidate and permitted actions")
    if context["unresolved_xids"] or {ref["kind"] for ref in context["references"].values()} != {"global", "project"}:
        raise ValueError("engineering decision requires verified global principles and project XIDs")
    if discovery is not None and (
        resolution["uncovered_areas"] or resolution["unknown_flags"] or resolution["unresolved"]
        or any(conflict["status"] == "unresolved" for conflict in resolution["conflicts"])
    ):
        raise ValueError("engineering decision has unresolved principle coverage, applicability or conflicts")
    if set(proposal["basis"]) != set(context["references"]) or any(
        use["applicability"] == "unresolved" for use in proposal["basis"].values()
    ) or not any(use["applicability"] == "applies" for use in proposal["basis"].values()):
        raise ValueError("prepared XIDs require resolved applicability before finalization")
    if set(proposal["verification"]) != set(work["required_checks"]) or any(
        check["status"] != "pass" for check in proposal["verification"].values()
    ):
        raise ValueError("required engineering verification is incomplete")
    if not require_authority:
        return

    decision_id = prepared["decision_id"]
    review = _object(policy["reviews"].get(decision_id),
                     {"reviewer", "prepared_sha256", "proposal_sha256", "verdict"}, "trusted review")
    binding = {"prepared_sha256": _digest(prepared), "proposal_sha256": _digest(proposal)}
    if (review["reviewer"] not in work["reviewers"] or review["reviewer"] == prepared["proposer"]
            or review["reviewer"] in evaluators
            or review != {"reviewer": review["reviewer"], **binding, "verdict": "pass"}):
        raise ValueError("engineering decision lacks current independent review for this revision")
    if work["approver"] is not None and policy["approvals"].get(decision_id) != {
        "approver": work["approver"], **binding, "status": "approved",
    }:
        raise ValueError("engineering decision lacks current scoped approval")


def record_decision(root, command):
    """Persist one immutable candidate or evaluated proposal under a stable ID."""
    policy = _policy(root)
    if not isinstance(command, dict):
        raise ValueError("engineering decision command must be an object")
    decision_id = _text(command.get("decision_id"), "decision ID")
    operation = command.get("action")
    if operation == "review":
        _object(command, {"action", "decision_id", "proposal"}, "review command")
        with closing(_store(root, readonly=True)) as db:
            entry = _read_decision(db, decision_id)
        _check_proposal(root, policy, entry, command["proposal"], require_authority=False)
        return {"decision_id": decision_id, "state": "ready_for_review",
                "prepared_sha256": _digest(entry["prepared"]), "proposal_sha256": _digest(command["proposal"])}
    with closing(_store(root)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS engineering_decision (id TEXT PRIMARY KEY, prepared TEXT NOT NULL, proposal TEXT)")
        db.execute("""CREATE TABLE IF NOT EXISTS engineering_reference_set (
            id TEXT PRIMARY KEY, searched_at TEXT, resolution TEXT, superseded_by TEXT
        )""")
        if operation == "prepare":
            prepared = _prepare(root, policy, command, db)
            db.execute("INSERT OR IGNORE INTO engineering_decision VALUES (?, ?, NULL)", (decision_id, _encode(prepared)))
            entry = _read_decision(db, decision_id)
            if entry["prepared"] != prepared:
                raise ValueError("engineering decision ID already binds another context")
            extra = {}
            if "principle_discovery" in prepared:
                if entry.get("superseded_by"):
                    raise ValueError("engineering decision has been superseded")
                db.execute("INSERT OR IGNORE INTO engineering_reference_set (id, searched_at) VALUES (?, ?)",
                           (decision_id, datetime.now(timezone.utc).isoformat()))
                previous_id = command.get("supersedes")
                if previous_id is not None:
                    previous = _read_decision(db, previous_id)
                    if (previous_id == decision_id
                            or previous["prepared"]["work_item_id"] != prepared["work_item_id"]
                            or previous.get("superseded_by") not in (None, decision_id)):
                        raise ValueError("supersession requires a prior decision for the same Work Item")
                    db.execute("INSERT OR IGNORE INTO engineering_reference_set (id) VALUES (?)", (previous_id,))
                    db.execute("UPDATE engineering_reference_set SET superseded_by = ? WHERE id = ?",
                               (decision_id, previous_id))
                extra = {"principle_discovery": prepared["principle_discovery"],
                         "searched_at": _read_decision(db, decision_id)["searched_at"]}
            references = {xid: {**ref, "content": _verified_file(
                root, ref["path"], ref["sha256"]).decode("utf-8-sig")}
                for xid, ref in prepared["context"]["references"].items()}
            if prepared.get("unknown_resolution_inputs"):
                extra["unknown_resolution_inputs"] = prepared["unknown_resolution_inputs"]
            return {"decision_id": decision_id, "state": "prepared", "prepared_sha256": _digest(prepared),
                    "references": references, "unresolved_xids": prepared["context"]["unresolved_xids"], **extra}
        if operation == "resolve":
            _object(command, {"action", "decision_id", "basis", "conflicts"}, "resolve command")
            entry = _read_decision(db, decision_id)
            _current_context(root, policy, entry)
            if "principle_discovery" not in entry["prepared"]:
                raise ValueError("principle resolution requires a discovery-enabled decision")
            resolution = principle_discovery.resolve(entry["prepared"], command["basis"], command["conflicts"])
            resolution["prepared_sha256"] = _digest(entry["prepared"])
            if entry["prepared"].get("checklist_enabled"):
                resolution["checklist"] = decision_checklist.select(entry["prepared"], resolution)
            if entry["reference_set"] is not None and entry["reference_set"] != resolution:
                raise ValueError("principle reference set is immutable; prepare a new decision")
            db.execute("UPDATE engineering_reference_set SET resolution = ? WHERE id = ?",
                       (_encode(resolution), decision_id))
            return {"decision_id": decision_id, "state": "references_resolved",
                    "reference_set_sha256": _digest(resolution), "reference_set": resolution}
        if operation != "finalize":
            raise ValueError("engineering decision action must be prepare, resolve, review or finalize")
        _object(command, {"action", "decision_id", "proposal"}, "finalize command")
        entry = _read_decision(db, decision_id)
        proposal = command["proposal"]
        if entry["proposal"] is not None and entry["proposal"] != proposal:
            raise ValueError("engineering decision result is immutable; use a new ID")
        _check_proposal(root, policy, entry, proposal)
        db.execute("UPDATE engineering_decision SET proposal = ? WHERE id = ?", (_encode(proposal), decision_id))
        return {"decision_id": decision_id, "state": proposal["classification"],
                "proposal_sha256": _digest(proposal), "candidate": proposal["candidate"]}


def require_decision(root, work_item_id, action, decision_id, *, handoff_request_id=None):
    """Authorize one currently registered action from an immutable decision."""
    policy = _policy(root)
    work = _work(policy, work_item_id)
    if action not in PROTECTED_ACTIONS or action not in work["actions"]:
        raise ValueError("engineering action is not permitted for this Work Item")
    decision_id = _text(decision_id, "engineering decision ID")
    if not _path(root, JOURNAL_FILE).is_file():
        raise ValueError("engineering decision journal does not exist")
    with closing(_store(root, readonly=True)) as db:
        entry = _read_decision(db, decision_id)
    prepared, proposal = entry["prepared"], entry["proposal"]
    if (prepared["work_item_id"] != work_item_id or not proposal
            or proposal["classification"] != "DETERMINED" or action not in proposal["actions"]):
        raise ValueError("action requires a DETERMINED engineering decision for this Work Item and scope")
    if handoff_request_id is not None and prepared.get("handoff_request_id") != handoff_request_id:
        raise ValueError("engineering resume decision is not linked to this Handoff request")
    _check_proposal(root, policy, entry, proposal)
    return {"decision_id": decision_id, "state": "DETERMINED", "work_item_id": work_item_id,
            "work_revision": work["revision"], "action": action,
            "proposal_sha256": _digest(proposal), "candidate": proposal["candidate"],
            **({"checklist_sha256": _digest(proposal["checklist"])} if "checklist" in proposal else {}),
            **({"reference_set_sha256": proposal["reference_set_sha256"]}
               if "reference_set_sha256" in proposal else {})}


def _technical_handoff_policy(root, work_item_id, decision_id):
    policy = _policy(root, required=False)
    if policy is not None and work_item_id in policy["work_items"]:
        if PROTECTED_ACTIONS.intersection(_work(policy, work_item_id)["actions"]):
            return policy
    if decision_id is not None:
        raise ValueError("engineering decision policy is required for this technical Work Item")
    return None


def require_handoff_decision(root, work_item_id, work_revision, source_run_id, decision_id):
    """Require an evaluated escalation before a managed technical handoff."""
    policy = _technical_handoff_policy(root, work_item_id, decision_id)
    if policy is None:
        return
    decision_id = _text(decision_id, "engineering decision ID")
    with closing(_store(root, readonly=True)) as db:
        entry = _read_decision(db, decision_id)
    prepared, proposal = entry["prepared"], entry["proposal"]
    if (prepared["work_item_id"] != work_item_id or prepared["source_run_id"] != source_run_id
            or prepared["context"]["work"]["revision"] != work_revision
            or not proposal or proposal["classification"] != "ESCALATION_REQUIRED"):
        raise ValueError("engineering handoff requires an escalation for the current Work Item revision")
    _check_proposal(root, policy, entry, proposal)


def require_unknown_decision(root, request):
    from xrefkit.unknown_resolution import check_request

    decision_id = _text(request["engineering_decision_id"], "engineering decision ID")
    policy = _technical_handoff_policy(root, request["work_item_id"], decision_id)
    with closing(_store(root, readonly=True)) as db:
        entry = _read_decision(db, decision_id)
    prepared, proposal = entry["prepared"], entry["proposal"]
    if (not prepared.get("checklist_enabled") or prepared["work_item_id"] != request["work_item_id"]
            or prepared["source_run_id"] != request["source_run_id"]
            or prepared["context"]["work"]["revision"] != request["work_revision"]
            or not proposal or proposal["classification"] not in {"CONDITIONAL", "BLOCKED", "ESCALATION_REQUIRED"}):
        raise ValueError("UNKNOWN handoff requires an evaluated open decision for the source Run and Work Item")
    _check_proposal(root, policy, entry, proposal)
    check_request(request, entry)


def require_handoff_resume(root, work_item_id, work_revision, request_id, decision_id):
    if _technical_handoff_policy(root, work_item_id, decision_id) is None:
        return
    receipt = require_decision(root, work_item_id, "manufacturing", decision_id, handoff_request_id=request_id)
    if receipt["work_revision"] != work_revision:
        raise ValueError("engineering resume decision belongs to another Work Item revision")


def bind_run(root, args):
    """Require an explicit Work Item and action only on enrolled project roots."""
    policy = _policy(root, required=False)
    action = getattr(args, "engineering_action", None)
    decision_id = getattr(args, "engineering_decision_id", None)
    candidate = getattr(args, "engineering_candidate", None)
    if policy is None:
        if action is not None or decision_id is not None or candidate is not None:
            raise ValueError("engineering decision policy is required")
        return None
    work_item_id = _text(getattr(args, "work_item_id", None), "engineering Work Item ID")
    work = _work(policy, work_item_id)
    if action not in work["actions"]:
        raise ValueError("an explicit engineering action registered for this Work Item is required")
    if action == "draft":
        if decision_id is not None or candidate is not None:
            raise ValueError("a draft does not consume an engineering decision")
        return {"work_item_id": work_item_id, "work_revision": work["revision"], "action": action}
    receipt = require_decision(root, work_item_id, action, decision_id)
    if _path(root, candidate) != _path(root, receipt["candidate"]["path"]):
        raise ValueError("engineering candidate must match the authorized artifact")
    return receipt


def bound_decision(run_text):
    from xrefkit.skillrun import _log_field, _observation_events

    events = _observation_events(run_text)
    matches = [event for event in events if event.get("event") == BOUND_EVENT]
    opened = next((event for event in events if event.get("event") == "operation.observed"
                   and event.get("operation") == "run.opened"), None)
    local_root = opened.get("facts", {}).get("local_root") if opened else None
    if not matches:
        if isinstance(local_root, str) and (Path(local_root) / POLICY_FILE).exists():
            raise ValueError("the enrolled root requires a new Run with an engineering binding")
        return None
    if (len(matches) != 1 or matches[0].get("work_item_id") != _log_field(run_text, "work_item_id")
            or matches[0].get("root") != local_root):
        raise ValueError("engineering binding does not match the Run Work Item")
    binding = matches[0]
    fields = {"event", "root", "work_item_id", "work_revision", "action"}
    action = _text(binding.get("action"), "bound engineering action")
    if action in PROTECTED_ACTIONS:
        fields.update({"decision_id", "state", "proposal_sha256", "candidate"})
        if "reference_set_sha256" in binding:
            fields.add("reference_set_sha256")
        if "checklist_sha256" in binding:
            fields.add("checklist_sha256")
    elif action != "draft":
        raise ValueError("unsupported engineering Run action")
    return _object(binding, fields, "engineering Run binding")


def validate_run_decision(run_text):
    binding = bound_decision(run_text)
    if binding is None or binding["action"] == "draft":
        return
    try:
        current = require_decision(Path(binding["root"]), binding["work_item_id"], binding["action"],
                                   binding["decision_id"])
    except (OSError, sqlite3.Error) as exc:
        raise ValueError(f"could not revalidate engineering decision: {exc}") from exc
    if any(binding.get(key) != value for key, value in current.items()):
        raise ValueError("engineering decision no longer matches the Run binding")


def cmd_engineering_decision(args):
    root = Path(args.root).resolve()
    try:
        if args.input is not None:
            result = record_decision(root, _read_json(_path(root, args.input)))
        elif args.inspect is not None:
            with closing(_store(root, readonly=True)) as db:
                result = _read_decision(db, args.inspect)
            resolution = result.get("reference_set") or {}
            if "checklist" in resolution:
                results = ((result["proposal"] or {}).get("checklist") or {}).get("results", {})
                result["checklist_pending"] = decision_checklist.pending(resolution["checklist"], results)
        else:
            work_item, action, decision_id = args.use
            result = require_decision(root, work_item, action, decision_id)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0
