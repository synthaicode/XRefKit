import json

import pytest

from test_engineering_decision import finalize, pinned, project
from test_principle_discovery import GLOBAL, discovery_context, discovery_project, evaluate, metadata, proposal_with
from test_subagent_startup import command
from xrefkit import decision_checklist
from xrefkit.engineering_decision import record_decision, require_decision


OMITTED_DESIGNS = {
    "API-01": "On timeout, retry the payment creation API using the existing request body.",
    "API-04": "After a timeout, POST the order again with a new request identifier until one call returns success.",
    "GDC-03": "Let each worker write final status directly; the status table remains the shared output.",
    "GDC-07": "On HTTP 200, mark the operation complete and publish the result.",
}


def checklist_proposal(proposal, found, resolved, *, evaluator="designer"):
    draft = proposal_with(proposal, resolved)
    proof = proposal["verification"]["replay"]
    refs = {xid: source["revision"] for xid, source in found["references"].items()}
    items = {}
    for check_id, check in resolved["reference_set"]["checklist"]["checks"].items():
        applies = check["applicability"]["applies"]
        items[check_id] = {
            "revision": check["revision"], "applicability": "applies" if applies else "not_applicable",
            "result": "PASS" if applies else "NOT_APPLICABLE",
            "reason": "The synthetic evidence covers the design question" if applies else "Single serialized writer",
            "references": refs, "evidence": [{key: proof[key] for key in ("path", "sha256")}] if applies else [],
            "unresolved": [], "evaluator": evaluator,
        }
    return {**draft, "checklist": {"decision_id": found["decision_id"], "candidate": draft["candidate"],
                                   "reference_set_sha256": draft["reference_set_sha256"], "results": items}}


@pytest.fixture
def checklist_project(discovery_project):
    policy, proposal, prepare, update, authorize = discovery_project
    policy["checklist"] = True
    update()
    return policy, proposal, prepare, update, authorize


def test_valid_checklist_binds_candidate_and_review(tmp_path, checklist_project):
    _, proposal, prepare, _, authorize = checklist_project
    found = record_decision(tmp_path, prepare)
    resolved = evaluate(tmp_path, found)
    definition = resolved["reference_set"]["checklist"]
    assert set(definition["categories"]) == {"api", "global"}
    assert len(definition["checks"]) == 15
    assert definition["checks"]["API-04"]["related_xids"] == [GLOBAL]
    assert definition["checks"]["GDC-10"]["knowledge_gaps"]
    draft = checklist_proposal(proposal, found, resolved)
    authorize(found, draft)
    assert finalize(tmp_path, draft)["state"] == "DETERMINED"
    receipt = require_decision(tmp_path, "WI-1", "retry", "ED-1")
    assert len(receipt["checklist_sha256"]) == 64
    assert receipt["candidate"] == draft["checklist"]["candidate"]


@pytest.mark.parametrize("omitted", ["API-01", "API-04", "GDC-03", "GDC-07"])
def test_review_rejects_missing_checks_on_original_draft(tmp_path, checklist_project, omitted):
    _, proposal, prepare, _, _ = checklist_project
    proposal["candidate"] = pinned(tmp_path, "design.md", OMITTED_DESIGNS[omitted])
    found = record_decision(tmp_path, prepare)
    draft = checklist_proposal(proposal, found, evaluate(tmp_path, found))
    del draft["checklist"]["results"][omitted]
    with pytest.raises(ValueError, match=f"{omitted}=MISSING"):
        record_decision(tmp_path, {"action": "review", "decision_id": "ED-1", "proposal": draft})
    with pytest.raises(ValueError, match=f"{omitted}=MISSING"):
        finalize(tmp_path, draft)


@pytest.mark.parametrize("concurrency", ["no", "unknown", "yes"])
def test_state_attributes_add_checks_and_detect_concurrency_omission(tmp_path, checklist_project, concurrency):
    policy, proposal, prepare, update, _ = checklist_project
    policy["catalog"][GLOBAL]["discovery"] = metadata(
        "responsibility dependencies change_impact consistency invariants transactions contention exclusion visibility")
    update()
    context = discovery_context(category="architecture_change", state_management="yes", concurrency=concurrency)
    proposal["candidate"] = pinned(tmp_path, "design.md",
                                   "Workers read status, calculate a new status, then overwrite it.")
    found = record_decision(tmp_path, {**prepare, "decision_context": context})
    resolved = evaluate(tmp_path, found)
    selection = resolved["reference_set"]["checklist"]
    assert set(selection["categories"]) == {"architecture", "state", "concurrency", "global"}
    assert selection["checks"]["CON-02"]["applicability"]["applies"] == (concurrency != "no")
    draft = checklist_proposal(proposal, found, resolved)
    del draft["checklist"]["results"]["CON-01"]
    with pytest.raises(ValueError, match="CON-01=MISSING"):
        finalize(tmp_path, draft)


@pytest.mark.parametrize("status", ["UNKNOWN", "FAIL"])
def test_pending_findings_reject_use_but_survive_blocked(tmp_path, checklist_project, status):
    _, proposal, prepare, _, _ = checklist_project
    found = record_decision(tmp_path, prepare)
    draft = checklist_proposal(proposal, found, evaluate(tmp_path, found))
    draft["checklist"]["results"]["API-01"].update(result=status, unresolved=["Provider result not established"])
    with pytest.raises(ValueError, match=f"API-01={status}"):
        finalize(tmp_path, draft)
    assert finalize(tmp_path, {**draft, "classification": "BLOCKED", "actions": []})["state"] == "BLOCKED"
    code, output = command("workflow", "engineering-decision", "--root", str(tmp_path), "--inspect", "ED-1")
    assert code == 0 and json.loads(output)["checklist_pending"] == {"API-01": status}
    with pytest.raises(ValueError, match="DETERMINED"):
        require_decision(tmp_path, "WI-1", "retry", "ED-1")


def test_required_api_check_refuses_nonapplicability_even_with_reason(tmp_path, checklist_project):
    _, proposal, prepare, _, _ = checklist_project
    found = record_decision(tmp_path, prepare)
    draft = checklist_proposal(proposal, found, evaluate(tmp_path, found))
    draft["checklist"]["results"]["API-04"].update(result="NOT_APPLICABLE", applicability="not_applicable",
                                                  reason="The producer says it is unnecessary")
    with pytest.raises(ValueError, match="API-04.*applicability"):
        finalize(tmp_path, draft)
    draft["checklist"]["results"]["API-04"]["reason"] = ""
    with pytest.raises(ValueError, match="API-04.*reason"):
        finalize(tmp_path, draft)


def test_checklist_evaluator_cannot_act_as_independent_reviewer(tmp_path, checklist_project):
    _, proposal, prepare, _, authorize = checklist_project
    found = record_decision(tmp_path, prepare)
    draft = checklist_proposal(proposal, found, evaluate(tmp_path, found), evaluator="reviewer")
    authorize(found, draft)
    with pytest.raises(ValueError, match="independent review"):
        finalize(tmp_path, draft)


def test_serial_state_can_record_reasoned_nonapplicability(tmp_path, checklist_project):
    policy, proposal, prepare, update, authorize = checklist_project
    policy["catalog"][GLOBAL]["discovery"] = metadata("consistency invariants transactions")
    update()
    found = record_decision(tmp_path, {**prepare, "decision_context": discovery_context(
        category="state_management", state_management="yes", concurrency="no")})
    draft = checklist_proposal(proposal, found, evaluate(tmp_path, found))
    na = draft["checklist"]["results"]["CON-02"]
    assert na["result"] == "NOT_APPLICABLE"
    na["reason"] = ""
    with pytest.raises(ValueError, match="CON-02.*reason"):
        finalize(tmp_path, draft)
    na["reason"] = "An exclusive single writer is verified by the integration test"
    authorize(found, draft)
    assert finalize(tmp_path, draft)["state"] == "DETERMINED"


def test_definition_change_requires_new_selection(tmp_path, checklist_project, monkeypatch):
    _, proposal, prepare, _, authorize = checklist_project
    found = record_decision(tmp_path, prepare)
    draft = checklist_proposal(proposal, found, evaluate(tmp_path, found))
    authorize(found, draft)
    finalize(tmp_path, draft)
    definitions = json.loads(decision_checklist.DEFINITIONS.read_bytes())
    definitions["revision"] = "future"
    replacement = tmp_path / "checklist-definition.json"
    replacement.write_text(json.dumps(definitions), encoding="utf-8")
    monkeypatch.setattr(decision_checklist, "DEFINITIONS", replacement)
    with pytest.raises(ValueError, match="checklist definition changed"):
        require_decision(tmp_path, "WI-1", "retry", "ED-1")


@pytest.mark.parametrize("change", ["candidate", "decision", "xid", "evidence"])
def test_stale_checklist_rejected_after_changes(tmp_path, checklist_project, change):
    policy, proposal, prepare, update, authorize = checklist_project
    found = record_decision(tmp_path, prepare)
    draft = checklist_proposal(proposal, found, evaluate(tmp_path, found))
    if change == "evidence":
        proof = pinned(tmp_path, "idempotency.md", "Synthetic checklist evidence")
        draft["checklist"]["results"]["API-04"]["evidence"] = [proof]
    authorize(found, draft)
    finalize(tmp_path, draft)
    if change == "decision":
        found = record_decision(tmp_path, {**prepare, "decision_id": "ED-2", "supersedes": "ED-1",
                                           "decision_context": discovery_context(target="Changed target")})
        resolved = evaluate(tmp_path, found)
        altered = {**draft, "reference_set_sha256": resolved["reference_set_sha256"]}
        with pytest.raises(ValueError, match="checklist must bind"):
            record_decision(tmp_path, {"action": "review", "decision_id": "ED-2", "proposal": altered})
    elif change == "xid":
        policy["catalog"][GLOBAL]["revision"] = "r2"
        update()
    elif change == "candidate":
        (tmp_path / "design.md").write_text("New candidate", encoding="utf-8")
    else:
        (tmp_path / "idempotency.md").write_text("New evidence", encoding="utf-8")
    with pytest.raises(ValueError, match="superseded|context changed|digest mismatch"):
        require_decision(tmp_path, "WI-1", "retry", "ED-1")


def test_non_enrolled_gate_retains_proposal_shape(tmp_path, discovery_project):
    policy, proposal, prepare, update, authorize = discovery_project
    found = record_decision(tmp_path, prepare)
    draft = proposal_with(proposal, evaluate(tmp_path, found))
    authorize(found, draft)
    finalize(tmp_path, draft)
    assert "checklist_sha256" not in require_decision(tmp_path, "WI-1", "retry", "ED-1")
    policy["checklist"] = True
    update()
    with pytest.raises(ValueError, match="checklist policy changed"):
        require_decision(tmp_path, "WI-1", "retry", "ED-1")
