"""Cross-package design review contract, run against installed distributions."""

from dataclasses import replace

import pytest

from xrefkit_skills_brownfield.design_review import make_finding, retry_disposition
from xrefkit_skills_project_management.design_review import receive_finding, resume_blockers
from xrefkit_skills_project_management.offline_progress import (
    OfflinePolicy, TransitionEvidence, TransitionRequest, evaluate_offline_transition,
)
from xrefkit_skills_project_management.schedule import assess_impact


PRINCIPLE = {
    "xid": "B4F1C8D2A609", "revision": "design-r1", "ref": "record:rule-1",
    "applicability": "same authorized execution operation",
}


def finding(cause, **changes):
    inputs = dict(
        work_item_id="#206", work_revision="r6", finding_id="finding-1",
        source_run_id="brownfield-1", observation="recorded discrepancy",
        cause=cause, evidence_refs=["review:1"], rationale="comparison with installed policy",
        confidence="high", principle_refs=[PRINCIPLE], policy_gaps=["affected policy"],
        related_issues=["#203", "#207"], approval_roles=["design owner"],
    )
    inputs.update(changes)
    return make_finding(**inputs)


def receive(value, **changes):
    return receive_finding(value, **({"work_item_id": "#206", "work_revision": "r6"} | changes))


@pytest.mark.parametrize(("cause", "outcome", "action", "phase"), [
    ("IMPLEMENTATION_DEFECT", "IMPLEMENTATION_FIX", "coordinate_existing_execution", "manufacturing"),
    ("DESIGN_POLICY_MISSING", "DESIGN_REVIEW_REQUIRED", "hold_execution_and_request_reevaluation", "design"),
    ("DESIGN_POLICY_CONFLICT", "DESIGN_REVIEW_REQUIRED", "hold_execution_and_request_reevaluation", "design"),
    ("DESIGN_POLICY_INVALID", "DESIGN_REVIEW_REQUIRED", "hold_execution_and_request_reevaluation", "design"),
    ("REQUIREMENT_CHANGE", "DESIGN_REVIEW_REQUIRED", "hold_execution_and_request_reevaluation", "requirements"),
    ("INSUFFICIENT_EVIDENCE", "INVESTIGATION_REQUIRED", "coordinate_evidence_collection", "investigation"),
])
def test_handoff_routes(cause, outcome, action, phase):
    record = finding(cause, unknowns=["obtain original observation from owner"])
    assert record["outcome"] == outcome
    assert record["next_phase"] == phase
    action_record = receive(record)
    assert action_record["action"] == action
    assert action_record["finding"]["principle_refs"] == [PRINCIPLE]
    assert action_record["related_issues_to_check"] == ["#203", "#207"]


def test_evidence_and_owner_fail_closed():
    with pytest.raises(ValueError, match="require evidence"):
        finding("DESIGN_POLICY_MISSING", evidence_refs=[])
    with pytest.raises(ValueError, match="require evidence"):
        finding("DESIGN_POLICY_CONFLICT", confidence="low")
    with pytest.raises(ValueError, match="requires explicit gaps"):
        finding("INSUFFICIENT_EVIDENCE")
    value = finding("DESIGN_POLICY_MISSING", approval_roles=[])
    assert receive(value)["resolve_approval_owner"]


@pytest.mark.parametrize(("changed", "result"), [
    ({"failure": "authentication"}, "stop"),
    ({"failure": "contract_violation", "transient": False}, "evaluate_contract"),
    ({"failure": "timeout", "effect": "unknown", "safe_replay": False}, "reconcile"),
    ({"failure": "timeout", "effect": "unknown", "safe_replay": True}, "bounded_retry"),
    ({"recovery_basis": ""}, "investigate"),
    ({"within_limits": False}, "stop"),
    ({}, "bounded_retry"),
])
def test_operation_failure_gate(changed, result):
    recovered = dict(
        failure="transport", preconditions=True, transient=True,
        recovery_basis="read-only transient fault now cleared", effect="not_executed",
        safe_replay=False, within_limits=True, can_continue_safely=True,
    )
    assert retry_disposition(**(recovered | changed)) == result


def test_duplicates_and_stale_work_do_not_propose_another_hold():
    first = finding("DESIGN_POLICY_CONFLICT")
    assert receive(first)["action"] == "hold_execution_and_request_reevaluation"
    assert receive(first, existing_findings=[first])["action"] == "reuse"
    with pytest.raises(ValueError, match="conflicting"):
        receive(first | {"observation": "unexpected rewrite"}, existing_findings=[first])
    with pytest.raises(ValueError, match="current Work Item"):
        receive(first, work_revision="r7")


def test_design_review_can_resume_only_through_existing_start_gate():
    assert receive(finding("DESIGN_POLICY_MISSING"))["action"].startswith("hold_execution")
    criteria = dict(
        verified_current_design=True, verified_required_approval=False, impact_reviewed=True,
        acceptance_current=True, hold_resolved=False, work_start_authorized=False,
    )
    blockers = resume_blockers(**criteria)
    assert blockers == ("required_approval", "hold_resolution", "work_start_authority")
    request = TransitionRequest("project", "offline", "#206", "r7", "start", True, human_decision_refs=blockers)
    policy = OfflinePolicy("project", "r1", "start-approval", "offline", ("start",))
    evidence = (TransitionEvidence("readiness", "project", "offline", "#206", "r7", "check:readiness", True),)
    assert evaluate_offline_transition(request, policy, evidence).outcome == "human_decision"
    reviewed = criteria | dict(verified_required_approval=True, hold_resolved=True)
    assert resume_blockers(**reviewed) == ("work_start_authority",)
    ready = resume_blockers(**(reviewed | {"work_start_authorized": True}))
    assert evaluate_offline_transition(replace(request, human_decision_refs=ready), policy, evidence).outcome == "proceed"


def test_design_impact_keeps_related_candidates_and_uses_existing_assessment():
    import json

    from xrefkit_skills_brownfield import package_root
    from xrefkit_skills_brownfield.understanding import analyze_understanding

    finding_record = finding("DESIGN_POLICY_MISSING")
    assert receive(finding_record)["related_issues_to_check"] == ["#203", "#207"]
    current = json.loads((package_root() / "examples/understanding-r001.json").read_text(encoding="utf-8"))
    notification = analyze_understanding(current)["notification"]
    execution = {
        "schema_version": 1, "plan_id": "issue206", "kind": "execution", "start": "2026-11-22",
        "calendar": {"working_weekdays": [0, 1, 2, 3, 4], "holidays": []}, "rules_ref": "rules/r1",
        "tasks": [
            {"id": identity, "label": identity, "duration": 1, "depends_on": dependencies,
             "requirement_xids": [xid], "evidence_refs": [], "decision_refs": [],
             "hold_refs": [], "work_ref": "#203" if identity == "migrate" else "#207"}
            for identity, xid, dependencies in (
                ("migrate", "ABCDEF123456", []),
                ("verify", "111111111111", [{"task": "migrate", "type": "FS", "lag": 0}]),
            )
        ],
    }
    result = assess_impact(execution, notification)
    assert result["direct_tasks"] == ["migrate"]
    assert result["dependent_tasks"] == ["verify"]
    assert result["readiness"] == "not_evaluated"
    assert result["schedule_changed"] is False
