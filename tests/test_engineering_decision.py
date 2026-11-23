import copy
import hashlib
import json

import pytest

from test_skill_definition_runtime import _definition
from test_subagent_startup import command
from xrefkit.decision_handoff import apply_transition
from xrefkit.engineering_decision import (
    POLICY_FILE, _digest, record_decision, require_decision, require_handoff_resume,
)


def pinned(root, name, body):
    (root / name).write_text(body, encoding="utf-8")
    return {"path": name, "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}


@pytest.fixture
def project(tmp_path):
    catalog = {}
    for xid, kind in (("111111AAAAAA", "global"), ("222222BBBBBB", "project")):
        catalog[xid] = {"kind": kind, "revision": "r1", **pinned(
            tmp_path, f"{kind}.md", f"<!-- xid: {xid} -->\n# {kind} design policy\n")}
    work = {"revision": "revision-1", "actions": ["draft", "manufacturing", "test_design", "retry"],
            "required_xids": list(catalog), "required_checks": ["reconciliation", "replay"],
            "reviewers": ["reviewer"], "approver": "design-owner"}
    policy = {"schema_version": 1, "work_items": {"WI-1": work, "WI-2": copy.deepcopy(work)},
              "catalog": catalog, "reviews": {}, "approvals": {}}

    def update():
        (tmp_path / POLICY_FILE).write_text(json.dumps(policy), encoding="utf-8")

    update()
    candidate = pinned(tmp_path, "design.md", "# Scoped design")
    evidence = pinned(tmp_path, "check.md", "# Test and review results")
    proposal = {"classification": "DETERMINED", "rationale": "Preserves operation identity",
                "basis": {xid: {"applicability": "applies", "reason": "Scope covers this change"} for xid in catalog},
                "verification": {name: {"status": "pass", **evidence} for name in work["required_checks"]},
                "candidate": candidate, "actions": ["manufacturing", "test_design", "retry"]}
    prepare = {"action": "prepare", "decision_id": "ED-1", "work_item_id": "WI-1",
               "run_log": "draft.md", "proposer": "designer", "question": "Does the revised design permit replay?"}
    code, output = command("workflow", "run", "--root", str(tmp_path), "--work-item-id", "WI-1",
                           "--engineering-action", "draft", "--out", "draft.md", "--task", "Prepare design",
                           "--use-default-completion-conditions", "--json")
    assert code == 0, output

    def authorize(result, draft=proposal):
        binding = {"prepared_sha256": result["prepared_sha256"], "proposal_sha256": _digest(draft)}
        policy["reviews"]["ED-1"] = {**binding, "reviewer": "reviewer", "verdict": "pass"}
        policy["approvals"]["ED-1"] = {**binding, "approver": "design-owner", "status": "approved"}
        update()

    return policy, proposal, prepare, update, authorize


def finalize(root, proposal):
    return record_decision(root, {"action": "finalize", "decision_id": "ED-1", "proposal": proposal})


def test_requires_resolved_basis_independent_review_and_scoped_approval(tmp_path, project):
    policy, proposal, prepare, update, authorize = project
    prepared = record_decision(tmp_path, prepare)
    assert "global design policy" in prepared["references"]["111111AAAAAA"]["content"]
    assert prepared == record_decision(tmp_path, prepare)
    with pytest.raises(ValueError, match="required engineering verification"):
        finalize(tmp_path, {**proposal, "verification": {}})
    with pytest.raises(ValueError, match="resolved applicability"):
        finalize(tmp_path, {**proposal, "basis": {}})
    review = record_decision(tmp_path, {"action": "review", "decision_id": "ED-1", "proposal": proposal})
    assert review["proposal_sha256"] == _digest(proposal)
    with pytest.raises(ValueError, match="requires a DETERMINED"):
        require_decision(tmp_path, "WI-1", "manufacturing", "ED-1")
    authorize(prepared)
    policy["reviews"]["ED-1"]["reviewer"] = "designer"
    policy["work_items"]["WI-1"]["reviewers"].append("designer")
    update()
    with pytest.raises(ValueError, match="context changed"):
        finalize(tmp_path, proposal)
    policy["work_items"]["WI-1"]["reviewers"].remove("designer")
    update()
    with pytest.raises(ValueError, match="independent review"):
        finalize(tmp_path, proposal)
    authorize(prepared)
    policy["approvals"]["ED-1"]["proposal_sha256"] = "invalid"
    update()
    with pytest.raises(ValueError, match="scoped approval"):
        finalize(tmp_path, proposal)
    authorize(prepared)
    assert finalize(tmp_path, proposal)["state"] == "DETERMINED"
    assert require_decision(tmp_path, "WI-1", "manufacturing", "ED-1")["candidate"] == proposal["candidate"]
    with pytest.raises(ValueError, match="Work Item and scope"):
        require_decision(tmp_path, "WI-2", "manufacturing", "ED-1")
    with pytest.raises(ValueError, match="immutable"):
        finalize(tmp_path, {**proposal, "rationale": "different"})


@pytest.mark.parametrize("changed", ["candidate", "project_reference", "approval", "work_revision"])
def test_revalidates_live_inputs_before_use(tmp_path, project, changed):
    policy, proposal, prepare, update, authorize = project
    authorize(record_decision(tmp_path, prepare))
    finalize(tmp_path, proposal)
    match changed:
        case "candidate":
            (tmp_path / "design.md").write_text("different artifact", encoding="utf-8")
        case "project_reference":
            (tmp_path / "project.md").write_text("new policy", encoding="utf-8")
        case "approval":
            policy["approvals"].clear()
        case "work_revision":
            policy["work_items"]["WI-1"]["revision"] = "revision-2"
    update()
    with pytest.raises(ValueError):
        require_decision(tmp_path, "WI-1", "retry", "ED-1")


@pytest.mark.parametrize("classification", ["CONDITIONAL", "BLOCKED", "ESCALATION_REQUIRED"])
def test_missing_xids_are_recorded_and_cannot_authorize(tmp_path, project, classification):
    policy, _, prepare, update, _ = project
    policy["catalog"].pop("222222BBBBBB")
    update()
    prepared = record_decision(tmp_path, prepare)
    assert set(prepared["unresolved_xids"]) == {"222222BBBBBB"}
    proposal = {"classification": classification, "rationale": "Project policy unavailable",
                "basis": {}, "verification": {}, "candidate": None, "actions": []}
    assert finalize(tmp_path, proposal)["state"] == classification
    with pytest.raises(ValueError, match="requires a DETERMINED"):
        require_decision(tmp_path, "WI-1", "manufacturing", "ED-1")


def test_direct_workflow_skill_and_retry_require_engineering_binding(tmp_path, project):
    policy, proposal, prepare, update, authorize = project
    root = str(tmp_path)
    log = tmp_path / "design-run.md"
    common = ("--root", root, "--work-item-id", "WI-1", "--task", "Synthetic change")
    def workflow(*args):
        return command("workflow", "run", *common, "--use-default-completion-conditions",
                       "--out", str(log), *args, "--json")

    assert workflow("--engineering-action", "manufacturing")[0] == 1
    assert not log.exists()
    assert workflow()[0] == 1
    assert workflow("--engineering-action", "draft")[0] == 0
    recovery = ("workflow", "recovery", "--log", str(log), "--recovery-id", "R1",
                "--status", "confirmed", "--resume-location", "manufacturing",
                "--reason", "Resolved", "--next-action", "Retry", "--reviewer", "reviewer")
    assert command(*recovery, "--json")[0] == 1
    input_path = tmp_path / "prepare.json"
    input_path.write_text(json.dumps(prepare), encoding="utf-8")
    code, output = command("workflow", "engineering-decision", "--root", root, "--input", "prepare.json")
    assert code == 0, output
    authorize(json.loads(output))
    finalize(tmp_path, proposal)
    assert command(*recovery, "--engineering-decision-id", "ED-1", "--json")[0] == 0
    assert command("workflow", "engineering-decision", "--root", root, "--use", "WI-1", "retry", "ED-1")[0] == 0
    definition = tmp_path / "SKILL.v1.md"
    definition.write_text(_definition(), encoding="utf-8")
    skill = ("skill", "run", *common, "--definition", str(definition),
             "--capability", "bounded design", "--tuning", "fixture", "--responsibility", "test",
             "--execution-mode", "subagent_required", "--engineering-action", "test_design",
             "--engineering-decision-id", "ED-1", "--out", str(tmp_path / "test-run.md"))
    assert command(*skill, "--engineering-candidate", "different.md", "--json")[0] == 1
    code, output = command(*skill, "--engineering-candidate", "design.md", "--json")
    assert code == 0, output
    policy["approvals"].clear()
    update()
    code, output = command("skill", "verify", "--log", str(tmp_path / "test-run.md"), "--json")
    assert code == 1
    assert any("scoped approval" in error for error in json.loads(output)["errors"])


@pytest.mark.parametrize("mode", ["legacy", "discovery", "checklist"])
def test_enrolled_pending_handoff_preserves_escalation_and_hold(tmp_path, project, mode):
    policy, _, prepare, update, _ = project
    root = str(tmp_path)
    discovery_enabled = mode != "legacy"
    if discovery_enabled:
        from test_principle_discovery import PROJECT, discovery_context, enable_discovery, evaluate, proposal_with

        enable_discovery(policy)
        prepare = {**prepare, "decision_context": discovery_context(external_side_effects="unknown")}
    if mode == "checklist":
        policy["checklist"] = True
    policy["work_items"]["PARENT"] = copy.deepcopy(policy["work_items"]["WI-1"])
    update()

    def invoke(*args):
        code, output = command(*map(str, args), "--json")
        assert code == 0, output
        return json.loads(output)

    def item(log, identifier, role):
        invoke("skill", "workitem", "--log", log, "--item", identifier, "--text", "Coordinate design",
               "--completion-criterion", "Evidence recorded", "--status", "pending", "--role", role)

    parent = tmp_path / "parent.md"
    parent_run = invoke("workflow", "run", "--root", root, "--work-item-id", "PARENT", "--engineering-action",
                        "draft", "--task", "Coordinate", "--out", parent, "--use-default-completion-conditions")
    case_runs = {}
    for work_id, skill, file in (("WI-1", "brownfield_example", "bf.md"), ("WI-2", "pm_example", "pm.md")):
        item(parent, work_id, parent_run["assigned_roles"]["executor"])
        definition = tmp_path / f"{skill}.md"
        definition.write_text(_definition().replace("definition_sample", skill), encoding="utf-8")
        case_runs[work_id] = invoke(
            "workflow", "delegate", "--root", root, "--parent-log", parent, "--out", tmp_path / file,
            "--work-item-id", work_id, "--engineering-action", "draft", "--definition", definition,
            "--task", "Investigate", "--capability", "design", "--tuning", "synthetic",
            "--responsibility", "record evidence", "--execution-mode", "subagent_required",
        )
    source = case_runs["WI-1"]
    item(source["run_log"], "WI-1", source["assigned_roles"]["executor"])
    prepared = record_decision(tmp_path, {**prepare, "run_log": "bf.md"})
    escalation = {"classification": "ESCALATION_REQUIRED", "rationale": "Exception requires authority",
                  "basis": {}, "verification": {}, "candidate": None, "actions": []}
    if discovery_enabled:
        resolution = evaluate(tmp_path, prepared, {
            PROJECT: {"applicability": "unresolved", "reason": "Product policy for duplicate effects is undecided"},
        })
        escalation = proposal_with(escalation, resolution)
        if mode == "checklist":
            escalation["checklist"] = {"decision_id": "ED-1", "candidate": None,
                                       "reference_set_sha256": escalation["reference_set_sha256"],
                                       "results": {"API-01": {
                                           "revision": "1", "applicability": "applies", "result": "UNKNOWN",
                                           "reason": "Provider effect contract is unavailable",
                                           "references": {}, "evidence": [], "unresolved": ["Provider effects"],
                                           "evaluator": "designer",
                                       }}}
    finalize(tmp_path, escalation)
    candidate = pinned(tmp_path, "finding.json", json.dumps({
        "schema": "brownfield.design_finding/v1", "engineering_decision_id": "ED-1",
        "source_run_id": source["run_id"], "work_item_id": "WI-1", "work_revision": "revision-1",
    }))
    invoke("skill", "artifact", "--log", source["run_log"], "--artifact", "F1", "--item", "WI-1",
           "--kind", "output", "--target", "finding.json", "--status", "done",
           "--role", source["assigned_roles"]["executor"])
    current = {"work_item_id": "WI-1", "work_revision": "revision-1",
               "policy_revision": "policy-r1", "policy_sha256": "a" * 64, "decision_owner": None}
    request = {**{k: v for k, v in current.items() if k != "decision_owner"},
               "source_artifact_id": "F1", "source_artifact_sha256": candidate["sha256"],
               "source_run_id": source["run_id"], "pm_work_item_id": "WI-2", "pm_skill_id": "pm_example",
               "subject": "Exception decision", "evidence": ["finding.json"], "unknowns": ["U1"]}

    def transition(action, data, actor="WI-1"):
        return apply_transition(tmp_path, tmp_path / "handoff.sqlite",
                                {"schema_version": 1, "request_id": "REQ-1", "action": action,
                                 "data": data, "current": current, "parent_log": str(parent),
                                 "run_log": case_runs[actor]["run_log"]})

    with pytest.raises(ValueError, match="engineering decision ID"):
        transition("create", request)
    assert transition("create", {**request, "engineering_decision_id": "ED-1"})["state"] == "prepared"
    assert transition("send", {})["state"] == "sent"
    assert transition("receive", {}, "WI-2")["state"] == "received"
    assert transition("route", {"owner": None, "reason": "Unknown authority", "evidence": ["F1"]}, "WI-2")["state"] == "waiting"
    assert transition("return", {"disposition": "held", "reason": "Authority unavailable", "evidence": ["F1"]}, "WI-2")["state"] == "returned"
    assert transition("acknowledge", {})["state"] == "acknowledged"
    assert transition("assess", {"outcome": "hold", "evidence": ["F1"], "resolved_unknowns": {}})["state"] == "assessed"
    if discovery_enabled:
        code, output = command("workflow", "engineering-decision", "--root", root, "--inspect", "ED-1")
        assert code == 0 and json.loads(output)["reference_set"]["unresolved"] == [PROJECT]
        if mode == "checklist":
            inspected = json.loads(output)
            assert inspected["checklist_pending"]["API-01"] == "UNKNOWN"
            assert inspected["proposal"]["checklist"]["results"]["API-01"]["unresolved"] == ["Provider effects"]


def test_handoff_resume_requires_technical_decision_linked_to_request(tmp_path, project):
    _, proposal, prepare, _, authorize = project
    prepared = record_decision(tmp_path, {**prepare, "handoff_request_id": "REQ-1"})
    authorize(prepared)
    finalize(tmp_path, proposal)
    with pytest.raises(ValueError, match="not linked"):
        require_handoff_resume(tmp_path, "WI-1", "revision-1", "REQ-2", "ED-1")
    with pytest.raises(ValueError, match="another Work Item revision"):
        require_handoff_resume(tmp_path, "WI-1", "revision-0", "REQ-1", "ED-1")
    require_handoff_resume(tmp_path, "WI-1", "revision-1", "REQ-1", "ED-1")
