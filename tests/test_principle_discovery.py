import json

import pytest

from test_engineering_decision import finalize, pinned, project
from test_subagent_startup import command
from xrefkit.engineering_decision import record_decision, require_decision


GLOBAL = "111111AAAAAA"
PROJECT = "222222BBBBBB"
IDEMPOTENCY = "333333CCCCCC"
IRRELEVANT = "444444DDDDDD"


def discovery_context(**overrides):
    return {"category": "api_integration", "target": "Timeout response",
            "requirements": ["REQ-1"], "constraints": ["No duplicate charge"],
            "assumptions": ["Timeout may occur before the response"],
            "external_side_effects": "no", "state_management": "no", "concurrency": "no",
            "failure_impact": "Caller cannot determine the result", "existing_xids": [],
            "related_decision_ids": [], "candidate": None, **overrides}


def metadata(areas, conditions="Applies within the declared contract", related=()):
    return {"areas": areas.split(), "conditions": conditions, "source": "Synthetic approved catalog",
            "related_xids": list(related)}


def enable_discovery(policy):
    policy["discovery"] = True
    policy["catalog"][GLOBAL]["discovery"] = metadata("contract failure idempotency external_side_effects")
    policy["catalog"][PROJECT]["discovery"] = metadata("contract")


def add_reference(root, policy, xid, areas, conditions="Applies to external non-idempotent operations", related=()):
    policy["catalog"][xid] = {"kind": "global", "revision": "r1",
                              **pinned(root, f"{xid}.md", f"<!-- xid: {xid} -->\n# Policy {xid}"),
                              "discovery": metadata(areas, conditions, related)}


@pytest.fixture
def discovery_project(project):
    policy, proposal, prepare, update, authorize = project
    enable_discovery(policy)
    update()
    return policy, proposal, {**prepare, "decision_context": discovery_context()}, update, authorize


def evaluate(root, prepared, overrides=None, conflicts=None):
    basis = {xid: {"applicability": "applies", "reason": "The approved scope matches REQ-1"}
             for xid in prepared["principle_discovery"]["matches"]}
    basis.update(overrides or {})
    result = record_decision(root, {"action": "resolve", "decision_id": prepared["decision_id"],
                                   "basis": basis, "conflicts": conflicts or []})
    return result


def proposal_with(proposal, evaluated):
    return {**proposal, "basis": evaluated["reference_set"]["basis"],
            "reference_set_sha256": evaluated["reference_set_sha256"],
            "alternatives": [{"option": "Return pending", "assessment": "Preserves operation identity"}]}


def test_t1_configured_references_suffice_with_discovery_enabled(tmp_path, discovery_project):
    _, proposal, prepare, _, authorize = discovery_project
    found = record_decision(tmp_path, prepare)
    assert found == record_decision(tmp_path, prepare)
    assert found["searched_at"].endswith("+00:00")
    resolved = evaluate(tmp_path, found)
    assert resolved["reference_set"]["discovered_xids"] == []
    proposed = proposal_with(proposal, resolved)
    authorize(found, proposed)
    finalize(tmp_path, proposed)
    receipt = require_decision(tmp_path, "WI-1", "manufacturing", "ED-1")
    assert receipt["reference_set_sha256"] == resolved["reference_set_sha256"]


def test_t2_t3_t8_api_discovers_idempotency_without_keyword_and_records_nonapplicability(tmp_path, discovery_project):
    policy, proposal, prepare, update, authorize = discovery_project
    add_reference(tmp_path, policy, IDEMPOTENCY, "idempotency unknown_outcome consistency",
                  related=[IRRELEVANT])
    add_reference(tmp_path, policy, IRRELEVANT, "", "Only applies when a distributed unit commits")
    update()
    context = discovery_context(external_side_effects="yes")
    found = record_decision(tmp_path, {**prepare, "question": "What should timeout return?", "decision_context": context})
    assert "area:idempotency" in found["principle_discovery"]["matches"][IDEMPOTENCY]
    assert f"related_xid:{IDEMPOTENCY}" in found["principle_discovery"]["matches"][IRRELEVANT]
    assert found["references"][IDEMPOTENCY]["discovery"]["conditions"]
    resolved = evaluate(tmp_path, found, {
        IRRELEVANT: {"applicability": "not_applicable", "reason": "The service never commits a distributed unit"},
    })
    assert IDEMPOTENCY in resolved["reference_set"]["required"]
    assert resolved["reference_set"]["not_applicable"] == [IRRELEVANT]
    proposed = proposal_with(proposal, resolved)
    authorize(found, proposed)
    finalize(tmp_path, proposed)
    assert require_decision(tmp_path, "WI-1", "retry", "ED-1")["state"] == "DETERMINED"
    code, output = command("workflow", "engineering-decision", "--root", str(tmp_path), "--inspect", "ED-1")
    assert code == 0, output
    assert json.loads(output)["reference_set"] == resolved["reference_set"]


def test_t4_unknown_side_effects_and_unavailable_reference_remain_unresolved(tmp_path, discovery_project):
    policy, proposal, prepare, update, _ = discovery_project
    policy["catalog"].pop(PROJECT)
    add_reference(tmp_path, policy, IDEMPOTENCY, "idempotency unknown_outcome consistency")
    update()
    found = record_decision(tmp_path, {**prepare, "decision_context": discovery_context(external_side_effects="unknown")})
    assert PROJECT in found["unresolved_xids"]
    with pytest.raises(ValueError, match="must remain unresolved"):
        evaluate(tmp_path, found, {PROJECT: {"applicability": "not_applicable", "reason": "Cannot read"}})
    unresolved = evaluate(tmp_path, found, {
        PROJECT: {"applicability": "unresolved", "reason": "Project policy unavailable"},
        IDEMPOTENCY: {"applicability": "unresolved", "reason": "Side effects are unknown"},
    })
    assert unresolved["reference_set"]["unknown_flags"] == ["external_side_effects"]
    assert set(unresolved["reference_set"]["unresolved"]) == {PROJECT, IDEMPOTENCY}
    proposed = proposal_with(proposal, unresolved)
    with pytest.raises(ValueError, match="verified global principles"):
        finalize(tmp_path, proposed)
    finalize(tmp_path, {**proposed, "classification": "BLOCKED", "actions": []})


@pytest.mark.parametrize("status", ["resolved", "unresolved"])
def test_t5_conflicting_principles_are_compared_against_requirements(tmp_path, discovery_project, status):
    policy, proposal, prepare, update, authorize = discovery_project
    add_reference(tmp_path, policy, IDEMPOTENCY, "responsibility dependencies", "Avoid duplication")
    add_reference(tmp_path, policy, IRRELEVANT, "dependencies change_impact", "Keep modules loosely coupled")
    update()
    found = record_decision(tmp_path, {**prepare, "decision_context": discovery_context(category="architecture_change")})
    conflict = {"xids": [IDEMPOTENCY, IRRELEVANT], "status": status, "requirements": ["REQ-1"],
                "reason": "Keep operation identity local to the owning module and tolerate duplicated mapping"}
    resolved = evaluate(tmp_path, found, conflicts=[conflict])
    assert resolved["reference_set"]["conflicts"] == [conflict]
    proposed = proposal_with(proposal, resolved)
    if status == "unresolved":
        with pytest.raises(ValueError, match="applicability or conflicts"):
            finalize(tmp_path, proposed)
    else:
        authorize(found, proposed)
        assert finalize(tmp_path, proposed)["state"] == "DETERMINED"


def test_t6_t10_configured_xids_cannot_be_omitted_or_rewritten(tmp_path, discovery_project):
    _, proposal, prepare, _, _ = discovery_project
    found = record_decision(tmp_path, prepare)
    with pytest.raises(ValueError, match="resolved before"):
        finalize(tmp_path, {**proposal, "reference_set_sha256": "a" * 64, "alternatives": []})
    code, output = command("workflow", "run", "--root", str(tmp_path), "--work-item-id", "WI-1",
                           "--engineering-action", "manufacturing", "--engineering-decision-id", "ED-1",
                           "--engineering-candidate", "design.md", "--task", "Synthetic dispatch",
                           "--use-default-completion-conditions", "--out", "must-not-open.md", "--json")
    assert code == 1 and "DETERMINED" in output
    assert not (tmp_path / "must-not-open.md").exists()
    with pytest.raises(ValueError, match="every discovered and configured"):
        record_decision(tmp_path, {"action": "resolve", "decision_id": "ED-1", "basis": {}, "conflicts": []})
    resolved = evaluate(tmp_path, found, {
        PROJECT: {"applicability": "not_applicable", "reason": "The rule is scoped to signed outbound calls"},
    })
    assert PROJECT in resolved["reference_set"]["configured_xids"]
    assert PROJECT in resolved["reference_set"]["not_applicable"]
    proposed = proposal_with(proposal, resolved)
    del proposed["basis"][PROJECT]
    with pytest.raises(ValueError, match="preserve the resolved"):
        finalize(tmp_path, proposed)


def test_t7_artifact_and_relevant_knowledge_changes_invalidate_without_unrelated_rank_drift(tmp_path, discovery_project):
    policy, proposal, prepare, update, authorize = discovery_project
    found = record_decision(tmp_path, prepare)
    proposed = proposal_with(proposal, evaluate(tmp_path, found))
    authorize(found, proposed)
    finalize(tmp_path, proposed)
    add_reference(tmp_path, policy, IRRELEVANT, "visibility")
    update()
    assert require_decision(tmp_path, "WI-1", "retry", "ED-1")["state"] == "DETERMINED"
    (tmp_path / "design.md").write_text("Changed candidate", encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        require_decision(tmp_path, "WI-1", "retry", "ED-1")
    add_reference(tmp_path, policy, IDEMPOTENCY, "idempotency")
    update()
    with pytest.raises(ValueError, match="coverage changed"):
        require_decision(tmp_path, "WI-1", "retry", "ED-1")
    revised = {**prepare, "decision_id": "ED-2", "supersedes": "ED-1",
               "decision_context": discovery_context(related_decision_ids=["ED-1"])}
    assert record_decision(tmp_path, revised)["state"] == "prepared"
    with pytest.raises(ValueError, match="superseded"):
        require_decision(tmp_path, "WI-1", "retry", "ED-1")


def test_t10_enrollment_needs_discovery_context_and_blocks_uncovered_area(tmp_path, discovery_project):
    policy, proposal, prepare, update, _ = discovery_project
    legacy = {k: v for k, v in prepare.items() if k != "decision_context"}
    with pytest.raises(ValueError, match="prepare command"):
        record_decision(tmp_path, legacy)
    policy["catalog"][GLOBAL]["discovery"]["areas"].remove("idempotency")
    update()
    found = record_decision(tmp_path, prepare)
    resolved = evaluate(tmp_path, found)
    assert resolved["reference_set"]["uncovered_areas"] == ["idempotency"]
    with pytest.raises(ValueError, match="unresolved principle coverage"):
        finalize(tmp_path, proposal_with(proposal, resolved))


def test_t11_enabling_discovery_preserves_history_but_requires_new_prepare_for_use(tmp_path, project):
    policy, proposal, prepare, update, authorize = project
    found = record_decision(tmp_path, prepare)
    authorize(found)
    finalize(tmp_path, proposal)
    assert require_decision(tmp_path, "WI-1", "manufacturing", "ED-1")["state"] == "DETERMINED"
    enable_discovery(policy)
    update()
    with pytest.raises(ValueError, match="discovery policy changed"):
        require_decision(tmp_path, "WI-1", "manufacturing", "ED-1")
    code, output = command("workflow", "engineering-decision", "--root", str(tmp_path), "--inspect", "ED-1")
    assert code == 0 and json.loads(output)["proposal"] == proposal
