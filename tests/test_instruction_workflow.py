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
