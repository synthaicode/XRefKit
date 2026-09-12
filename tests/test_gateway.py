import copy
import json

import pytest
from pydantic import ValidationError

from xrefkit.cli import main
from xrefkit.gateway import AXES, Assessment, Feedback, Policy, evaluate, route, snapshot


@pytest.fixture
def request_and_policy(tmp_path):
    instruction = tmp_path / "instruction.txt"
    skill = tmp_path / "meta.md"
    profile = tmp_path / "existing-profile.md"
    instruction.write_text("Compare the orthogonal array; change only section A.", encoding="utf-8")
    skill.write_text("Compare the sources and preserve scope.", encoding="utf-8")
    profile.write_text("Prefer Japanese explanations.", encoding="utf-8")
    refs = [{"source_id": "instruction", "locator": "line 1"}]
    assessment = {"version": 1, "request_id": "request-1", "revision": 0,
                  "environment": "vscode:test",
                  "instruction": instruction.read_text(encoding="utf-8"),
                  "sources": [snapshot(instruction, "instruction", "instruction"),
                              snapshot(skill, "skill", "skill"), snapshot(profile, "profile", "profile")],
                  "unresolved": [], "steps": [
                      {"id": "count", "kind": "deterministic", "task": "Count combinations",
                       "scope": "section A", "evidence": refs, "tool_ref": "existing-counter"},
                      {"id": "interpret", "kind": "model", "task": "Compare",
                       "scope": "section A only", "evidence": refs, "depends_on": ["count"],
                       "execution_kind": "implementation",
                       "capabilities": ["orthogonal_array", "incremental_scope"],
                       "metrics": {axis: {"value": 1, "basis": "estimated", "evidence": refs}
                                   for axis in AXES}}]}
    policy = {"version": "trial-1", "host": "vscode_copilot", "parent_cost_tier": 3,
              "parent_model_id": "gateway-parent",
              "environment": "vscode:test",
              "candidates": [
                  {"id": "cheap", "priority": 0, "cost_tier": 1,
                   "capabilities": ["incremental_scope"], "limits": dict.fromkeys(AXES, 10),
                   "evaluation_ref": "fixture-small", "max_input_bytes": 10000},
                  {"id": "capable", "priority": 1, "cost_tier": 3,
                   "capabilities": ["incremental_scope", "orthogonal_array"],
                   "limits": dict.fromkeys(AXES, 10), "evaluation_ref": "fixture-array",
                   "max_input_bytes": 10000}]}
    return assessment, policy


def run_pair(pair):
    return route(Assessment.model_validate(pair[0]), Policy.model_validate(pair[1]))


def test_capability_excludes_cheapest_and_leaves_tools_unassigned(request_and_policy):
    result = run_pair(request_and_policy)
    assert result["status"] == "ready"
    assert result["decisions"][0] == {"step_id": "count", "kind": "deterministic", "tool_ref": "existing-counter"}
    assert result["decisions"][1]["model"] == "capable"
    assert result["dispatch_status"] == "subagent_dispatch_required"
    assert result["subagent_dispatches"] == [{
        "step_id": "interpret",
        "parent_model": "gateway-parent",
        "selected_model": "capable",
        "agent_role": "implementation_subagent",
        "rationale": "The step is classified as implementation and the evaluated policy selected capable; the parent remains the gateway/coordinator.",
        "parent_execution": "prohibited",
        "dispatch_owner": "client_host",
    }]


def test_analysis_does_not_require_implementation_subagent_dispatch(request_and_policy):
    assessment, policy = request_and_policy
    assessment["steps"][1]["execution_kind"] = "analysis"
    result = run_pair((assessment, policy))
    assert result["status"] == "ready"
    assert result["dispatch_status"] == "not_dispatched"
    assert result["subagent_dispatches"] == []


def test_implementation_requires_recorded_parent_model(request_and_policy):
    assessment, policy = request_and_policy
    policy["host"] = "generic"
    policy["parent_model_id"] = None
    policy["parent_cost_tier"] = None
    result = run_pair((assessment, policy))
    assert result["status"] == "needs_assessment"
    assert "parent_model_id is required before implementation subagent dispatch" in result["issues"]
    assert result["subagent_dispatches"] == []


@pytest.mark.parametrize("problem", ["unknown", "scope", "capacity", "stale", "instruction"])
def test_routing_cannot_hide_missing_or_changed_requirements(request_and_policy, problem):
    assessment, policy = request_and_policy
    if problem == "unknown":
        assessment["steps"][1]["metrics"]["scope_changes"].update(value=None, basis="unknown")
    elif problem == "scope":
        assessment["unresolved"] = None
    elif problem == "capacity":
        policy["candidates"][1]["max_input_bytes"] = 1
    elif problem == "instruction":
        assessment["instruction"] = "Changed instruction without a source snapshot"
    else:
        from pathlib import Path
        Path(assessment["sources"][2]["path"]).write_text("changed preference", encoding="utf-8")
    assert run_pair((assessment, policy))["status"] == "needs_assessment"


def test_parent_tier_block_returns_conversation_upgrade_proposal(request_and_policy):
    assessment, policy = request_and_policy
    policy["parent_cost_tier"] = 1
    result = run_pair((assessment, policy))
    assert result["status"] == "conversation_upgrade_required"
    assert result["dispatch_status"] == "not_dispatched"
    assert result["conversation_upgrade"] == {
        "proposal_only": True,
        "action": "user_selects_conversation_model",
        "current_conversation_model": "gateway-parent",
        "current_cost_tier": 1,
        "required_minimum_tier": 3,
        "affected_steps": ["interpret"],
        "workers_callable_after_upgrade": [{
            "step_id": "interpret", "model": "capable", "cost_tier": 3,
            "evaluation_ref": "fixture-array"}],
        "reason": "evaluated workers satisfy task requirements but exceed the current conversation cost tier",
        "resume": {"request_id": "request-1", "revision": 0,
                   "tool": "route_instruction_gateway",
                   "rule": "select a conversation model at or above required_minimum_tier, refresh source snapshots, update the environment policy, and rerun routing"},
    }


def test_upgrade_tier_covers_every_blocked_step(request_and_policy):
    assessment, policy = copy.deepcopy(request_and_policy)
    assessment["steps"].append({
        **copy.deepcopy(assessment["steps"][1]), "id": "deep-review",
        "depends_on": ["interpret"], "capabilities": ["deep_review"]})
    policy["candidates"].append({
        "id": "reviewer", "priority": 0, "cost_tier": 4,
        "capabilities": ["deep_review"], "limits": dict.fromkeys(AXES, 10),
        "evaluation_ref": "fixture-review", "max_input_bytes": 10000})
    policy["parent_cost_tier"] = 1
    result = run_pair((assessment, policy))
    assert result["status"] == "conversation_upgrade_required"
    assert result["conversation_upgrade"]["required_minimum_tier"] == 4
    assert {row["step_id"] for row in result["conversation_upgrade"]["workers_callable_after_upgrade"]} == {
        "interpret", "deep-review"}


def test_upgrade_is_not_proposed_when_capability_is_missing(request_and_policy):
    assessment, policy = request_and_policy
    policy["parent_cost_tier"] = 0
    for candidate in policy["candidates"]:
        candidate["capabilities"] = []
    result = run_pair((assessment, policy))
    assert result["status"] == "needs_assessment"
    assert result["conversation_upgrade"] is None


def test_copilot_policy_requires_current_conversation_model(request_and_policy):
    _, policy = request_and_policy
    policy["parent_model_id"] = None
    with pytest.raises(ValidationError, match="parent_model_id"):
        Policy.model_validate(policy)


def test_upgrade_cli_is_nonready(request_and_policy, tmp_path, capsys):
    assessment, policy = request_and_policy
    policy["parent_cost_tier"] = 1
    assessment_path = tmp_path / "assessment.json"
    policy_path = tmp_path / "policy.json"
    assessment_path.write_text(json.dumps(assessment), encoding="utf-8")
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    assert main(["gateway", "route", "--assessment", str(assessment_path),
                 "--policy", str(policy_path)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "conversation_upgrade_required"


@pytest.mark.parametrize("problem", ["cycle", "reference", "typo", "negative", "unknown_zero", "missing_execution_kind"])
def test_assessment_rejects_invalid_boundaries(request_and_policy, problem):
    assessment, _ = request_and_policy
    step = assessment["steps"][1]
    if problem == "cycle":
        step["depends_on"] = ["interpret"]
    elif problem == "reference":
        step["evidence"] = [{"source_id": "missing", "locator": "line 1"}]
    elif problem == "typo":
        step["metrics"]["scope_change"] = step["metrics"].pop("scope_changes")
    elif problem == "negative":
        step["metrics"]["scope_changes"]["value"] = -1
    elif problem == "missing_execution_kind":
        step.pop("execution_kind")
    else:
        step["metrics"]["scope_changes"].update(value=0, basis="unknown")
    with pytest.raises(ValidationError):
        Assessment.model_validate(assessment)


def attempt(**updates):
    value = {"id": "a1", "goal_id": "g", "scope_revision": 0, "model": "capable",
             "route_ref": "route-1.json", "reason": "initial"}
    value.update(updates)
    return value


def test_similar_instruction_is_not_automatically_dissatisfaction():
    feedback = Feedback.model_validate({"version": 1, "cost_unit": "USD", "attempts": [
        attempt(), attempt(id="a2", retry_of="a1", reason="unknown")]})
    result = evaluate(feedback)
    assert result["quality_retries"] == 0
    assert result["unknown_retries"] == 1
    assert result["first_acceptance_rate"] is None
    assert result["usage"]["cost"]["total"] is None


def test_quality_retry_and_requirement_change_are_separate():
    feedback = Feedback.model_validate({"version": 1, "cost_unit": "USD", "attempts": [
        attempt(accepted=False, acceptance_evidence="user correction", cost=0.1),
        attempt(id="a2", retry_of="a1", reason="scope_error", reason_evidence="user: only A",
                accepted=True, acceptance_evidence="user accepted", cost=0.2),
        attempt(id="a3", retry_of="a2", reason="requirement_change", scope_revision=1,
                reason_evidence="user: include B", cost=0.3)]})
    result = evaluate(feedback)
    assert result["quality_retries"] == 1
    assert result["requirement_changes"] == 1
    assert result["first_acceptance_rate"] == 0
    assert result["usage"]["cost"]["total"] == pytest.approx(0.6)
    assert result["acceptance_by_scope"][0]["attempts_to_acceptance"] == 2
    assert result["acceptance_by_scope"][0]["usage_observed"]["cost"] == pytest.approx(0.3)
    assert result["acceptance_by_scope"][1]["attempts_to_acceptance"] is None


def test_feedback_rejects_unsubstantiated_or_cross_goal_retry():
    with pytest.raises(ValidationError):
        Feedback.model_validate({"version": 1, "cost_unit": "USD", "attempts": [attempt(accepted=True)]})
    with pytest.raises(ValueError, match="same goal"):
        evaluate(Feedback.model_validate({"version": 1, "cost_unit": "USD", "attempts": [
            attempt(), attempt(id="a2", goal_id="other", retry_of="a1", reason="unknown")]}))


def test_cli_roundtrip_and_no_overwrite(request_and_policy, tmp_path, capsys):
    assessment, policy = request_and_policy
    profile_path = tmp_path / "existing-profile.md"
    before = profile_path.read_bytes()
    assert main(["gateway", "prepare", "--request-id", "r", "--environment", "vscode:test", "--instruction-file",
                 str(tmp_path / "instruction.txt"), "--skill-file", str(tmp_path / "meta.md"),
                 "--profile-file", str(profile_path)]) == 0
    prepared = json.loads(capsys.readouterr().out)
    assert prepared["unresolved"] is None
    assert prepared["steps"] == []
    assert profile_path.read_bytes() == before
    assessment_path = tmp_path / "assessment.json"
    policy_path = tmp_path / "policy.json"
    assessment_path.write_text(json.dumps(assessment), encoding="utf-8")
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    args = ["gateway", "route", "--assessment", str(assessment_path), "--policy", str(policy_path),
            "--out", str(tmp_path / "route.json")]
    assert main(args) == 0
    assert main(args) == 2
    assert "error" in json.loads(capsys.readouterr().err)


def test_explicit_cheaper_qualified_candidate(request_and_policy):
    pair = copy.deepcopy(request_and_policy)
    pair[1]["candidates"][0]["capabilities"].append("orthogonal_array")
    assert run_pair(pair)["decisions"][1]["model"] == "cheap"


def test_schema_and_feedback_cli(tmp_path, capsys):
    assert main(["gateway", "schema", "assessment"]) == 0
    schema = json.loads(capsys.readouterr().out)
    assert schema["additionalProperties"] is False
    assert main(["gateway", "schema", "dispatch_plan"]) == 0
    dispatch_schema = json.loads(capsys.readouterr().out)
    assert set(dispatch_schema["required"]) == {
        "step_id", "parent_model", "selected_model", "agent_role", "rationale",
        "parent_execution", "dispatch_owner"}
    source = tmp_path / "feedback.json"
    source.write_text(json.dumps({"version": 1, "cost_unit": "USD", "attempts": [attempt()]}), encoding="utf-8")
    assert main(["gateway", "evaluate", "--feedback", str(source)]) == 0
    assert json.loads(capsys.readouterr().out)["unjudged_initial_attempts"] == 1


def test_missing_source_and_invalid_policy_are_errors(request_and_policy, tmp_path, capsys):
    assert main(["gateway", "prepare", "--request-id", "r", "--environment", "vscode:test", "--instruction-file",
                 str(tmp_path / "absent"), "--skill-file", str(tmp_path / "meta.md")]) == 2
    assert json.loads(capsys.readouterr().err)["ok"] is False
    policy = request_and_policy[1]
    policy["parent_cost_tier"] = None
    with pytest.raises(ValidationError):
        Policy.model_validate(policy)


def test_environment_policy_cannot_be_reused(request_and_policy):
    request_and_policy[1]["environment"] = "codex:personal"
    result = run_pair(request_and_policy)
    assert result["status"] == "needs_assessment"
    assert result["decisions"][1]["model"] is None


def test_profile_root_scopes_existing_files(request_and_policy, tmp_path, capsys):
    root = tmp_path / "vscode-user-profile"
    root.mkdir()
    profile = root / "preferences.md"
    profile.write_text("Japanese reports", encoding="utf-8")
    args = ["gateway", "prepare", "--request-id", "r", "--environment", "vscode:work",
            "--instruction-file", str(tmp_path / "instruction.txt"),
            "--skill-file", str(tmp_path / "meta.md"), "--profile-root", str(root)]
    assert main(args + ["--profile-file", "preferences.md"]) == 0
    prepared = json.loads(capsys.readouterr().out)
    assert prepared["environment"] == "vscode:work"
    assert prepared["sources"][-1]["path"] == str(profile.resolve())
    assert profile.read_text(encoding="utf-8") == "Japanese reports"
    assert main(args + ["--profile-file", "../existing-profile.md"]) == 2
    assert "outside" in json.loads(capsys.readouterr().err)["error"]
