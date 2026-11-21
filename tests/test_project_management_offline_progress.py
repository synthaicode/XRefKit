import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest

# The release compatibility suite also runs against published wheels. These
# tests cover the new source module before it is present in any published wheel.
MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "packages" / "xrefkit-skills-project-management"
    / "src" / "xrefkit_skills_project_management" / "offline_progress.py"
)
SPEC = importlib.util.spec_from_file_location("project_management_offline_progress", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
OfflinePolicy = MODULE.OfflinePolicy
TransitionEvidence = MODULE.TransitionEvidence
TransitionRequest = MODULE.TransitionRequest
evaluate_offline_transition = MODULE.evaluate_offline_transition


POLICY = OfflinePolicy(
    project="epic", revision="policy-r1", approval_ref="decision/1",
    scope="synthetic", transitions=("start", "review", "accept", "handoff"),
)
START = TransitionRequest(
    project="epic", scope="synthetic", work_id="issue/202", work_revision="work-r1",
    transition="start", offline=True,
    human_decision_refs=(),
)
READY = TransitionEvidence("readiness", "epic", "synthetic", "issue/202", "work-r1", "check/readiness", True)
VERIFIED = replace(READY, check="verification", record_ref="check/tests", candidate="candidate-1")
REVIEWED = TransitionEvidence(
    "independent_review", "epic", "synthetic", "issue/202", "work-r1",
    "check/review", True, "candidate-1", True,
)


def test_ordinary_start_uses_existing_policy_without_another_approval():
    result = evaluate_offline_transition(START, POLICY, (READY,))
    assert result.outcome == "proceed"
    assert result.request == START
    assert result.approval_ref == "decision/1"
    assert result.policy_revision == "policy-r1"
    assert result.evidence_refs == ("check/readiness",)


@pytest.mark.parametrize(
    ("request_change", "policy_change"),
    [
        ({"human_decision_refs": ("D202-6",)}, {}),
        ({"offline": False}, {}),
        ({"scope": "live"}, {}),
        ({"project": "other"}, {}),
        ({}, {"transitions": ("handoff",)}),
        ({}, {"approval_ref": ""}),
    ],
)
def test_human_authority_is_not_inferred(request_change, policy_change):
    result = evaluate_offline_transition(
        replace(START, **request_change), replace(POLICY, **policy_change), (READY,),
    )
    assert result.outcome == "human_decision"


def test_missing_policy_routes_to_human_decision():
    assert evaluate_offline_transition(START, None, (READY,)).outcome == "human_decision"


def test_missing_factual_evidence_routes_to_existing_owner():
    assert evaluate_offline_transition(START, POLICY, ()).outcome == "await_evidence"
    request = replace(START, offline=None)
    assert evaluate_offline_transition(request, POLICY, (READY,)).outcome == "await_evidence"
    request = replace(START, human_decision_refs=None)
    assert evaluate_offline_transition(request, POLICY, (READY,)).outcome == "await_evidence"


@pytest.mark.parametrize("change", [{"work_id": "issue/203"}, {"project": "other"}, {"scope": "other"}])
def test_other_work_or_scope_cannot_supply_evidence_at_the_same_revision(change):
    evidence = replace(READY, **change)
    assert evaluate_offline_transition(START, POLICY, (evidence,)).outcome == "await_evidence"


def test_review_and_handoff_need_the_exact_upstream_evidence():
    review = replace(START, transition="review", candidate="candidate-1")
    assert evaluate_offline_transition(review, POLICY, (VERIFIED,)).outcome == "proceed"
    handoff = replace(review, transition="handoff")
    assert evaluate_offline_transition(handoff, POLICY, (VERIFIED, REVIEWED)).outcome == "await_evidence"
    accepted = replace(VERIFIED, check="acceptance", record_ref="record/accept")
    assert evaluate_offline_transition(handoff, POLICY, (accepted,)).outcome == "proceed"


@pytest.mark.parametrize(
    "unresolved",
    [
        (),
        (replace(REVIEWED, candidate="candidate-0"),),
        (replace(REVIEWED, work_revision="work-r0"),),
        (replace(REVIEWED, passed=False),),
        (replace(REVIEWED, independent=False),),
        (REVIEWED, replace(REVIEWED, record_ref="check/conflict", passed=False)),
    ],
)
def test_acceptance_waits_for_a_single_current_independent_pass(unresolved):
    request = replace(START, transition="accept", candidate="candidate-1")
    result = evaluate_offline_transition(request, POLICY, (VERIFIED, *unresolved))
    assert result.outcome == "await_evidence"
    assert result.unresolved == ("independent_review",)
    assert evaluate_offline_transition(request, POLICY, (VERIFIED, REVIEWED)).outcome == "proceed"
