import json
import argparse
import subprocess
import uuid

from xrefkit.decision_trace import main
from xrefkit.skillrun import run_workflow_instruction


def test_event_impact_and_graph(tmp_path, capsys):
    assert main([
        "event", "--root", str(tmp_path), "--event-id", "DEC-1",
        "--event-type", "decision-change", "--reason", "initial decision",
    ]) == 0
    assert main([
        "event", "--root", str(tmp_path), "--event-id", "EVAL-1",
        "--event-type", "evaluation", "--reason", "evaluate provisional result",
        "--depends-on", "DEC-1",
    ]) == 0
    capsys.readouterr()

    assert main(["impact", "--root", str(tmp_path), "--event-id", "DEC-1", "--json"]) == 0
    impact = json.loads(capsys.readouterr().out)
    assert impact["direct_impact"] == ["EVAL-1"]
    assert impact["needs_human_review"] == ["EVAL-1"]
    assert impact["summary"]["groups"] == {"evaluation": 1}
    assert impact["groups"]["evaluation"][0]["review_required"] is True

    assert main(["graph", "--root", str(tmp_path)]) == 0
    graph = capsys.readouterr().out
    assert "DEC-1<br/>provisional" in graph
    assert "EVAL-1<br/>provisional" in graph
    assert "-->" in graph


def test_duplicate_event_is_rejected(tmp_path):
    args = [
        "event", "--root", str(tmp_path), "--event-id", "DEC-1",
        "--event-type", "decision-note", "--reason", "record",
    ]
    assert main(args) == 0
    assert main(args) == 2
    assert len((tmp_path / "work" / "decision-trace" / "events.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_checkpoint_commits_manifest_and_creates_tag(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Decision Trace Test")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "initial")

    assert main([
        "checkpoint", "--root", str(tmp_path), "--checkpoint-id", "CP-1",
        "--purpose", "before AI run", "--json",
    ]) == 0
    manifest = tmp_path / "work" / "decision-trace" / "checkpoints" / "CP-1.json"
    assert manifest.exists()
    assert json.loads(manifest.read_text(encoding="utf-8"))["git_commit"]
    assert git("rev-parse", "checkpoint/CP-1^{}").stdout.strip() == git("rev-parse", "HEAD").stdout.strip()
    assert "checkpoint: CP-1" in git("log", "-1", "--pretty=%s").stdout


def test_checkpoint_stops_on_dirty_worktree(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "README.md").write_text("uncommitted\n", encoding="utf-8")
    assert main([
        "checkpoint", "--root", str(tmp_path), "--checkpoint-id", "CP-1",
        "--purpose", "before AI run",
    ]) == 2


def test_branch_is_created_from_fixed_ref(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Decision Trace Test")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "initial")
    base = git("rev-parse", "HEAD").stdout.strip()

    assert main([
        "branch", "--root", str(tmp_path), "--branch", "hypothesis/decision-Y",
        "--from-ref", "HEAD", "--purpose", "provisional decision Y", "--json",
    ]) == 0
    assert git("rev-parse", "hypothesis/decision-Y").stdout.strip() == base


def test_branch_delete_preserves_disposal_adr(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Decision Trace Test")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "initial")
    git("branch", "hypothesis/decision-Y")

    assert main([
        "branch-delete", "--root", str(tmp_path), "--branch", "hypothesis/decision-Y",
        "--event-id", "ADR-002", "--reason", "performance evaluation failed", "--force", "--json",
    ]) == 0
    assert git("branch", "--list", "hypothesis/decision-Y").stdout.strip() == ""
    events = [
        json.loads(line)
        for line in (tmp_path / "work" / "decision-trace" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["status"] for event in events] == ["disposal-requested", "deleted"]
    assert events[1]["depends_on"] == ["ADR-002"]


def test_resolution_is_a_new_final_event(tmp_path):
    assert main([
        "event", "--root", str(tmp_path), "--event-id", "DEC-001",
        "--event-type", "decision-change", "--reason", "try Y",
    ]) == 0
    assert main([
        "resolve", "--root", str(tmp_path), "--event-id", "RES-001",
        "--target-event-id", "DEC-001", "--resolution", "rejected",
        "--reason", "evaluation failed", "--json",
    ]) == 0
    events = [
        json.loads(line)
        for line in (tmp_path / "work" / "decision-trace" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert events[0]["status"] == "provisional"
    assert events[0]["resolution"] is None
    assert events[1]["event_type"] == "resolution"
    assert events[1]["resolution"] == "rejected"
    assert events[1]["target_event_id"] == "DEC-001"


def test_return_check_and_execute_checkpoint_before_branching(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Decision Trace Test")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "initial")
    assert main([
        "event", "--root", str(tmp_path), "--event-id", "DEC-001",
        "--event-type", "decision-note", "--reason", "historical decision",
    ]) == 0

    assert main([
        "return-check", "--root", str(tmp_path), "--target-event-id", "DEC-001",
        "--to-ref", "HEAD", "--json",
    ]) == 0
    assert main([
        "return-execute", "--root", str(tmp_path), "--event-id", "RET-001",
        "--target-event-id", "DEC-001", "--to-ref", "HEAD",
        "--branch", "hypothesis/resume-DEC-001", "--checkpoint-id", "CP-RETURN-001",
        "--reason", "reconsider historical decision", "--confirmed", "--json",
    ]) == 0
    assert git("branch", "--list", "hypothesis/resume-DEC-001").stdout.strip()
    events = [
        json.loads(line)
        for line in (tmp_path / "work" / "decision-trace" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert events[-1]["event_type"] == "return"
    assert events[-1]["status"] == "provisional"
    assert events[-1]["human_decision"] == "confirmed"


def test_current_only_context_contains_only_dependency_lineage(tmp_path, capsys):
    for event_id, event_type, reason, dependencies in [
        ("DEC-001", "decision-note", "old decision", []),
        ("DEC-002", "decision-change", "new decision", ["DEC-001"]),
        ("EVAL-001", "evaluation", "evaluate new decision", ["DEC-002"]),
        ("DEC-OLD", "decision-note", "unrelated old path", []),
    ]:
        command = [
            "event", "--root", str(tmp_path), "--event-id", event_id,
            "--event-type", event_type, "--reason", reason,
        ]
        for dependency in dependencies:
            command.extend(["--depends-on", dependency])
        assert main(command) == 0
    capsys.readouterr()

    assert main(["context", "--root", str(tmp_path), "--event-id", "EVAL-001", "--json"]) == 0
    context = json.loads(capsys.readouterr().out)
    assert [event["event_id"] for event in context["events"]] == ["DEC-001", "DEC-002", "EVAL-001"]
    assert context["excluded_event_ids"] == ["DEC-OLD"]
    assert context["policy"] == "current-only"


def test_source_check_verifies_commit_and_path(tmp_path):
    source = tmp_path / "source"
    ledger = tmp_path / "ledger"
    source.mkdir()
    ledger.mkdir()

    def git(*args):
        return subprocess.run(["git", *args], cwd=source, check=True, capture_output=True, text=True)

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Decision Trace Test")
    (source / "src.txt").write_text("source\n", encoding="utf-8")
    git("add", "src.txt")
    git("commit", "-m", "source")
    commit = git("rev-parse", "HEAD").stdout.strip()
    assert main([
        "event", "--root", str(ledger), "--event-id", "SRC-001",
        "--event-type", "source-link", "--reason", "link source",
        "--source-repo", str(source), "--source-commit", commit, "--source-path", "src.txt",
    ]) == 0
    assert main([
        "source-check", "--root", str(ledger), "--event-id", "SRC-001",
        "--source-root", str(source), "--json",
    ]) == 0


def test_validate_checks_ledger_references(tmp_path, capsys):
    assert main([
        "event", "--root", str(tmp_path), "--event-id", "DEC-001",
        "--event-type", "decision-note", "--reason", "record",
    ]) == 0
    capsys.readouterr()
    assert main(["validate", "--root", str(tmp_path), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is True
    assert result["event_count"] == 1


def test_evaluation_point_records_criteria_as_provisional(tmp_path):
    assert main([
        "event", "--root", str(tmp_path), "--event-id", "DEC-001",
        "--event-type", "decision-change", "--reason", "try change",
    ]) == 0
    assert main([
        "evaluation-point", "--root", str(tmp_path), "--event-id", "EVP-001",
        "--target-event-id", "DEC-001", "--criteria", "performance under threshold",
        "--criteria", "source diff is traceable", "--evidence", "VER-001",
        "--reason", "whole evaluation after provisional application",
    ]) == 0
    events = [
        json.loads(line)
        for line in (tmp_path / "work" / "decision-trace" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert events[-1]["event_type"] == "evaluation-point"
    assert events[-1]["status"] == "provisional"
    assert events[-1]["criteria"] == ["performance under threshold", "source diff is traceable"]


def test_workflow_run_creates_automatic_checkpoint_in_git_worktree(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Decision Trace Test")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "initial")
    run_id = str(uuid.uuid4())
    result = run_workflow_instruction(argparse.Namespace(
        root=str(tmp_path), task="continue protocol work", task_file=None,
        completion_condition=["run log is created"], use_default_completion_conditions=False,
        run_id=run_id, out=str(tmp_path / "run.md"), flow_id=None, root_run_id=None,
        parent_run_id=None, work_item_id=None, node_id=None, purpose=None,
        scope_in=[], scope_out=[], owner=None, authority=None, expected_evidence=[], stop_condition=[],
    ))
    assert result.ok is True
    assert result.decision_trace_checkpoint["checkpoint"]["run_id"] == run_id
    assert "AI Decision Trace Checkpoint" in (tmp_path / "run.md").read_text(encoding="utf-8")
    assert git("rev-parse", f"checkpoint/CP-RUN-{run_id}^{{}}").stdout.strip()


def test_worktree_creates_isolated_hypothesis_checkout(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Decision Trace Test")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "initial")
    worktree_path = tmp_path.parent / f"{tmp_path.name}-hypothesis"
    assert main([
        "worktree", "--root", str(tmp_path), "--path", str(worktree_path),
        "--branch", "hypothesis/parallel-Y", "--from-ref", "HEAD",
        "--purpose", "parallel hypothesis evaluation", "--json",
    ]) == 0
    assert (worktree_path / "README.md").exists()
    assert git("-C", str(worktree_path), "branch", "--show-current").stdout.strip() == "hypothesis/parallel-Y"
    git("worktree", "remove", "--force", str(worktree_path))
