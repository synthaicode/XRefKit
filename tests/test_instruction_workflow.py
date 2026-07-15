import contextlib
import io
import json
from pathlib import Path

from xrefkit.__main__ import main


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
