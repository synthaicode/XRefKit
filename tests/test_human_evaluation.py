import contextlib
import io
from pathlib import Path

from xrefkit.__main__ import main


def _run(root: Path, *args: str) -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        argv = list(args)
        if argv[:2] == ["workflow", "run"]:
            argv.extend(["--root", str(root)])
        return main(argv)


def _closed_run(tmp_path: Path) -> Path:
    log = tmp_path / "work" / "sessions" / "preceding.md"
    assert _run(
        tmp_path,
        "workflow", "run", "--task", "Produce a bounded output", "--out", str(log),
        "--use-default-completion-conditions",
    ) == 0
    assert _run(
        tmp_path, "skill", "workitem", "--log", str(log), "--item", "WI-001",
        "--text", "Produce output", "--completion-criterion", "output is recorded",
        "--status", "done", "--role", "instruction:executor",
    ) == 0
    for artifact_id, kind, target, role in (
        ("OUT-001", "output", "output.md", "instruction:executor"),
        ("EVD-001", "evidence", "test command passed", "instruction:checker"),
    ):
        assert _run(
            tmp_path, "skill", "artifact", "--log", str(log), "--artifact", artifact_id,
            "--kind", kind, "--target", target, "--item", "WI-001", "--status", "done",
            "--role", role,
        ) == 0
    assert _run(tmp_path, "skill", "phase", "--log", str(log), "--phase", "execution", "--status", "done", "--role", "instruction:executor") == 0
    assert _run(tmp_path, "skill", "phase", "--log", str(log), "--phase", "handoff", "--status", "done", "--role", "instruction:handoff_owner") == 0
    assert _run(tmp_path, "skill", "verify", "--log", str(log)) == 0
    assert _run(tmp_path, "skill", "close", "--log", str(log)) == 0
    return log


def test_human_evaluation_is_optional_and_scoped(tmp_path: Path) -> None:
    log = _closed_run(tmp_path)
    assert _run(
        tmp_path, "skill", "evaluate", "--log", str(log),
        "--decision", "accepted_with_conditions",
        "--classification", "correction",
        "--next-handling", "repair_previous_run",
        "--purpose-fit", "The overall purpose remains valid",
        "--verified", "WI-001 and EVD-001",
        "--uncertainty", "target B source is not snapshotted",
        "--scope-finding", "WI-A|accepted|Target A is acceptable",
        "--scope-finding", "WI-B|correction|Target B needs repair",
        "--scope-link", "WI-B|EVD-B",
        "--context-ref", "criteria:v1",
        "--comparability", "gap",
        "--comparability-gap", "target B source snapshot is unavailable",
        "--evaluated-at", "2026-08-19T01:02:03Z",
        "--proposed-classification", "continuation",
    ) == 0
    text = log.read_text(encoding="utf-8")
    assert '"event":"human.evaluation"' in text
    assert '"classification":"correction"' in text
    assert '"preceding_run_id"' in text
    assert '"target":"WI-B"' in text
    assert '"linked_targets":["EVD-B"]' in text
    assert '"comparability":"gap"' in text
    assert '"classification_source":"human_confirmed"' in text


def test_human_evaluation_does_not_accept_an_open_run(tmp_path: Path) -> None:
    log = tmp_path / "work" / "sessions" / "open.md"
    assert _run(
        tmp_path, "workflow", "run", "--task", "Open work", "--out", str(log),
        "--use-default-completion-conditions",
    ) == 0
    assert _run(
        tmp_path, "skill", "evaluate", "--log", str(log), "--decision", "accepted",
        "--classification", "continuation", "--next-handling", "continue_next_step",
        "--purpose-fit", "still fits", "--verified", "none", "--uncertainty", "none",
    ) == 1


def test_comparability_gap_requires_a_reason(tmp_path: Path) -> None:
    log = _closed_run(tmp_path)
    assert _run(
        tmp_path, "skill", "evaluate", "--log", str(log), "--decision", "accepted",
        "--classification", "continuation", "--next-handling", "continue_next_step",
        "--purpose-fit", "still fits", "--verified", "none", "--uncertainty", "none",
        "--comparability", "gap",
    ) == 1
