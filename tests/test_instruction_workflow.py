import contextlib
import io
import json
from pathlib import Path

from xrefkit.__main__ import main
from xrefkit.skillrun import _append_observation_event


def _run(root: Path, *args: str) -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        argv = list(args)
        if argv[:2] == ["workflow", "run"]:
            argv.extend(["--root", str(root)])
        return main(argv)


def test_instruction_workflow_requires_completion_conditions(tmp_path: Path) -> None:
    out = tmp_path / "work" / "sessions" / "run.md"
    assert _run(tmp_path, "workflow", "run", "--task", "Do work", "--out", str(out)) == 1
    assert not out.exists()


def test_instruction_workflow_uses_default_conditions_and_shared_protocol(tmp_path: Path) -> None:
    out = tmp_path / "work" / "sessions" / "run.md"
    assert _run(
        tmp_path,
        "workflow",
        "run",
        "--task",
        "Do work",
        "--out",
        str(out),
        "--use-default-completion-conditions",
    ) == 0
    text = out.read_text(encoding="utf-8")
    assert "# Workflow Run Log" in text
    assert "## Run Load Gate" in text
    assert "- basis: `default`" in text
    assert "- quality_policy: `human_acceptance`" in text

    assert _run(
        tmp_path,
        "skill",
        "workitem",
        "--log",
        str(out),
        "--item",
        "WI-001",
        "--text",
        "Perform the instruction",
        "--completion-criterion",
        "instruction result is recorded and verified",
        "--status",
        "done",
        "--role",
        "instruction:executor",
    ) == 0
    for artifact_id, kind, target, role in (
        ("OUT-001", "output", "output.md", "instruction:executor"),
        ("EVD-001", "evidence", "test command", "instruction:checker"),
    ):
        assert _run(
            tmp_path,
            "skill",
            "artifact",
            "--log",
            str(out),
            "--artifact",
            artifact_id,
            "--kind",
            kind,
            "--target",
            target,
            "--item",
            "WI-001",
            "--status",
            "done",
            "--role",
            role,
        ) == 0
    assert _run(tmp_path, "skill", "phase", "--log", str(out), "--phase", "execution", "--status", "done", "--role", "instruction:executor") == 0
    assert _run(tmp_path, "skill", "phase", "--log", str(out), "--phase", "handoff", "--status", "done", "--role", "instruction:handoff_owner") == 0
    assert _run(tmp_path, "skill", "verify", "--log", str(out)) == 0

    # Quality is a human decision and is recorded separately from progression.
    assert _run(
        tmp_path,
        "skill",
        "feedback",
        "--log",
        str(out),
        "--kind",
        "human",
        "--status",
        "accepted",
        "--target",
        "OUT-001",
        "--note",
        "human accepted output quality",
    ) == 0
    assert _run(tmp_path, "skill", "close", "--log", str(out)) == 0
    assert "## Completion Conditions" in out.read_text(encoding="utf-8")


def test_instruction_workflow_records_minimum_intake_without_inventing_missing_values(tmp_path: Path) -> None:
    unknown_out = tmp_path / "work" / "sessions" / "unknown.md"
    assert _run(
        tmp_path, "workflow", "run", "--task", "Missing intake", "--out", str(unknown_out),
        "--use-default-completion-conditions",
    ) == 0
    unknown_text = unknown_out.read_text(encoding="utf-8")
    assert "## Minimum Intake" in unknown_text
    assert "- purpose: `unknown`" in unknown_text
    assert "- owner: `unknown`" in unknown_text

    explicit_out = tmp_path / "work" / "sessions" / "explicit.md"
    assert _run(
        tmp_path, "workflow", "run", "--task", "Explicit intake", "--out", str(explicit_out),
        "--purpose", "Deliver the reviewed change", "--scope-in", "Dashboard",
        "--scope-out", "Production deployment", "--owner", "human-owner",
        "--authority", "approved issue", "--expected-evidence", "pytest output",
        "--stop-condition", "Stop when expected evidence is unavailable",
        "--use-default-completion-conditions",
    ) == 0
    explicit_text = explicit_out.read_text(encoding="utf-8")
    assert "- purpose: `Deliver the reviewed change`" in explicit_text
    assert "- scope_out: `Production deployment`" in explicit_text
    assert "- stop_conditions: `Stop when expected evidence is unavailable`" in explicit_text


def test_prompt_flow_continuation_scope_change_and_unrelated_work_remain_distinct(tmp_path: Path) -> None:
    root = tmp_path
    parent = root / "work" / "sessions" / "parent.md"
    continuation = root / "work" / "sessions" / "continuation.md"
    unrelated = root / "work" / "sessions" / "unrelated.md"
    assert _run(
        root, "workflow", "run", "--task", "Initial prompt", "--out", str(parent),
        "--run-id", "11111111-1111-4111-8111-111111111111", "--flow-id", "FLOW-CONTINUE",
        "--node-id", "NODE-ROOT", "--use-default-completion-conditions",
    ) == 0
    assert _run(
        root, "skill", "workitem", "--log", str(parent), "--item", "WI-001",
        "--text", "Initial scope", "--completion-criterion", "initial scope is recorded",
        "--status", "pending", "--role", "instruction:executor",
    ) == 0
    assert _run(
        root, "workflow", "run", "--task", "Continue the same prompt flow", "--out", str(continuation),
        "--run-id", "22222222-2222-4222-8222-222222222222", "--flow-id", "FLOW-CONTINUE",
        "--root-run-id", "11111111-1111-4111-8111-111111111111",
        "--parent-run-id", "11111111-1111-4111-8111-111111111111", "--work-item-id", "WI-001",
        "--node-id", "NODE-CONTINUATION", "--use-default-completion-conditions",
    ) == 0
    assert _run(
        root, "skill", "workitem", "--log", str(parent), "--item", "WI-002", "--supersedes", "WI-001",
        "--text", "Revised scope", "--completion-criterion", "revised scope is recorded",
        "--status", "pending", "--role", "instruction:executor",
    ) == 0
    assert _run(
        root, "workflow", "run", "--task", "Unrelated new work", "--out", str(unrelated),
        "--run-id", "33333333-3333-4333-8333-333333333333", "--flow-id", "FLOW-NEW",
        "--node-id", "NODE-NEW", "--use-default-completion-conditions",
    ) == 0
    parent_text = parent.read_text(encoding="utf-8")
    continuation_text = continuation.read_text(encoding="utf-8")
    assert "supersedes=`WI-001`" in parent_text
    assert "- flow_id: `FLOW-CONTINUE`" in continuation_text
    assert "- parent_run_id: `11111111-1111-4111-8111-111111111111`" in continuation_text
    assert "- flow_id: `FLOW-NEW`" in unrelated.read_text(encoding="utf-8")


def test_workitem_requires_criterion_or_explicit_unknown_reason(tmp_path: Path) -> None:
    out = tmp_path / "work" / "sessions" / "run.md"
    assert _run(
        tmp_path,
        "workflow",
        "run",
        "--task",
        "Do work",
        "--out",
        str(out),
        "--use-default-completion-conditions",
    ) == 0
    assert _run(
        tmp_path,
        "skill",
        "workitem",
        "--log",
        str(out),
        "--item",
        "WI-001",
        "--text",
        "Investigate missing requirement",
        "--status",
        "pending",
        "--role",
        "instruction:executor",
    ) == 1
    assert _run(
        tmp_path,
        "skill",
        "workitem",
        "--log",
        str(out),
        "--item",
        "WI-001",
        "--text",
        "Investigate missing requirement",
        "--status",
        "unknown",
        "--criterion-unknown-reason",
        "The business owner has not defined the acceptance outcome",
        "--role",
        "instruction:executor",
    ) == 0
    text = out.read_text(encoding="utf-8")
    assert "criterion=`` reason=`The business owner has not defined the acceptance outcome`" in text
    assert _run(tmp_path, "skill", "phase", "--log", str(out), "--phase", "execution", "--status", "done", "--role", "instruction:executor") == 0
    assert _run(tmp_path, "skill", "verify", "--log", str(out)) == 1


def test_workitem_criterion_is_immutable_and_changes_use_supersedes(tmp_path: Path) -> None:
    out = tmp_path / "work" / "sessions" / "run.md"
    assert _run(tmp_path, "workflow", "run", "--task", "Do work", "--out", str(out), "--use-default-completion-conditions") == 0
    base = [
        "skill", "workitem", "--log", str(out), "--item", "WI-001",
        "--text", "Implement original outcome", "--completion-criterion", "original outcome is verified",
        "--status", "pending", "--role", "instruction:executor",
    ]
    assert _run(tmp_path, *base) == 0
    assert _run(tmp_path, *base[:-6], "--completion-criterion", "different outcome is verified", "--status", "pending", "--role", "instruction:executor") == 1
    assert _run(
        tmp_path,
        "skill", "workitem", "--log", str(out), "--item", "WI-002", "--supersedes", "WI-001",
        "--text", "Implement revised outcome", "--completion-criterion", "revised outcome is verified",
        "--status", "pending", "--role", "instruction:executor",
    ) == 0
    text = out.read_text(encoding="utf-8")
    assert "WI-002" in text and "supersedes=`WI-001`" in text


def test_instruction_workflow_records_prompt_flow_correlation(tmp_path: Path) -> None:
    out = tmp_path / "work" / "sessions" / "root.md"
    assert _run(
        tmp_path,
        "workflow",
        "run",
        "--task",
        "Coordinate prompt flow",
        "--out",
        str(out),
        "--run-id",
        "11111111-1111-4111-8111-111111111111",
        "--flow-id",
        "FLOW-001",
        "--node-id",
        "NODE-ROOT",
        "--use-default-completion-conditions",
    ) == 0
    text = out.read_text(encoding="utf-8")
    assert "- flow_id: `FLOW-001`" in text
    assert "- root_run_id: `11111111-1111-4111-8111-111111111111`" in text
    assert "- parent_run_id: `-`" in text
    assert "- node_id: `NODE-ROOT`" in text


def test_instruction_workflow_records_clarification_and_human_confirmed_recovery(tmp_path: Path) -> None:
    out = tmp_path / "work" / "sessions" / "root.md"
    assert _run(
        tmp_path,
        "workflow", "run", "--task", "Uncertain flow", "--out", str(out),
        "--use-default-completion-conditions",
    ) == 0
    assert _run(
        tmp_path,
        "skill", "routing", "--log", str(out),
        "--selection-mode", "needs_clarification",
        "--candidate", "skill_a", "--candidate", "skill_b",
        "--reason", "Both Skills may apply to the requested work",
        "--target-work-item", "WI-001",
    ) == 0
    assert _run(
        tmp_path,
        "workflow", "recovery", "--log", str(out),
        "--recovery-id", "REC-001", "--status", "proposed",
        "--resume-location", "WI-001 checkpoint",
        "--reason", "The previous executor stopped before verification",
        "--next-action", "Run the recorded verification command",
        "--executable-action", "Run verification command once",
        "--owner", "recovery-owner",
        "--verification-method", "Verify the recorded check passes",
        "--maximum-attempts", "2",
        "--stop-condition", "Stop after two failed attempts",
    ) == 0
    assert _run(
        tmp_path,
        "workflow", "recovery", "--log", str(out),
        "--recovery-id", "REC-001", "--status", "confirmed",
        "--resume-location", "WI-001 checkpoint",
        "--reason", "The previous executor stopped before verification",
        "--next-action", "Run the recorded verification command",
        "--executable-action", "Run verification command once",
        "--owner", "recovery-owner",
        "--verification-method", "Verify the recorded check passes",
        "--maximum-attempts", "2",
        "--stop-condition", "Stop after two failed attempts",
        "--reviewer", "human-owner",
    ) == 0
    text = out.read_text(encoding="utf-8")
    assert '"selection_mode":"needs_clarification"' in text
    assert '"status":"proposed"' in text
    assert '"status":"confirmed"' in text
    assert '"owner":"recovery-owner"' in text
    assert '"maximum_attempts":2' in text
    assert '"stop_conditions":["Stop after two failed attempts"]' in text


def test_instruction_workflow_records_parent_semantic_routing_modes(tmp_path: Path) -> None:
    out = tmp_path / "work" / "sessions" / "root.md"
    assert _run(
        tmp_path,
        "workflow", "run", "--task", "Route a mixed prompt", "--out", str(out),
        "--use-default-completion-conditions",
    ) == 0
    assert _run(
        tmp_path,
        "workflow", "routing", "--log", str(out),
        "--selected-skill", "skill_a", "--candidate", "skill_a", "--candidate", "skill_b",
        "--selection-mode", "semantic", "--target-work-item", "WI-001",
        "--reason", "The work item matches skill_a's declared responsibility",
    ) == 0
    assert _run(
        tmp_path,
        "workflow", "routing", "--log", str(out),
        "--selection-mode", "fallback",
        "--target-work-item", "WI-002",
        "--reason", "No existing Skill matches the generic coordination work",
    ) == 0
    assert _run(
        tmp_path,
        "workflow", "routing", "--log", str(out),
        "--candidate", "skill_a", "--candidate", "skill_b",
        "--selection-mode", "needs_clarification", "--target-work-item", "WI-003",
        "--reason", "The available Skill boundaries overlap and require human confirmation",
    ) == 0
    text = out.read_text(encoding="utf-8")
    assert text.count('"event":"flow.routed"') == 3
    assert '"selection_mode":"fallback"' in text
    assert '"status":"needs_clarification"' in text


def test_parent_reconcile_blocks_until_work_items_are_done_or_escalated(tmp_path: Path) -> None:
    out = tmp_path / "work" / "sessions" / "parent.md"
    assert _run(
        tmp_path,
        "workflow", "run", "--task", "Reconcile flow", "--out", str(out),
        "--use-default-completion-conditions",
    ) == 0
    assert _run(
        tmp_path,
        "skill", "workitem", "--log", str(out), "--item", "WI-001",
        "--text", "Complete the flow item", "--completion-criterion", "item is complete",
        "--status", "pending", "--role", "instruction:executor",
    ) == 0
    assert _run(tmp_path, "workflow", "reconcile", "--log", str(out)) == 1
    text = out.read_text(encoding="utf-8")
    assert '"event":"flow.reconciled"' in text
    assert '"status":"blocked"' in text
    assert "parent run" in text
    assert "output artifact" in text


def test_parent_reconcile_can_apply_closed_child_status_explicitly(tmp_path: Path) -> None:
    parent = tmp_path / "work" / "sessions" / "parent.md"
    child = tmp_path / "work" / "sessions" / "child.md"
    assert _run(
        tmp_path, "workflow", "run", "--task", "Parent flow", "--run-id", "11111111-1111-4111-8111-111111111111",
        "--out", str(parent), "--use-default-completion-conditions",
    ) == 0
    assert _run(
        tmp_path, "skill", "workitem", "--log", str(parent), "--item", "WI-001",
        "--text", "Complete delegated item", "--completion-criterion", "child result is verified",
        "--status", "pending", "--role", "instruction:executor",
    ) == 0
    assert _run(
        tmp_path, "workflow", "run", "--task", "Child flow", "--run-id", "22222222-2222-4222-8222-222222222222",
        "--flow-id", "11111111-1111-4111-8111-111111111111", "--root-run-id", "11111111-1111-4111-8111-111111111111", "--parent-run-id", "11111111-1111-4111-8111-111111111111",
        "--work-item-id", "WI-001", "--out", str(child), "--use-default-completion-conditions",
    ) == 0
    assert _run(
        tmp_path, "skill", "workitem", "--log", str(child), "--item", "WI-CHILD",
        "--text", "Produce child result", "--completion-criterion", "child result is recorded",
        "--status", "done", "--role", "instruction:executor",
    ) == 0
    assert _run(tmp_path, "skill", "artifact", "--log", str(child), "--artifact", "OUT-CHILD", "--kind", "output", "--target", "child-output.md", "--item", "WI-CHILD", "--status", "done", "--role", "instruction:executor") == 0
    assert _run(tmp_path, "skill", "artifact", "--log", str(child), "--artifact", "EVD-CHILD", "--kind", "evidence", "--target", "child-check", "--item", "WI-CHILD", "--status", "done", "--role", "instruction:checker") == 0
    assert _run(tmp_path, "skill", "phase", "--log", str(child), "--phase", "execution", "--status", "done", "--role", "instruction:executor") == 0
    assert _run(tmp_path, "skill", "phase", "--log", str(child), "--phase", "handoff", "--status", "done", "--role", "instruction:handoff_owner") == 0
    assert _run(tmp_path, "skill", "verify", "--log", str(child)) == 0
    assert _run(tmp_path, "skill", "feedback", "--log", str(child), "--kind", "human", "--status", "accepted", "--target", "WI-CHILD", "--note", "accepted") == 0
    assert _run(tmp_path, "skill", "close", "--log", str(child)) == 0
    parent.write_text(
        _append_observation_event(
            parent.read_text(encoding="utf-8"),
            section="Prompt Flow Trace",
            event={
                "event": "child_run.started", "flow_id": "11111111-1111-4111-8111-111111111111", "parent_run_id": "11111111-1111-4111-8111-111111111111",
                "child_run_id": "22222222-2222-4222-8222-222222222222", "child_log": str(child), "work_item_id": "WI-001",
            },
        ),
        encoding="utf-8",
    )
    assert _run(tmp_path, "skill", "artifact", "--log", str(parent), "--artifact", "OUT-PARENT", "--kind", "output", "--target", "parent-output.md", "--item", "WI-001", "--status", "done", "--role", "instruction:executor") == 0
    assert _run(tmp_path, "skill", "artifact", "--log", str(parent), "--artifact", "EVD-PARENT", "--kind", "evidence", "--target", "parent-check", "--item", "WI-001", "--status", "done", "--role", "instruction:checker") == 0
    assert _run(
        tmp_path, "workflow", "reconcile", "--log", str(parent), "--apply-child-status",
    ) == 0
    text = parent.read_text(encoding="utf-8")
    assert "WI-001 status=`done`" in text
    assert '"event":"flow.child_status_applied"' in text
    assert '"event":"flow.reconciled"' in text
    assert '"findings":[]' in text
    assert _run(tmp_path, "skill", "phase", "--log", str(parent), "--phase", "execution", "--status", "done", "--role", "instruction:executor") == 0
    assert _run(tmp_path, "skill", "phase", "--log", str(parent), "--phase", "handoff", "--status", "done", "--role", "instruction:handoff_owner") == 0
    assert _run(tmp_path, "skill", "verify", "--log", str(parent)) == 0
    assert _run(tmp_path, "skill", "feedback", "--log", str(parent), "--kind", "human", "--status", "accepted", "--target", "OUT-PARENT", "--note", "accepted") == 0
    assert _run(tmp_path, "skill", "close", "--log", str(parent)) == 0
