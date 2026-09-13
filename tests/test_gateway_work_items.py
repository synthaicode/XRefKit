import copy
import json

import pytest

from xrefkit.gateway import (
    AXES,
    Assessment,
    Policy,
    WorkItemResult,
    WorkflowState,
    initialize_workflow,
    record_work_item_result,
    route_work_items,
    snapshot,
)
from xrefkit.cli import main


def evidence(ref: str, summary: str = "verified fixture evidence") -> dict:
    return {"ref": ref, "summary": summary}


def measurements(ref: list[dict], value: int = 1) -> dict:
    return {
        axis: {"value": value, "basis": "measured", "evidence": ref}
        for axis in AXES
    }


@pytest.fixture
def release_flow(tmp_path):
    instruction = tmp_path / "instruction.txt"
    skill = tmp_path / "meta.md"
    instruction.write_text(
        "Create the PR and, after CI passes, merge, tag, and verify PyPI.",
        encoding="utf-8",
    )
    skill.write_text("Use the governed release workflow.", encoding="utf-8")
    source_ref = [{"source_id": "instruction", "locator": "line 1"}]
    authorization = {
        "action": "write release state",
        "scope": "PR, merge, tag, and release for this request",
        "status": "authorized",
        "evidence": source_ref,
    }
    assessment = Assessment.model_validate({
        "version": 1,
        "request_id": "release-1",
        "revision": 0,
        "environment": "codex:test",
        "instruction": instruction.read_text(encoding="utf-8"),
        "sources": [
            snapshot(instruction, "instruction", "instruction"),
            snapshot(skill, "skill", "skill"),
        ],
        "unresolved": [],
        "steps": [
            {
                "id": "pr",
                "node_id": "release/pr",
                "kind": "model",
                "execution_kind": "operation",
                "task": "Write and create the PR",
                "scope": "one reviewed branch and PR",
                "evidence": source_ref,
                "capabilities": ["routine_release"],
                "metrics": measurements(source_ref),
                "authorization": authorization,
            },
            {
                "id": "ci",
                "node_id": "release/ci",
                "kind": "deterministic",
                "task": "Wait for CI",
                "scope": "PR checks",
                "evidence": source_ref,
                "depends_on": ["pr"],
                "tool_ref": "gh pr checks --watch",
            },
            {
                "id": "merge",
                "node_id": "release/merge",
                "kind": "model",
                "execution_kind": "operation",
                "task": "Interpret checks and merge the PR",
                "scope": "the reviewed PR",
                "evidence": source_ref,
                "depends_on": ["ci"],
                "capabilities": ["routine_release"],
                "metrics": measurements(source_ref),
                "authorization": authorization,
            },
            {
                "id": "tag",
                "node_id": "release/tag",
                "kind": "deterministic",
                "task": "Create and push the approved tag",
                "scope": "the merged commit",
                "evidence": source_ref,
                "depends_on": ["merge"],
                "tool_ref": "git tag-and-push-approved-version",
                "authorization": authorization,
            },
            {
                "id": "registry",
                "node_id": "release/registry",
                "kind": "model",
                "execution_kind": "operation",
                "task": "Interpret registry and clean-install verification",
                "scope": "the released PyPI version",
                "evidence": source_ref,
                "depends_on": ["tag"],
                "capabilities": ["routine_release"],
                "metrics": measurements(source_ref),
            },
        ],
    })
    policy = Policy.model_validate({
        "version": "release-cost-v1",
        "environment": "codex:test",
        "host": "generic",
        "parent_model_id": "gateway-parent",
        "selection_strategy": "lowest_cost_eligible",
        "candidates": [
            {
                "id": "low",
                "cost_tier": 1,
                "priority": 5,
                "capabilities": ["routine_release"],
                "limits": dict.fromkeys(AXES, 2),
                "evaluation_ref": "eval/low-release",
                "max_input_bytes": 10000,
            },
            {
                "id": "high",
                "cost_tier": 3,
                "priority": 0,
                "capabilities": [
                    "routine_release",
                    "ci_incompatibility_diagnosis",
                    "security_diagnosis",
                    "dependency_diagnosis",
                ],
                "limits": dict.fromkeys(AXES, 10),
                "evaluation_ref": "eval/high-recovery",
                "max_input_bytes": 10000,
            },
        ],
    })
    return assessment, policy


def state_from(result: dict) -> WorkflowState:
    return WorkflowState.model_validate(result["workflow_state"])


def succeed(assessment, state, *, observed_model=None, resolves=None):
    item = next(item for item in state.items if item.status == "in_progress")
    payload = {
        "version": 1,
        "request_id": assessment.request_id,
        "assessment_revision": assessment.revision,
        "step_id": item.step_id,
        "node_id": item.node_id,
        "route_id": item.assignment.route_id,
        "route_revision": item.assignment.route_revision,
        "outcome": "succeeded",
        "observed_model": observed_model,
        "route_evidence": f"runs/{item.assignment.route_id}",
        "evidence": [evidence(f"evidence/{item.step_id}")],
    }
    if resolves:
        payload["resolves_failure_id"] = resolves
        payload["resolution_evidence"] = [evidence(f"resolution/{resolves}")]
    return record_work_item_result(assessment, state, WorkItemResult.model_validate(payload))


def test_release_routes_low_escalates_ci_then_deescalates(release_flow):
    assessment, policy = release_flow
    state = state_from(initialize_workflow(assessment))

    routed = route_work_items(assessment, policy, state)
    assert routed["subagent_dispatches"][0]["agent_role"] == "operational_subagent"
    assert routed["subagent_dispatches"][0]["selected_model"] == "low"
    state = state_from(succeed(assessment, state_from(routed), observed_model="low"))

    routed = route_work_items(assessment, policy, state)
    assert routed["decisions"][1]["kind"] == "deterministic"
    state = state_from(routed)
    ci = next(item for item in state.items if item.step_id == "ci")
    failure = {
        "id": "ci-incompat-1",
        "category": "ci",
        "disposition": "model_reroute",
        "known_transient": False,
        "classification_evidence": [evidence("ci/run-17", "unsupported dependency API")],
        "revised_scope": "diagnose and fix the CI dependency incompatibility",
        "recovery_execution_kind": "implementation",
        "required_capabilities": ["ci_incompatibility_diagnosis"],
        "metrics": measurements([evidence("ci/run-17")], value=4),
        "minimum_cost_tier": 2,
    }
    failed = record_work_item_result(assessment, state, WorkItemResult.model_validate({
        "version": 1,
        "request_id": assessment.request_id,
        "assessment_revision": assessment.revision,
        "step_id": "ci",
        "node_id": ci.node_id,
        "route_id": ci.assignment.route_id,
        "route_revision": ci.assignment.route_revision,
        "outcome": "failed",
        "route_evidence": "ci/run-17",
        "evidence": [evidence("ci/run-17")],
        "failure": failure,
    }))
    assert failed["status"] == "reroute_required"
    assert failed["reroute_requirement"]["revised_scope"].startswith("diagnose")

    routed = route_work_items(assessment, policy, state_from(failed))
    dispatch = routed["subagent_dispatches"][0]
    assert dispatch["work_item_id"] == "ci"
    assert dispatch["selected_model"] == "high"
    assert dispatch["scope"] == failure["revised_scope"]
    state = state_from(succeed(
        assessment, state_from(routed), observed_model="high", resolves="ci-incompat-1"
    ))

    routed = route_work_items(assessment, policy, state)
    assert routed["subagent_dispatches"][0]["work_item_id"] == "merge"
    assert routed["subagent_dispatches"][0]["selected_model"] == "low"
    state = state_from(succeed(assessment, state_from(routed), observed_model="low"))

    routed = route_work_items(assessment, policy, state)
    assert next(row for row in routed["decisions"] if row["work_item_id"] == "tag")["kind"] == "deterministic"
    state = state_from(succeed(assessment, state_from(routed)))
    routed = route_work_items(assessment, policy, state)
    assert routed["subagent_dispatches"][0]["work_item_id"] == "registry"
    assert routed["subagent_dispatches"][0]["selected_model"] == "low"

    ci_state = next(item for item in state_from(routed).items if item.step_id == "ci")
    assert [(row.selected_model, row.observed_model) for row in ci_state.observations] == [
        (None, None), ("high", "high")
    ]


@pytest.mark.parametrize(
    ("category", "capability"),
    [("security", "security_diagnosis"), ("dependency", "dependency_diagnosis")],
)
def test_unexpected_security_or_dependency_failure_requires_higher_model(
    release_flow, category, capability
):
    assessment, policy = release_flow
    state = state_from(initialize_workflow(assessment))
    routed = route_work_items(assessment, policy, state)
    state = state_from(routed)
    pr = next(item for item in state.items if item.step_id == "pr")
    failure = {
        "id": f"{category}-1",
        "category": category,
        "disposition": "model_reroute",
        "known_transient": False,
        "classification_evidence": [evidence(f"finding/{category}")],
        "revised_scope": f"diagnose and fix the {category} finding",
        "recovery_execution_kind": "implementation",
        "required_capabilities": [capability],
        "metrics": measurements([evidence(f"finding/{category}")], value=4),
        "minimum_cost_tier": 2,
    }
    failed = record_work_item_result(assessment, state, WorkItemResult.model_validate({
        "version": 1,
        "request_id": assessment.request_id,
        "assessment_revision": assessment.revision,
        "step_id": pr.step_id,
        "node_id": pr.node_id,
        "route_id": pr.assignment.route_id,
        "route_revision": pr.assignment.route_revision,
        "outcome": "failed",
        "observed_model": "low",
        "route_evidence": f"finding/{category}",
        "evidence": [evidence(f"finding/{category}")],
        "failure": failure,
    }))
    rerouted = route_work_items(assessment, policy, state_from(failed))
    assert rerouted["subagent_dispatches"][0]["selected_model"] == "high"


def test_known_transient_failure_remains_deterministic_retry(release_flow):
    assessment, policy = release_flow
    state = state_from(initialize_workflow(assessment))
    state = state_from(succeed(
        assessment,
        state_from(route_work_items(assessment, policy, state)),
        observed_model="low",
    ))
    state = state_from(route_work_items(assessment, policy, state))
    ci = next(item for item in state.items if item.step_id == "ci")
    failed = record_work_item_result(assessment, state, WorkItemResult.model_validate({
        "version": 1,
        "request_id": assessment.request_id,
        "assessment_revision": assessment.revision,
        "step_id": ci.step_id,
        "node_id": ci.node_id,
        "route_id": ci.assignment.route_id,
        "route_revision": ci.assignment.route_revision,
        "outcome": "failed",
        "route_evidence": "ci/run-18",
        "evidence": [evidence("ci/run-18", "documented transient network reset")],
        "failure": {
            "id": "ci-transient-1",
            "category": "ci",
            "disposition": "deterministic_retry",
            "known_transient": True,
            "classification_evidence": [evidence("ci/run-18")],
            "retry_tool_ref": "gh pr checks --watch",
        },
    }))
    retried = route_work_items(assessment, policy, state_from(failed))
    decision = next(row for row in retried["decisions"] if row["work_item_id"] == "ci")
    assert decision["kind"] == "deterministic"
    assert retried["subagent_dispatches"] == []


def test_authorization_gates_execution_without_changing_low_model(release_flow):
    assessment, policy = release_flow
    pending_auth = assessment.model_copy(deep=True)
    pending_auth.steps[0].authorization.status = "required"
    pending_auth.steps[0].authorization.evidence = []
    state = state_from(initialize_workflow(pending_auth))
    result = route_work_items(pending_auth, policy, state)
    pr = next(row for row in result["decisions"] if row["work_item_id"] == "pr")
    assert pr["model"] == "low"
    assert pr["execution_authorized"] is False
    assert result["status"] == "authorization_required"
    assert result["subagent_dispatches"] == []
    assert state_from(result).items[0].status == "pending"


def test_stateless_route_activates_only_one_independent_node(release_flow):
    assessment, policy = release_flow
    parallel_ready = assessment.model_copy(deep=True)
    parallel_ready.steps[2].depends_on = []
    state = state_from(initialize_workflow(parallel_ready))
    routed = route_work_items(parallel_ready, policy, state)
    active = [item for item in state_from(routed).items if item.status == "in_progress"]
    assert [item.step_id for item in active] == ["pr"]
    merge = next(row for row in routed["decisions"] if row["work_item_id"] == "merge")
    assert merge["dispatch"] == "waiting_serial_turn"
    assert len(routed["subagent_dispatches"]) == 1

    repeated = route_work_items(parallel_ready, policy, state_from(routed))
    repeated_state = state_from(repeated)
    assert repeated["status"] == "waiting_active_result"
    assert repeated["subagent_dispatches"] == []
    assert [item.step_id for item in repeated_state.items
            if item.status == "in_progress"] == ["pr"]
    merge = next(row for row in repeated["decisions"] if row["work_item_id"] == "merge")
    assert merge["dispatch"] == "waiting_active_result"

    state = state_from(succeed(parallel_ready, state_from(routed), observed_model="low"))
    next_route = route_work_items(parallel_ready, policy, state)
    assert next(item for item in state_from(next_route).items
                if item.status == "in_progress").step_id == "ci"
    state = state_from(succeed(parallel_ready, state_from(next_route)))
    merge_route = route_work_items(parallel_ready, policy, state)
    assert merge_route["subagent_dispatches"][0]["work_item_id"] == "merge"


def test_removed_node_requires_tombstone_and_preserves_history(release_flow):
    assessment, policy = release_flow
    state = state_from(initialize_workflow(assessment))
    while not all(item.status == "done" for item in state.items):
        routed = route_work_items(assessment, policy, state)
        state = state_from(routed)
        active = next(item for item in state.items if item.status == "in_progress")
        state = state_from(succeed(
            assessment,
            state,
            observed_model=(active.assignment.selected_model
                            if active.assignment.kind == "model" else None),
        ))
    registry = next(item for item in state.items if item.step_id == "registry")
    without_registry = assessment.model_dump()
    without_registry["revision"] = 1
    without_registry["steps"] = [
        step for step in without_registry["steps"] if step["id"] != "registry"
    ]
    with pytest.raises(ValueError, match="scope_change"):
        initialize_workflow(Assessment.model_validate(without_registry), previous_state=state)

    without_registry["scope_change"] = {
        "previous_revision": 0,
        "affected_steps": ["tag"],
        "removed_steps": [],
        "reason": "incomplete removal declaration",
        "evidence": [{"source_id": "instruction", "locator": "line 1"}],
    }
    with pytest.raises(ValueError, match="tombstone"):
        initialize_workflow(Assessment.model_validate(without_registry), previous_state=state)

    without_registry["scope_change"] = {
        "previous_revision": 0,
        "affected_steps": [],
        "removed_steps": [{
            "step_id": registry.step_id,
            "node_id": registry.node_id,
            "definition_sha256": registry.definition_sha256,
            "prior_status": registry.status,
            "reason": "registry interpretation is no longer in this request",
            "evidence": [{"source_id": "instruction", "locator": "line 1"}],
            "authorization": (registry.authorization.model_dump()
                              if registry.authorization else None),
        }],
        "reason": "remove registry interpretation from the revised scope",
        "evidence": [{"source_id": "instruction", "locator": "line 1"}],
    }
    revised = Assessment.model_validate(without_registry)
    reentered = state_from(initialize_workflow(revised, previous_state=state))
    assert {item.step_id for item in reentered.items} == {"pr", "ci", "merge", "tag"}
    assert len(reentered.retired_items) == 1
    retired = reentered.retired_items[0]
    assert retired.tombstone.step_id == "registry"
    assert retired.item.observations == registry.observations
    assert retired.item.completion_evidence == registry.completion_evidence


def test_completed_node_is_not_redispatched_and_reopen_requires_evidenced_revision(release_flow):
    assessment, policy = release_flow
    state = state_from(initialize_workflow(assessment))
    state = state_from(succeed(
        assessment,
        state_from(route_work_items(assessment, policy, state)),
        observed_model="low",
    ))
    routed = route_work_items(assessment, policy, state)
    pr = next(row for row in routed["decisions"] if row["work_item_id"] == "pr")
    assert pr == {"work_item_id": "pr", "node_id": "release/pr",
                  "state": "done", "dispatch": "not_pending"}

    completed = next(item for item in state.items if item.step_id == "pr")
    with pytest.raises(ValueError, match="completed work item"):
        record_work_item_result(assessment, state, WorkItemResult.model_validate({
            "version": 1,
            "request_id": assessment.request_id,
            "assessment_revision": assessment.revision,
            "step_id": completed.step_id,
            "node_id": completed.node_id,
            "route_id": completed.observations[0].route_id,
            "route_revision": completed.observations[0].route_revision,
            "outcome": "succeeded",
            "observed_model": "low",
            "route_evidence": "duplicate",
            "evidence": [evidence("duplicate")],
        }))

    newer = Assessment.model_validate({
        **assessment.model_dump(),
        "revision": 1,
        "scope_change": {
            "previous_revision": 0,
            "affected_steps": ["pr"],
            "reason": "user explicitly changed the PR scope",
            "evidence": [{"source_id": "instruction", "locator": "line 1"}],
        },
    })
    reentered = state_from(initialize_workflow(newer, previous_state=state))
    assert next(item for item in reentered.items if item.step_id == "pr").status == "pending"


def test_default_policy_keeps_priority_semantics(release_flow):
    assessment, policy = release_flow
    default_policy = Policy.model_validate({
        **policy.model_dump(exclude={"selection_strategy"}),
    })
    result = route_work_items(
        assessment, default_policy, state_from(initialize_workflow(assessment))
    )
    assert result["selection_strategy"] == "priority"
    assert result["subagent_dispatches"][0]["selected_model"] == "high"


def test_workflow_preserves_no_candidate_and_parent_upgrade_states(release_flow):
    assessment, policy = release_flow
    state = state_from(initialize_workflow(assessment))
    unavailable = policy.model_copy(deep=True)
    for candidate in unavailable.candidates:
        candidate.capabilities = []
    assert route_work_items(assessment, unavailable, state)["status"] == "needs_assessment"

    parent_limited = policy.model_copy(deep=True)
    parent_limited.host = "vscode_copilot"
    parent_limited.parent_cost_tier = 0
    upgraded = route_work_items(assessment, parent_limited, state)
    assert upgraded["status"] == "conversation_upgrade_required"
    assert upgraded["conversation_upgrade"]["required_minimum_tier"] == 1
    assert upgraded["conversation_upgrade"]["workers_callable_after_upgrade"][0]["model"] == "low"
    assert upgraded["workflow_state"] == state.model_dump()


def test_workflow_cli_schema_init_and_route(release_flow, tmp_path, capsys):
    assessment, policy = release_flow
    assessment_path = tmp_path / "assessment.json"
    policy_path = tmp_path / "policy.json"
    assessment_path.write_text(assessment.model_dump_json(), encoding="utf-8")
    policy_path.write_text(policy.model_dump_json(), encoding="utf-8")

    assert main(["gateway", "schema", "work_item_result"]) == 0
    assert json.loads(capsys.readouterr().out)["additionalProperties"] is False
    assert main([
        "gateway", "workflow-init", "--assessment", str(assessment_path),
        "--out", str(tmp_path / "initialized.json"),
    ]) == 0
    assert main([
        "gateway", "workflow-route", "--assessment", str(assessment_path),
        "--policy", str(policy_path), "--state", str(tmp_path / "initialized.json"),
        "--out", str(tmp_path / "routed.json"),
    ]) == 0
    routed = json.loads((tmp_path / "routed.json").read_text(encoding="utf-8"))
    assert routed["subagent_dispatches"][0]["selected_model"] == "low"
    active = routed["workflow_state"]["items"][0]
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps({
        "version": 1,
        "request_id": assessment.request_id,
        "assessment_revision": assessment.revision,
        "step_id": active["step_id"],
        "node_id": active["node_id"],
        "route_id": active["assignment"]["route_id"],
        "route_revision": active["assignment"]["route_revision"],
        "outcome": "succeeded",
        "observed_model": "low",
        "route_evidence": "host/cli-route",
        "evidence": [evidence("host/cli-route")],
    }), encoding="utf-8")
    assert main([
        "gateway", "workflow-result", "--assessment", str(assessment_path),
        "--state", str(tmp_path / "routed.json"), "--result", str(result_path),
        "--out", str(tmp_path / "recorded.json"),
    ]) == 0
    recorded = json.loads((tmp_path / "recorded.json").read_text(encoding="utf-8"))
    assert recorded["work_item_status"] == "done"
