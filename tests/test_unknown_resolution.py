import copy
import json
import shutil

import pytest

from test_decision_checklist import checklist_project, checklist_proposal, discovery_project, project
from test_decision_handoff import cli, item
from test_engineering_decision import pinned
from test_principle_discovery import evaluate
from test_subagent_startup import command
from xrefkit import discovery
from xrefkit.decision_handoff import _digest
from xrefkit.engineering_decision import record_decision, require_decision
from xrefkit.loaders import load_package_manifest
from xrefkit.unknown_resolution import JOURNAL


@pytest.fixture
def resolution_case(tmp_path, checklist_project, monkeypatch):
    brownfield_root = pytest.importorskip("xrefkit_skills_brownfield").package_root
    pm_root = pytest.importorskip("xrefkit_skills_project_management").package_root
    discovered = discovery.discover_skill_packages()
    if not {"brownfield", "project_management"}.issubset({package.entry_point_name for package in discovered}):
        packages = []
        for entry, root in (("brownfield", brownfield_root()), ("project_management", pm_root())):
            manifest = root / "package_manifest.yaml"
            packages.append(discovery.DiscoveredSkillPackage(entry, root, manifest, load_package_manifest(manifest)))
        monkeypatch.setattr(discovery, "discover_skill_packages", lambda: packages)
    policy, proposal, prepare, update, _ = checklist_project
    policy["work_items"]["PARENT"] = copy.deepcopy(policy["work_items"]["WI-1"])
    update()
    parent = tmp_path / "parent.md"
    p = cli("workflow", "run", "--root", tmp_path, "--work-item-id", "PARENT",
            "--engineering-action", "draft", "--task", "Coordinate", "--out", parent,
            "--use-default-completion-conditions")
    runs = {}
    materialized = tmp_path / "pm-package"
    materialized.mkdir()
    definition = materialized / "SKILL.v1.md"
    governance = materialized / "pm_decision_coordination.json"
    shutil.copyfile(pm_root() / "skills/packs/project-management/pm_decision_coordination/SKILL.v1.md", definition)
    shutil.copyfile(pm_root() / "governance/skills/pm_decision_coordination.json", governance)
    for work_id, skill_args in (
        ("WI-1", ("--package-skill", "xrefkit.skills.brownfield::brownfield.workflow")),
        ("WI-2", ("--definition", definition, "--governance", governance)),
    ):
        item(parent, work_id, p["assigned_roles"]["executor"])
        runs[work_id] = cli(
            "workflow", "delegate", "--root", tmp_path, "--parent-log", parent,
            "--out", tmp_path / f"{work_id}.md", "--work-item-id", work_id,
            "--engineering-action", "draft", *skill_args, "--task", "Investigate",
            "--capability", "design", "--tuning", "synthetic", "--responsibility", "record evidence",
            "--execution-mode", "subagent_required",
        )
    source = runs["WI-1"]
    item(source["run_log"], "WI-1", source["assigned_roles"]["executor"])
    prepared = record_decision(tmp_path, {**prepare, "run_log": "WI-1.md"})
    resolved = evaluate(tmp_path, prepared)
    draft = checklist_proposal(proposal, prepared, resolved)
    checks = resolved["reference_set"]["checklist"]
    unknowns = ["API-01", "API-04"]
    items = {}
    for check_id in unknowns:
        result = draft["checklist"]["results"][check_id]
        result.update(result="UNKNOWN", reason="Provider contract unavailable", unresolved=["Replay scope"])
        items[check_id] = {
            "classification": "MISSING_EVIDENCE", "question": checks["checks"][check_id]["question"],
            "reason": result["reason"], "related_xids": result["references"],
            "required_action": "Verify provider replay", "expected_evidence": "Provider execution log",
            "acceptance_criteria": "One effect remains after replay",
        }
    unresolved = {**draft, "classification": "CONDITIONAL", "actions": []}
    record_decision(tmp_path, {"action": "finalize", "decision_id": "ED-1", "proposal": unresolved})
    finding = pinned(tmp_path, "finding.json", json.dumps({
        "schema": "brownfield.design_finding/v1", "engineering_decision_id": "ED-1",
        "source_run_id": source["run_id"], "work_item_id": "WI-1", "work_revision": "revision-1",
    }))
    cli("skill", "artifact", "--log", source["run_log"], "--artifact", "F1", "--item", "WI-1",
        "--kind", "output", "--target", "finding.json", "--status", "done",
        "--role", source["assigned_roles"]["executor"])
    current = {"work_item_id": "WI-1", "work_revision": "revision-1",
               "policy_revision": "policy-r1", "policy_sha256": "a" * 64}
    request = {**current, "request_type": "UNKNOWN_RESOLUTION", "engineering_decision_id": "ED-1",
               "source_artifact_id": "F1", "source_artifact_sha256": finding["sha256"],
               "source_run_id": source["run_id"], "pm_work_item_id": "WI-2", "pm_skill_id": "pm_decision_coordination",
               "subject": "Verify provider replay", "evidence": ["finding.json"], "unknowns": unknowns,
               "resolution": {"candidate": draft["candidate"], "reference_set_sha256": draft["reference_set_sha256"],
                              "checklist_revision": checks["revision"], "items": items,
                              "group": {"cause": "Provider contract", "owner": "provider-test",
                                        "environment": "sandbox", "authority": "design-owner"}}}
    current["decision_owner"] = "provider-test"
    route = {"owner": "provider-test", "role": "verifier", "due_at": "2099-01-01T00:00:00+00:00",
             "blocked_scope": "WI-1", "restart_condition": "Rerun the engineering gate",
             "reason": "Verify replay", "evidence": ["finding.json"]}

    def transition(action, data=None, *, request_id="REQ-1", expected_error=None, journal=JOURNAL):
        actor = "WI-2" if action in {"receive", "route", "return"} else "WI-1"
        payload = {"schema_version": 1, "request_id": request_id, "action": action,
                   "data": data or {}, "current": current, "parent_log": str(parent),
                   "run_log": runs[actor]["run_log"]}
        file = tmp_path / f"{request_id}-{action}.json"
        file.write_text(json.dumps(payload), encoding="utf-8")
        code, output = command("workflow", "decision-handoff", "--root", str(tmp_path),
                               "--journal", journal, "--input", str(file))
        if expected_error:
            assert code == 1 and expected_error in output
        else:
            assert code == 0, output
        return json.loads(output)

    def next_decision(decision_id, work_id="WI-1"):
        name = f"{decision_id}.md"
        cli("workflow", "run", "--root", tmp_path, "--work-item-id", work_id,
            "--engineering-action", "draft", "--out", name, "--task", "Reevaluate",
            "--use-default-completion-conditions")
        new = {**prepare, "decision_id": decision_id, "run_log": name, "work_item_id": work_id}
        if work_id == "WI-1":
            new["supersedes"] = "ED-1"
        return new

    return policy, proposal, update, transition, request, current, route, next_decision


@pytest.mark.parametrize("outcome", [
    "EVIDENCE_PROVIDED", "INFORMATION_PROVIDED", "DESIGN_DIRECTION", "RISK_ACCEPTED", "REJECTED", "CANNOT_RESOLVE",
])
def test_unknown_full_protocol(tmp_path, resolution_case, outcome):
    policy, proposal, update, transition, req, current, route, next_decision = resolution_case
    code, output = command("workflow", "engineering-decision", "--root", str(tmp_path), "--inspect", "ED-1")
    assert code == 0, output
    old = json.loads(output)
    assert old["checklist_pending"] == dict.fromkeys(req["unknowns"], "UNKNOWN")
    assert old["proposal"]["checklist"]["results"]["API-01"]["reason"] == "Provider contract unavailable"
    transition("create", req, journal="alternate.sqlite", expected_error="canonical")
    created = transition("create", req)
    assert created["receipt"]["run"]["run_id"] == req["source_run_id"]
    assert transition("create", req)["reused"]
    transition("create", req, request_id="DUPLICATE", expected_error="already belongs")
    assert transition("send")["state"] == "sent"
    assert transition("receive")["receipt"]["run"]["work_item_id"] == "WI-2"
    transition("route", {**route, "blocked_scope": "WI-2"}, expected_error="scoped Work Item")
    assert transition("route", route)["state"] == "waiting"
    with pytest.raises(ValueError, match="awaiting"):
        record_decision(tmp_path, next_decision("ED-WAIT"))
    with pytest.raises(ValueError, match="DETERMINED"):
        require_decision(tmp_path, "WI-1", "manufacturing", "ED-1")
    unrelated = record_decision(tmp_path, next_decision("ED-OTHER", "WI-2"))
    assert "unknown_resolution_inputs" not in unrelated

    proof = pinned(tmp_path, "human-record.md", "Synthetic human record for this test")
    response = {"request_id": "REQ-1", "candidate": req["resolution"]["candidate"], "responses": {
        check_id: {"outcome": outcome, "actor": "test-person", "authority": "design-owner",
                   "responded_at": "2026-01-01T00:00:00+00:00", "action": "Confirm recorded response",
                   "evidence": [proof], "unresolved": ["Technical evaluation remains"]}
        for check_id in req["unknowns"]
    }}
    if outcome in {"DESIGN_DIRECTION", "RISK_ACCEPTED"}:
        current["resolution_authority"] = "design-owner"
    transition("return", response, expected_error="host-verified")
    current["human_response_sha256"] = _digest(response)
    if outcome == "RISK_ACCEPTED":
        wrong = copy.deepcopy(response)
        wrong["responses"]["API-01"]["authority"] = "pm"
        transition("return", wrong, expected_error="decision authority")
    changed = {**response, "candidate": {**response["candidate"], "sha256": "0" * 64}}
    transition("return", changed, expected_error="original candidate")
    proof_path = tmp_path / proof["path"]
    proof_path.write_text("altered", encoding="utf-8")
    transition("return", response, expected_error="evidence digest mismatch")
    proof_path.write_text("Synthetic human record for this test", encoding="utf-8")

    if outcome == "EVIDENCE_PROVIDED":
        proposal["candidate"] = pinned(tmp_path, "design.md", "# Revised after the original request")
        with pytest.raises(ValueError, match="evidence digest mismatch"):
            record_decision(tmp_path, {"action": "review", "decision_id": "ED-1", "proposal": old["proposal"]})
    assert transition("return", response)["state"] == "returned"
    assert transition("return", response)["reused"]
    new = next_decision("ED-2")
    with pytest.raises(ValueError, match="source acknowledgment"):
        record_decision(tmp_path, new)
    assert transition("acknowledge")["state"] == "acknowledged"
    transition("assess", {"outcome": "resume", "evidence": ["human-record.md"], "resolved_unknowns": {}},
               expected_error="stays held")
    assert transition("assess", {"outcome": "hold", "evidence": ["human-record.md"],
                                 "resolved_unknowns": {}})["state"] == "assessed"
    new["decision_context"] = {**new["decision_context"], "candidate": proposal["candidate"]}
    found = record_decision(tmp_path, new)
    assert found["unknown_resolution_inputs"]["REQ-1"] == {"source_decision_id": "ED-1", "return": response}
    reviewed = checklist_proposal(proposal, found, evaluate(tmp_path, found))
    if outcome in {"RISK_ACCEPTED", "REJECTED", "CANNOT_RESOLVE"}:
        reviewed["checklist"]["results"]["API-04"].update(result="UNKNOWN", unresolved=["Insufficient proof"])
        finalize = {"action": "finalize", "decision_id": "ED-2", "proposal": reviewed}
        with pytest.raises(ValueError, match="API-04=UNKNOWN"):
            record_decision(tmp_path, finalize)
        assert record_decision(tmp_path, {**finalize, "proposal": {
            **reviewed, "classification": "CONDITIONAL", "actions": [],
        }})["state"] == "CONDITIONAL"
        return

    for check_id in req["unknowns"]:
        reviewed["checklist"]["results"][check_id]["evidence"].append(proof)
    finalize = {"action": "finalize", "decision_id": "ED-2", "proposal": reviewed}
    review = record_decision(tmp_path, {**finalize, "action": "review"})
    binding = {key: review[key] for key in ("prepared_sha256", "proposal_sha256")}
    with pytest.raises(ValueError, match="trusted review"):
        record_decision(tmp_path, finalize)
    policy["reviews"]["ED-2"] = {**binding, "reviewer": "reviewer", "verdict": "pass"}
    policy["approvals"]["ED-2"] = {**binding, "approver": "design-owner", "status": "approved"}
    update()
    assert record_decision(tmp_path, finalize)["state"] == "DETERMINED"
    assert require_decision(tmp_path, "WI-1", "manufacturing", "ED-2")["candidate"] == proposal["candidate"]
    proof_path.write_text("altered later", encoding="utf-8")
    with pytest.raises(ValueError, match="evidence digest mismatch"):
        require_decision(tmp_path, "WI-1", "manufacturing", "ED-2")


@pytest.mark.parametrize(("classification", "role"), [
    ("MISSING_INFORMATION", "investigator"), ("AUTHORITY_REQUIRED", "decision_authority"),
    ("ENVIRONMENT_BLOCKED", "environment_owner"), ("KNOWLEDGE_GAP", "knowledge_owner"),
    ("DESIGN_UNRESOLVED", None),
])
def test_unknown_classification_and_scoped_routing(resolution_case, classification, role):
    _, _, _, transition, request, _, route, _ = resolution_case
    for item in request["resolution"]["items"].values():
        item["classification"] = classification
    if role is None:
        transition("create", request, expected_error="rework stays in Brownfield")
        return
    transition("create", request)
    transition("send")
    transition("receive")
    transition("route", {**route, "role": "pm"}, expected_error="routing role")
    assert transition("route", {**route, "role": role})["state"] == "waiting"


def test_unknown_scope_prevents_stale_use_and_allows_other_work(tmp_path, resolution_case):
    policy, proposal, update, transition, request, _, route, next_decision = resolution_case
    for decision_id, work_item in (("ED-PRIOR", "WI-1"), ("ED-OTHER", "WI-2")):
        prepare = next_decision(decision_id, work_item)
        prepare.pop("supersedes", None)
        found = record_decision(tmp_path, prepare)
        draft = checklist_proposal(proposal, found, evaluate(tmp_path, found))
        binding = {"prepared_sha256": found["prepared_sha256"], "proposal_sha256": _digest(draft)}
        policy["reviews"][decision_id] = {**binding, "reviewer": "reviewer", "verdict": "pass"}
        policy["approvals"][decision_id] = {**binding, "approver": "design-owner", "status": "approved"}
        update()
        record_decision(tmp_path, {"action": "finalize", "decision_id": decision_id, "proposal": draft})
    transition("create", request)
    transition("send")
    transition("receive")
    transition("route", route)
    with pytest.raises(ValueError, match="awaiting"):
        require_decision(tmp_path, "WI-1", "manufacturing", "ED-PRIOR")
    assert require_decision(tmp_path, "WI-2", "manufacturing", "ED-OTHER")["state"] == "DETERMINED"
    assert transition("cancel", {"reason": "Provider evidence now requested through a revised scope"})["state"] == "cancelled"
    assert require_decision(tmp_path, "WI-1", "manufacturing", "ED-PRIOR")["state"] == "DETERMINED"


def test_same_scope_items_must_be_grouped_and_only_unknowns_can_be_sent(resolution_case):
    _, _, _, transition, request, _, _, _ = resolution_case
    first, second = request["unknowns"]
    resolution = request["resolution"]

    def one_item(check_id, value):
        return {**request, "unknowns": [check_id], "resolution": {**resolution, "items": {check_id: value}}}

    transition("create", one_item("API-05", resolution["items"][first]), expected_error="actual UNKNOWN")
    transition("create", one_item(first, resolution["items"][first]))
    transition("create", one_item(second, resolution["items"][second]), request_id="SPLIT",
               expected_error="must be grouped")
