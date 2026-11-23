from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
from pathlib import Path

import pytest

from test_skill_definition_runtime import _definition
from test_subagent_startup import command
from xrefkit.decision_handoff import RESUME_CHECKS, _digest, apply_transition
from xrefkit.discovery import DiscoveredSkillPackage
from xrefkit.loaders import load_package_manifest
from xrefkit.skillrun import _observation_events


def cli(*args, expected=0):
    code, output = command(*map(str, args), "--json")
    assert code == expected, output
    return json.loads(output)


def item(log, item_id, role, status="pending"):
    cli("skill", "workitem", "--log", log, "--item", item_id, "--text", "Review work",
        "--completion-criterion", "evidence checked", "--status", status, "--role", role)


@pytest.fixture
def pair(tmp_path, monkeypatch):
    brownfield = (Path(__file__).resolve().parents[1] / "packages/xrefkit-skills-brownfield"
                  / "src/xrefkit_skills_brownfield")
    manifest = brownfield / "package_manifest.yaml"
    discovered = DiscoveredSkillPackage("brownfield", brownfield, manifest, load_package_manifest(manifest))
    monkeypatch.setattr("xrefkit.discovery.discover_skill_packages", lambda: [discovered])
    parent, source, pm = [tmp_path / name for name in ("parent.md", "brownfield.md", "pm.md")]
    parent_run = cli("workflow", "run", "--root", tmp_path, "--task", "Review the fixture",
                     "--out", parent, "--use-default-completion-conditions")
    definition = tmp_path / "SKILL.v1.md"
    definition.write_text(_definition().replace("definition_sample", "work_progress_coordination"), encoding="utf-8")
    options = ("--capability", "bounded review", "--tuning", "fixture", "--responsibility", "report evidence",
               "--execution-mode", "subagent_required")
    item(parent, "DESIGN", "instruction:executor")
    item(parent, "PM", "instruction:executor")
    source_run = cli("workflow", "delegate", "--root", tmp_path, "--parent-log", parent,
                     "--work-item-id", "DESIGN", "--out", source, "--task", "Find the decision",
                     "--package-skill", "xrefkit.skills.brownfield::brownfield.workflow", *options)
    pm_run = cli("workflow", "delegate", "--root", tmp_path, "--parent-log", parent,
                 "--work-item-id", "PM", "--out", pm, "--task", "Route the decision",
                 "--definition", definition, *options)
    item(source, "WORK", "brownfield.workflow:executor")
    (tmp_path / "finding.json").write_text('{"reference":"f1"}', encoding="utf-8")
    cli("skill", "artifact", "--log", source, "--artifact", "FINDING",
        "--kind", "output", "--target", "finding.json", "--item", "WORK",
        "--status", "done", "--role", "brownfield.workflow:executor")
    return parent, source, pm, parent_run["run_id"], source_run["run_id"], pm_run["run_id"]


@pytest.fixture
def request_protocol(tmp_path, pair):
    parent, source, pm, _, source_id, _ = pair
    journal = tmp_path / "decisions.sqlite"
    current = {
        "work_item_id": "WORK", "work_revision": "work-2", "policy_revision": "policy-2",
        "policy_sha256": "a" * 64, "decision_owner": "design-owner",
    }
    request = {
        **{key: current[key] for key in ("work_item_id", "work_revision", "policy_revision", "policy_sha256")},
        "source_run_id": source_id, "pm_work_item_id": "PM", "pm_skill_id": "work_progress_coordination",
        "subject": "Is replay allowed after a missing receipt?", "evidence": ["finding.json#f1"],
        "source_artifact_id": "FINDING",
        "source_artifact_sha256": hashlib.sha256((tmp_path / "finding.json").read_bytes()).hexdigest(),
        "unknowns": ["U-provider", "U-budget"],
    }

    def transition(action, data=None, *, revision=None, actor=None):
        return apply_transition(tmp_path, journal, {
            "schema_version": 1, "request_id": "DR-1", "action": action,
            "parent_log": str(parent), "run_log": str(actor or (pm if action in {"receive", "route", "return"} else source)),
            "current": current if revision is None else revision, "data": {} if data is None else data,
        })

    return transition, request, current


def start(transition, request):
    assert transition("create", request)["state"] == "prepared"
    assert transition("send")["state"] == "sent"


def route(transition, owner="design-owner"):
    assert transition("route", {"owner": owner, "reason": "Reserved judgment", "evidence": ["routing"]})["state"] == "waiting"


def test_pending_source_sends_once_and_concurrent_receive_is_idempotent(pair, request_protocol):
    transition, request, _ = request_protocol
    _, source, _, *_ = pair
    before = source.read_bytes()
    start(transition, request)
    with ThreadPoolExecutor(max_workers=2) as workers:
        receipts = list(workers.map(lambda _: transition("receive"), range(2)))
    assert {result["reused"] for result in receipts} == {False, True}
    assert receipts[0]["receipt"] == receipts[1]["receipt"]
    assert transition("send")["state"] == "received"
    assert transition("create", request)["reused"]
    assert source.read_bytes() == before
    assert "## Closure Gate\n\n- status: `pending`" in source.read_text(encoding="utf-8")


@pytest.mark.parametrize("field,value", [("work_revision", "work-1"), ("policy_revision", "policy-1"),
                                          ("policy_sha256", "b" * 64)])
def test_stale_and_conflicting_requests_are_refused(request_protocol, field, value):
    transition, request, current = request_protocol
    with pytest.raises(ValueError, match="current Work Item and design policy"):
        transition("create", {**request, field: value})
    start(transition, request)
    with pytest.raises(ValueError, match="conflicting"):
        transition("create", {**request, "subject": "Conflicting subject"})
    with pytest.raises(ValueError, match="current Work Item and design policy"):
        transition("receive", revision={**current, field: value})
    assert transition("receive")["state"] == "received"


def test_unresolved_authority_can_return_hold_without_resuming(request_protocol, pair):
    transition, request, current = request_protocol
    start(transition, request)
    with pytest.raises(ValueError, match="designated PM"):
        transition("receive", actor=pair[1])
    transition("receive")
    current["decision_owner"] = None
    route(transition, None)
    held = {"disposition": "held", "reason": "Human authority still unknown", "evidence": ["missing owner"]}
    assert transition("return", held)["state"] == "returned"
    with pytest.raises(ValueError, match="original source"):
        transition("acknowledge", actor=pair[2])
    assert transition("acknowledge")["state"] == "acknowledged"
    assessment = {"outcome": "resume", "evidence": ["impact review"], "resolved_unknowns": {}}
    with pytest.raises(ValueError, match="resume prerequisites"):
        transition("assess", assessment)
    assert transition("assess", {**assessment, "outcome": "hold"})["state"] == "assessed"


def test_decision_and_resume_require_exact_current_authority_and_evidence(request_protocol):
    transition, request, current = request_protocol
    start(transition, request)
    transition("receive")
    route(transition)
    decision = {"disposition": "decided", "decision": "Proceed within approved limits",
                "approval_ref": "approval-42", "evidence": ["scope evidence"]}
    with pytest.raises(ValueError, match="scoped approval"):
        transition("return", decision)
    current["approval"] = {
        **{key: current[key] for key in ("work_item_id", "work_revision", "policy_revision", "policy_sha256")},
        "request_id": "DR-1", "authority": "design-owner", "status": "approved",
        "reference": "approval-42", "decision_sha256": _digest(decision),
    }
    with pytest.raises(ValueError, match="scoped approval"):
        transition("return", {**decision, "decision": "Outside limits"})
    transition("return", decision)
    wrong_owner = copy.deepcopy(current)
    wrong_owner["approval"]["authority"] = "pm"
    with pytest.raises(ValueError, match="scoped approval"):
        transition("acknowledge", revision=wrong_owner)
    transition("acknowledge")
    assessment = {"outcome": "resume", "evidence": ["impact review"],
                  "resolved_unknowns": {"U-provider": "provider evidence", "U-budget": "budget evidence"}}
    with pytest.raises(ValueError, match="resume prerequisites"):
        transition("assess", assessment)
    current["resume_checks"] = dict.fromkeys(RESUME_CHECKS, True)
    with pytest.raises(ValueError, match="resume prerequisites"):
        transition("assess", {**assessment, "resolved_unknowns": {}})
    assert transition("assess", assessment)["receipt"]["data"]["outcome"] == "resume"


def test_cancel_preserves_journal_and_blocks_new_receipt(request_protocol, tmp_path):
    transition, request, _ = request_protocol
    start(transition, request)
    assert transition("cancel", {"reason": "Superseded plan"})["state"] == "cancelled"
    with pytest.raises(ValueError, match="cannot receive"):
        transition("receive")
    code, output = command("workflow", "decision-handoff", "--root", str(tmp_path),
                           "--journal", "decisions.sqlite", "--inspect", "DR-1")
    assert code == 0, output
    assert [receipt["sequence"] for receipt in json.loads(output)["receipts"]] == [1, 2, 3]


def test_cli_creates_receipt_and_reads_history(request_protocol, pair, tmp_path):
    _, data, current = request_protocol
    input_file = tmp_path / "create.json"
    input_file.write_text(json.dumps({
        "schema_version": 1, "action": "create", "request_id": "DR-CLI",
        "parent_log": pair[0].name, "run_log": pair[1].name, "data": data, "current": current,
    }), encoding="utf-8")
    args = ("workflow", "decision-handoff", "--root", str(tmp_path), "--journal", "decisions.sqlite")
    code, output = command(*args, "--input", input_file.name)
    assert code == 0, output
    created = json.loads(output)["receipt"]
    code, output = command(*args, "--inspect", "DR-CLI")
    assert code == 0, output
    assert json.loads(output)["receipts"] == [created]


def test_send_refuses_changed_source_artifact_and_can_retry(request_protocol, tmp_path):
    transition, request, _ = request_protocol
    finding = tmp_path / "finding.json"
    original = finding.read_bytes()
    transition("create", request)
    finding.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="finding artifact"):
        transition("send")
    finding.write_bytes(original)
    assert transition("send")["state"] == "sent"


def test_reconcile_counts_typed_runs_but_requires_host_completion(pair):
    parent, source, pm, parent_id, _, pm_id = pair
    cli("workflow", "reconcile", "--log", parent, "--apply-child-status", expected=1)
    trace = _observation_events(parent.read_text(encoding="utf-8"))
    assert [event["skill_id"] for event in trace if event["event"] == "child_run.started"] == [
        "brownfield.workflow", "work_progress_coordination",
    ]
    assert trace[-1]["child_run_count"] == 2
    assert not trace[-1]["child_status_updates"]
    assert any("lacks verified host completion evidence" in finding for finding in trace[-1]["findings"])
    assert source.exists()

    role = "work_progress_coordination"
    item(pm, "HANDLE", role + ":executor", "done")
    for kind in ("output", "evidence"):
        cli("skill", "artifact", "--log", pm, "--artifact", kind.upper(), "--kind", kind,
            "--target", kind + ".json", "--item", "HANDLE", "--status", "done",
            "--role", role + (":executor" if kind == "output" else ":checker"))
    for phase, user in (("execution", "executor"), ("handoff", "handoff_owner")):
        cli("skill", "phase", "--log", pm, "--phase", phase, "--status", "done", "--role", role + ":" + user)
    assert any("host completion" in error for error in
               cli("skill", "verify", "--log", pm, expected=1)["errors"])
    assert any("host completion" in error for error in
               cli("skill", "close", "--log", pm, expected=1)["errors"])
    blocked = cli("workflow", "reconcile", "--log", parent, "--apply-child-status", expected=1)
    assert {item["item_id"]: item["status"] for item in blocked["work_items"]}["PM"] == "pending"

    receipt_path = pm.with_suffix(".json")
    receipt = {"schema_version": 1, "run_id": pm_id, "parent_run_id": parent_id,
               "flow_id": parent_id, "root_run_id": parent_id, "work_item_id": "PM",
               "invocation_id": "synthetic-host-execution", "outcome": "succeeded",
               "started_at": "2026-11-22T06:00:00Z", "completed_at": "2026-11-22T06:00:03Z"}
    receipt_path.write_text(json.dumps({**receipt, "work_item_id": "DESIGN"}), encoding="utf-8")
    cli("workflow", "record-child-execution", "--root", pm.parent,
        "--log", pm, "--receipt", receipt_path, expected=1)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert not cli("workflow", "record-child-execution", "--root", pm.parent,
                   "--log", pm, "--receipt", receipt_path)["reused"]
    assert cli("workflow", "record-child-execution", "--root", pm.parent,
               "--log", pm, "--receipt", receipt_path)["reused"]
    receipt_path.write_text(json.dumps({**receipt, "invocation_id": "other"}), encoding="utf-8")
    blocked = cli("workflow", "reconcile", "--log", parent, "--apply-child-status", expected=1)
    assert {item["item_id"]: item["status"] for item in blocked["work_items"]}["PM"] == "pending"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    cli("skill", "verify", "--log", pm)
    cli("skill", "close", "--log", pm)
    reconciled = cli("workflow", "reconcile", "--log", parent, "--apply-child-status", expected=1)
    assert {item["item_id"]: item["status"] for item in reconciled["work_items"]} == {"DESIGN": "pending", "PM": "done"}
