"""Portable decision-trace ledger for human-AI collaborative work."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEDGER_RELATIVE = Path("work") / "decision-trace" / "events.jsonl"
CHECKPOINT_RELATIVE = Path("work") / "decision-trace" / "checkpoints"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).resolve()


def _ledger(root: Path) -> Path:
    return root / LEDGER_RELATIVE


def _read_events(root: Path) -> list[dict[str, Any]]:
    path = _ledger(root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid decision-trace JSON at line {line_number}") from exc
        if not isinstance(value, dict) or not value.get("event_id"):
            raise ValueError(f"decision-trace event at line {line_number} must be an object with event_id")
        events.append(value)
    return events


def _write_event(root: Path, event: dict[str, Any]) -> None:
    path = _ledger(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_events(root)
    if any(item.get("event_id") == event["event_id"] for item in existing):
        raise ValueError(f"event_id already exists: {event['event_id']}")
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _emit(payload: Any, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _list_values(values: list[str] | None) -> list[str]:
    return list(values or [])


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ValueError(detail)
    return result.stdout.strip()


def _has_non_trace_changes(root: Path) -> bool:
    output = _git(root, "status", "--porcelain", "--untracked-files=all")
    for line in output.splitlines():
        path = line[3:].strip().split(" -> ")[-1].replace("\\", "/").lstrip("./")
        if not path.casefold().startswith("work/decision-trace"):
            return True
    return False


def _event_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "recorded_by": "ai_protocol",
        "event_id": args.event_id,
        "event_type": args.event_type,
        "status": args.status,
        "resolution": None,
        "created_at": _now(),
        "from_decision": args.from_decision,
        "to_decision": args.to_decision,
        "reason": args.reason,
        "evidence": _list_values(args.evidence),
        "depends_on": _list_values(args.depends_on),
        "affected": _list_values(args.affected),
        "source_repo": args.source_repo,
        "source_commit": args.source_commit,
        "source_path": args.source_path,
        "branch": args.branch,
        "base_ref": args.base_ref,
        "human_decision": args.human_decision,
    }


def _impact_group(event: dict[str, Any]) -> str:
    event_type = event.get("event_type")
    return {
        "decision-change": "decision",
        "decision-note": "decision",
        "re-adopt": "decision",
        "plan-change": "plan",
        "investigation": "investigation_verification",
        "verification": "investigation_verification",
        "provisional-apply": "provisional",
        "evaluation": "evaluation",
        "artifact": "artifact",
        "source-link": "source",
        "branch-disposal": "branch_lifecycle",
        "resolution": "resolution",
        "return": "return",
        "evaluation-point": "evaluation",
    }.get(event_type, "unknown")


def _impact_candidate(event: dict[str, Any], distance: str) -> dict[str, Any]:
    candidate = {
        "event_id": event["event_id"],
        "event_type": event.get("event_type"),
        "group": _impact_group(event),
        "status": event.get("status", "unknown"),
        "distance": distance,
        "review_required": True,
        "reason": event.get("reason"),
    }
    source = {
        key: event.get(key)
        for key in ("source_repo", "source_commit", "source_path")
        if event.get(key)
    }
    if source:
        candidate["source"] = source
    if event.get("affected"):
        candidate["affected"] = event["affected"]
    return candidate


def _impact(root: Path, event_id: str) -> dict[str, Any]:
    events = _read_events(root)
    by_id = {event["event_id"]: event for event in events}
    if event_id not in by_id:
        raise ValueError(f"unknown event_id: {event_id}")
    dependents: dict[str, set[str]] = defaultdict(set)
    for event in events:
        for dependency in event.get("depends_on", []):
            dependents[dependency].add(event["event_id"])
    direct = sorted(dependents.get(event_id, set()))
    seen = set(direct)
    queue = deque(direct)
    while queue:
        current = queue.popleft()
        for dependent in sorted(dependents.get(current, set())):
            if dependent not in seen:
                seen.add(dependent)
                queue.append(dependent)
    direct_candidates = [_impact_candidate(by_id[item], "direct") for item in direct]
    transitive_candidates = [
        _impact_candidate(by_id[item], "transitive") for item in sorted(seen) if item not in direct
    ]
    candidates = direct_candidates + transitive_candidates
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        groups[candidate["group"]].append(candidate)
    return {
        "root_event": event_id,
        "direct_impact": direct,
        "transitive_impact": sorted(seen),
        "needs_human_review": sorted(seen),
        "summary": {
            "direct": len(direct),
            "transitive": len(seen),
            "needs_human_review": len(seen),
            "groups": {key: len(value) for key, value in sorted(groups.items())},
        },
        "groups": {key: value for key, value in sorted(groups.items())},
    }


def _graph(root: Path) -> str:
    events = _read_events(root)
    lines = ["flowchart TD"]
    node_ids = {str(event["event_id"]): f"n{index}" for index, event in enumerate(events, start=1)}
    for event in events:
        raw_event_id = str(event["event_id"])
        event_id = raw_event_id.replace('"', "'")
        status = str(event.get("status", "unknown")).replace('"', "'")
        lines.append(f'    {node_ids[raw_event_id]}["{event_id}<br/>{status}"]')
        for dependency in event.get("depends_on", []):
            source = node_ids.get(str(dependency), f'unknown_{len(node_ids)}')
            lines.append(f"    {source} --> {node_ids[raw_event_id]}")
    return "\n".join(lines)


def _checkpoint(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if _has_non_trace_changes(root):
        raise ValueError("working tree has non-trace changes; checkpoint requires human handling of uncommitted changes")
    base_commit = _git(root, "rev-parse", "HEAD")
    tag = args.tag or f"checkpoint/{args.checkpoint_id}"
    checkpoint_dir = root / CHECKPOINT_RELATIVE
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "recorded_by": "ai_protocol",
        "checkpoint_id": args.checkpoint_id,
        "checkpoint_type": args.checkpoint_type,
        "created_at": _now(),
        "git_commit": base_commit,
        "purpose": args.purpose,
        "work_item_id": args.work_item_id,
        "run_id": args.run_id,
        "context_policy": args.context_policy,
        "human_approved": False,
    }
    manifest_path = checkpoint_dir / f"{args.checkpoint_id}.json"
    if manifest_path.exists():
        raise ValueError(f"checkpoint_id already exists: {args.checkpoint_id}")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        relative_manifest = str(manifest_path.relative_to(root))
        _git(root, "add", "--", relative_manifest)
        _git(root, "commit", "--only", "-m", f"checkpoint: {args.checkpoint_id}", "--", relative_manifest)
        commit = _git(root, "rev-parse", "HEAD")
        _git(root, "tag", "-a", tag, commit, "-m", json.dumps(manifest, ensure_ascii=False))
    except ValueError:
        # Preserve the manifest for diagnosis if commit/tag setup fails.
        raise
    return {
        "checkpoint": manifest,
        "checkpoint_commit": commit,
        "tag": tag,
        "manifest": str(manifest_path.relative_to(root)),
    }


def _branch(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if _has_non_trace_changes(root):
        raise ValueError("working tree has non-trace changes; branch creation requires human handling of uncommitted changes")
    branch = args.branch
    if _git(root, "branch", "--list", branch):
        raise ValueError(f"branch already exists: {branch}")
    base_ref = args.from_ref or "HEAD"
    base_commit = _git(root, "rev-parse", base_ref)
    _git(root, "branch", branch, base_ref)
    return {
        "recorded_by": "ai_protocol",
        "branch": branch,
        "base_ref": base_ref,
        "base_commit": base_commit,
        "purpose": args.purpose,
        "decision_event_id": args.decision_event_id,
        "human_approved": False,
    }


def _branch_delete(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if _git(root, "branch", "--show-current") == args.branch:
        raise ValueError("cannot delete the currently checked out branch")
    if not _git(root, "branch", "--list", args.branch):
        raise ValueError(f"branch does not exist: {args.branch}")
    branch_commit = _git(root, "rev-parse", args.branch)
    request = {
        "recorded_by": "ai_protocol",
        "event_id": args.event_id,
        "event_type": "branch-disposal",
        "status": "disposal-requested",
        "created_at": _now(),
        "branch": args.branch,
        "base_ref": args.base_ref,
        "branch_commit": branch_commit,
        "reason": args.reason,
        "depends_on": _list_values(args.depends_on),
        "human_decision": "pending",
    }
    _write_event(root, request)
    delete_args = ["branch", "-D" if args.force else "-d", args.branch]
    try:
        _git(root, *delete_args)
    except ValueError:
        raise
    completed = dict(request)
    completed["event_id"] = f"{args.event_id}-completed"
    completed["status"] = "deleted"
    completed["created_at"] = _now()
    completed["human_decision"] = "confirmed-by-command"
    completed["depends_on"] = [args.event_id]
    _write_event(root, completed)
    return {"requested": request, "deleted": completed}


def _resolve(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    events = _read_events(root)
    if not any(event.get("event_id") == args.target_event_id for event in events):
        raise ValueError(f"unknown target event_id: {args.target_event_id}")
    resolution = {
        "recorded_by": "ai_protocol",
        "event_id": args.event_id,
        "event_type": "resolution",
        "status": "recorded",
        "resolution": args.resolution,
        "created_at": _now(),
        "target_event_id": args.target_event_id,
        "evaluation_event_id": args.evaluation_event_id,
        "reason": args.reason,
        "depends_on": [args.target_event_id, *(_list_values(args.depends_on))],
        "human_decision": "required",
    }
    _write_event(root, resolution)
    return resolution


def _return_check(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    events = _read_events(root)
    target = next((event for event in events if event.get("event_id") == args.target_event_id), None)
    if target is None:
        raise ValueError(f"unknown target event_id: {args.target_event_id}")
    to_commit = _git(root, "rev-parse", args.to_ref)
    current_commit = _git(root, "rev-parse", "HEAD")
    impact = _impact(root, args.target_event_id)
    return {
        "target_event_id": args.target_event_id,
        "to_ref": args.to_ref,
        "to_commit": to_commit,
        "current_commit": current_commit,
        "impact": impact,
        "requires_human_confirmation": True,
        "execution_allowed": False,
    }


def _return_execute(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not args.confirmed:
        raise ValueError("return execution requires explicit confirmation")
    checked = _return_check(root, args)
    checkpoint_args = argparse.Namespace(
        checkpoint_id=args.checkpoint_id,
        checkpoint_type="resume",
        purpose=f"before return to {args.target_event_id}",
        work_item_id=None,
        run_id=None,
        context_policy="current-only",
        tag=None,
    )
    checkpoint = _checkpoint(root, checkpoint_args)
    if _git(root, "branch", "--list", args.branch):
        raise ValueError(f"branch already exists: {args.branch}")
    _git(root, "branch", args.branch, checked["to_commit"])
    event = {
        "recorded_by": "ai_protocol",
        "event_id": args.event_id,
        "event_type": "return",
        "status": "provisional",
        "resolution": None,
        "created_at": _now(),
        "target_event_id": args.target_event_id,
        "from_checkpoint": checkpoint["checkpoint"]["checkpoint_id"],
        "to_ref": args.to_ref,
        "to_commit": checked["to_commit"],
        "branch": args.branch,
        "reason": args.reason,
        "depends_on": [args.target_event_id],
        "human_decision": "confirmed",
    }
    _write_event(root, event)
    return {"checkpoint": checkpoint, "return": event, "impact": checked["impact"]}


def _context(root: Path, event_id: str) -> dict[str, Any]:
    events = _read_events(root)
    by_id = {event["event_id"]: event for event in events}
    if event_id not in by_id:
        raise ValueError(f"unknown event_id: {event_id}")
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    visiting: set[str] = set()

    def visit(current_id: str) -> None:
        if current_id in selected_ids:
            return
        if current_id in visiting:
            raise ValueError(f"cycle in decision-trace dependencies at: {current_id}")
        visiting.add(current_id)
        event = by_id[current_id]
        for dependency in event.get("depends_on", []):
            if dependency in by_id:
                visit(dependency)
        visiting.remove(current_id)
        selected_ids.add(current_id)
        selected.append(event)

    visit(event_id)
    return {
        "policy": "current-only",
        "root_event": event_id,
        "events": selected,
        "excluded_event_ids": sorted(set(by_id) - selected_ids),
    }


def _source_check(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    events = _read_events(root)
    event = next((item for item in events if item.get("event_id") == args.event_id), None)
    if event is None:
        raise ValueError(f"unknown event_id: {args.event_id}")
    commit = event.get("source_commit")
    path = event.get("source_path")
    if not commit or not path:
        raise ValueError(f"event {args.event_id} has no source_commit and source_path")
    source_root = Path(args.source_root).resolve()
    _git(source_root, "cat-file", "-e", f"{commit}^{{commit}}")
    listed = _git(source_root, "ls-tree", "--full-tree", "--name-only", "-r", commit, "--", path)
    if path not in listed.splitlines():
        raise ValueError(f"source_path not found at source_commit: {path}")
    return {
        "event_id": args.event_id,
        "source_repo": event.get("source_repo"),
        "source_commit": commit,
        "source_path": path,
        "verified": True,
    }


def _validate(root: Path) -> dict[str, Any]:
    events = _read_events(root)
    issues: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        event_id = event.get("event_id")
        if event_id in by_id:
            issues.append(f"duplicate event_id: {event_id}")
        else:
            by_id[event_id] = event
    for event in events:
        event_id = event["event_id"]
        for dependency in event.get("depends_on", []):
            if dependency not in by_id:
                issues.append(f"unknown dependency: {event_id} -> {dependency}")
        if event.get("event_type") == "resolution" and event.get("target_event_id") not in by_id:
            issues.append(f"resolution target not found: {event_id} -> {event.get('target_event_id')}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(event_id: str) -> None:
        if event_id in visiting:
            issues.append(f"dependency cycle at: {event_id}")
            return
        if event_id in visited or event_id not in by_id:
            return
        visiting.add(event_id)
        for dependency in by_id[event_id].get("depends_on", []):
            visit(dependency)
        visiting.remove(event_id)
        visited.add(event_id)

    for event_id in by_id:
        visit(event_id)
    return {"valid": not issues, "event_count": len(events), "issues": sorted(set(issues))}


def _evaluation_point(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    events = _read_events(root)
    if not any(event.get("event_id") == args.target_event_id for event in events):
        raise ValueError(f"unknown target event_id: {args.target_event_id}")
    event = {
        "recorded_by": "ai_protocol",
        "event_id": args.event_id,
        "event_type": "evaluation-point",
        "status": "provisional",
        "resolution": None,
        "created_at": _now(),
        "target_event_id": args.target_event_id,
        "criteria": _list_values(args.criteria),
        "evidence": _list_values(args.evidence),
        "reason": args.reason,
        "depends_on": [args.target_event_id],
        "human_decision": "pending",
    }
    _write_event(root, event)
    return event


def _worktree(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if _has_non_trace_changes(root):
        raise ValueError("working tree has non-trace changes; worktree creation requires human handling of uncommitted changes")
    path = str(Path(args.path).resolve())
    branch_exists = bool(_git(root, "branch", "--list", args.branch))
    if branch_exists:
        _git(root, "worktree", "add", path, args.branch)
        base_ref = args.from_ref or args.branch
    else:
        base_ref = args.from_ref or "HEAD"
        _git(root, "worktree", "add", "-b", args.branch, path, base_ref)
    return {
        "recorded_by": "ai_protocol",
        "path": path,
        "branch": args.branch,
        "base_ref": base_ref,
        "purpose": args.purpose,
    }


def add_trace_parser(subparsers: argparse._SubParsersAction) -> None:
    trace = subparsers.add_parser("trace", help="AI protocol adapter for decision changes and Git checkpoints")
    sub = trace.add_subparsers(dest="trace_cmd", required=True)

    event = sub.add_parser("event", help="Append one decision-change event")
    event.add_argument("--root", default=".")
    event.add_argument("--event-id", required=True)
    event.add_argument("--event-type", required=True, choices=["decision-change", "evaluation", "evaluation-point", "re-adopt", "provisional-apply", "decision-note", "plan-change", "investigation", "verification", "artifact", "source-link", "branch-disposal", "return"])
    event.add_argument("--status", default="provisional", choices=["provisional", "accepted", "rejected", "re-adopted", "needs-review", "superseded", "disposal-requested", "deleted"])
    event.add_argument("--from-decision", default=None)
    event.add_argument("--to-decision", default=None)
    event.add_argument("--reason", required=True)
    event.add_argument("--evidence", action="append", default=[])
    event.add_argument("--depends-on", action="append", default=[])
    event.add_argument("--affected", action="append", default=[])
    event.add_argument("--source-repo", default=None)
    event.add_argument("--source-commit", default=None)
    event.add_argument("--source-path", default=None)
    event.add_argument("--branch", default=None)
    event.add_argument("--base-ref", default=None)
    event.add_argument("--human-decision", default="pending")
    event.add_argument("--json", action="store_true")

    impact = sub.add_parser("impact", help="Show direct and transitive impact candidates")
    impact.add_argument("--root", default=".")
    impact.add_argument("--event-id", required=True)
    impact.add_argument("--json", action="store_true")

    graph = sub.add_parser("graph", help="Render the recorded dependency graph as Mermaid")
    graph.add_argument("--root", default=".")
    graph.add_argument("--json", action="store_true")

    checkpoint = sub.add_parser("checkpoint", help="Create a named Git restore point and manifest")
    checkpoint.add_argument("--root", default=".")
    checkpoint.add_argument("--checkpoint-id", required=True)
    checkpoint.add_argument("--checkpoint-type", default="before-ai-run", choices=["before-ai-run", "decision", "evaluation", "resume"])
    checkpoint.add_argument("--purpose", required=True)
    checkpoint.add_argument("--work-item-id", default=None)
    checkpoint.add_argument("--run-id", default=None)
    checkpoint.add_argument("--context-policy", default="current-only")
    checkpoint.add_argument("--tag", default=None)
    checkpoint.add_argument("--json", action="store_true")

    branch = sub.add_parser("branch", help="Create a provisional hypothesis branch from a fixed ref")
    branch.add_argument("--root", default=".")
    branch.add_argument("--branch", required=True)
    branch.add_argument("--from-ref", default=None)
    branch.add_argument("--purpose", required=True)
    branch.add_argument("--decision-event-id", default=None)
    branch.add_argument("--json", action="store_true")

    branch_delete = sub.add_parser("branch-delete", help="Record and delete a rejected hypothesis branch")
    branch_delete.add_argument("--root", default=".")
    branch_delete.add_argument("--branch", required=True)
    branch_delete.add_argument("--event-id", required=True)
    branch_delete.add_argument("--base-ref", default=None)
    branch_delete.add_argument("--reason", required=True)
    branch_delete.add_argument("--depends-on", action="append", default=[])
    branch_delete.add_argument("--force", action="store_true", help="Delete an unmerged branch explicitly")
    branch_delete.add_argument("--json", action="store_true")

    resolve = sub.add_parser("resolve", help="Record the final resolution without rewriting provisional events")
    resolve.add_argument("--root", default=".")
    resolve.add_argument("--event-id", required=True)
    resolve.add_argument("--target-event-id", required=True)
    resolve.add_argument("--evaluation-event-id", default=None)
    resolve.add_argument("--resolution", required=True, choices=["adopted", "rejected", "re-adopted", "revised"])
    resolve.add_argument("--reason", required=True)
    resolve.add_argument("--depends-on", action="append", default=[])
    resolve.add_argument("--json", action="store_true")

    return_check = sub.add_parser("return-check", help="Check a historical return target without changing state")
    return_check.add_argument("--root", default=".")
    return_check.add_argument("--target-event-id", required=True)
    return_check.add_argument("--to-ref", required=True)
    return_check.add_argument("--json", action="store_true")

    return_execute = sub.add_parser("return-execute", help="Create a checkpoint and provisional branch for a confirmed return")
    return_execute.add_argument("--root", default=".")
    return_execute.add_argument("--event-id", required=True)
    return_execute.add_argument("--target-event-id", required=True)
    return_execute.add_argument("--to-ref", required=True)
    return_execute.add_argument("--branch", required=True)
    return_execute.add_argument("--checkpoint-id", required=True)
    return_execute.add_argument("--reason", required=True)
    return_execute.add_argument("--confirmed", action="store_true")
    return_execute.add_argument("--json", action="store_true")

    context = sub.add_parser("context", help="Build current-only AI context from one event lineage")
    context.add_argument("--root", default=".")
    context.add_argument("--event-id", required=True)
    context.add_argument("--json", action="store_true")

    source_check = sub.add_parser("source-check", help="Verify a source commit and path for an event")
    source_check.add_argument("--root", default=".")
    source_check.add_argument("--event-id", required=True)
    source_check.add_argument("--source-root", required=True)
    source_check.add_argument("--json", action="store_true")
    validate = sub.add_parser("validate", help="Validate the decision-trace ledger before continuing")
    validate.add_argument("--root", default=".")
    validate.add_argument("--json", action="store_true")
    worktree = sub.add_parser("worktree", help="Create an isolated AI hypothesis worktree")
    worktree.add_argument("--root", default=".")
    worktree.add_argument("--path", required=True)
    worktree.add_argument("--branch", required=True)
    worktree.add_argument("--from-ref", default=None)
    worktree.add_argument("--purpose", required=True)
    worktree.add_argument("--json", action="store_true")
    evaluation_point = sub.add_parser("evaluation-point", help="Create a provisional whole-evaluation point with criteria")
    evaluation_point.add_argument("--root", default=".")
    evaluation_point.add_argument("--event-id", required=True)
    evaluation_point.add_argument("--target-event-id", required=True)
    evaluation_point.add_argument("--criteria", action="append", required=True)
    evaluation_point.add_argument("--evidence", action="append", default=[])
    evaluation_point.add_argument("--reason", required=True)
    evaluation_point.add_argument("--json", action="store_true")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xrefkit trace", description="AI protocol adapter for decision changes and Git checkpoints")
    subparsers = parser.add_subparsers(dest="trace_cmd", required=True)
    # The standalone parser has the trace command as its root, so add the
    # operation-specific parsers directly.
    sub = subparsers

    event = sub.add_parser("event", help="Append one decision-change event")
    event.add_argument("--root", default=".")
    event.add_argument("--event-id", required=True)
    event.add_argument("--event-type", required=True, choices=["decision-change", "evaluation", "evaluation-point", "re-adopt", "provisional-apply", "decision-note", "plan-change", "investigation", "verification", "artifact", "source-link", "branch-disposal", "return"])
    event.add_argument("--status", default="provisional", choices=["provisional", "accepted", "rejected", "re-adopted", "needs-review", "superseded", "disposal-requested", "deleted"])
    event.add_argument("--from-decision", default=None)
    event.add_argument("--to-decision", default=None)
    event.add_argument("--reason", required=True)
    event.add_argument("--evidence", action="append", default=[])
    event.add_argument("--depends-on", action="append", default=[])
    event.add_argument("--affected", action="append", default=[])
    event.add_argument("--source-repo", default=None)
    event.add_argument("--source-commit", default=None)
    event.add_argument("--source-path", default=None)
    event.add_argument("--branch", default=None)
    event.add_argument("--base-ref", default=None)
    event.add_argument("--human-decision", default="pending")
    event.add_argument("--json", action="store_true")

    impact = sub.add_parser("impact", help="Show direct and transitive impact candidates")
    impact.add_argument("--root", default=".")
    impact.add_argument("--event-id", required=True)
    impact.add_argument("--json", action="store_true")

    graph = sub.add_parser("graph", help="Render the recorded dependency graph as Mermaid")
    graph.add_argument("--root", default=".")
    graph.add_argument("--json", action="store_true")

    checkpoint = sub.add_parser("checkpoint", help="Create a named Git restore point and manifest")
    checkpoint.add_argument("--root", default=".")
    checkpoint.add_argument("--checkpoint-id", required=True)
    checkpoint.add_argument("--checkpoint-type", default="before-ai-run", choices=["before-ai-run", "decision", "evaluation", "resume"])
    checkpoint.add_argument("--purpose", required=True)
    checkpoint.add_argument("--work-item-id", default=None)
    checkpoint.add_argument("--run-id", default=None)
    checkpoint.add_argument("--context-policy", default="current-only")
    checkpoint.add_argument("--tag", default=None)
    checkpoint.add_argument("--json", action="store_true")
    branch = sub.add_parser("branch", help="Create a provisional hypothesis branch from a fixed ref")
    branch.add_argument("--root", default=".")
    branch.add_argument("--branch", required=True)
    branch.add_argument("--from-ref", default=None)
    branch.add_argument("--purpose", required=True)
    branch.add_argument("--decision-event-id", default=None)
    branch.add_argument("--json", action="store_true")
    branch_delete = sub.add_parser("branch-delete", help="Record and delete a rejected hypothesis branch")
    branch_delete.add_argument("--root", default=".")
    branch_delete.add_argument("--branch", required=True)
    branch_delete.add_argument("--event-id", required=True)
    branch_delete.add_argument("--base-ref", default=None)
    branch_delete.add_argument("--reason", required=True)
    branch_delete.add_argument("--depends-on", action="append", default=[])
    branch_delete.add_argument("--force", action="store_true", help="Delete an unmerged branch explicitly")
    branch_delete.add_argument("--json", action="store_true")
    resolve = sub.add_parser("resolve", help="Record the final resolution without rewriting provisional events")
    resolve.add_argument("--root", default=".")
    resolve.add_argument("--event-id", required=True)
    resolve.add_argument("--target-event-id", required=True)
    resolve.add_argument("--evaluation-event-id", default=None)
    resolve.add_argument("--resolution", required=True, choices=["adopted", "rejected", "re-adopted", "revised"])
    resolve.add_argument("--reason", required=True)
    resolve.add_argument("--depends-on", action="append", default=[])
    resolve.add_argument("--json", action="store_true")
    return_check = sub.add_parser("return-check", help="Check a historical return target without changing state")
    return_check.add_argument("--root", default=".")
    return_check.add_argument("--target-event-id", required=True)
    return_check.add_argument("--to-ref", required=True)
    return_check.add_argument("--json", action="store_true")
    return_execute = sub.add_parser("return-execute", help="Create a checkpoint and provisional branch for a confirmed return")
    return_execute.add_argument("--root", default=".")
    return_execute.add_argument("--event-id", required=True)
    return_execute.add_argument("--target-event-id", required=True)
    return_execute.add_argument("--to-ref", required=True)
    return_execute.add_argument("--branch", required=True)
    return_execute.add_argument("--checkpoint-id", required=True)
    return_execute.add_argument("--reason", required=True)
    return_execute.add_argument("--confirmed", action="store_true")
    return_execute.add_argument("--json", action="store_true")
    context = sub.add_parser("context", help="Build current-only AI context from one event lineage")
    context.add_argument("--root", default=".")
    context.add_argument("--event-id", required=True)
    context.add_argument("--json", action="store_true")
    source_check = sub.add_parser("source-check", help="Verify a source commit and path for an event")
    source_check.add_argument("--root", default=".")
    source_check.add_argument("--event-id", required=True)
    source_check.add_argument("--source-root", required=True)
    source_check.add_argument("--json", action="store_true")
    validate = sub.add_parser("validate", help="Validate the decision-trace ledger before continuing")
    validate.add_argument("--root", default=".")
    validate.add_argument("--json", action="store_true")
    worktree = sub.add_parser("worktree", help="Create an isolated AI hypothesis worktree")
    worktree.add_argument("--root", default=".")
    worktree.add_argument("--path", required=True)
    worktree.add_argument("--branch", required=True)
    worktree.add_argument("--from-ref", default=None)
    worktree.add_argument("--purpose", required=True)
    worktree.add_argument("--json", action="store_true")
    evaluation_point = sub.add_parser("evaluation-point", help="Create a provisional whole-evaluation point with criteria")
    evaluation_point.add_argument("--root", default=".")
    evaluation_point.add_argument("--event-id", required=True)
    evaluation_point.add_argument("--target-event-id", required=True)
    evaluation_point.add_argument("--criteria", action="append", required=True)
    evaluation_point.add_argument("--evidence", action="append", default=[])
    evaluation_point.add_argument("--reason", required=True)
    evaluation_point.add_argument("--json", action="store_true")
    return parser


def cmd_trace(args: argparse.Namespace) -> int:
    try:
        root = _root(args)
        if args.trace_cmd == "event":
            event = _event_payload(args)
            _write_event(root, event)
            _emit(event, args.json)
        elif args.trace_cmd == "impact":
            _emit(_impact(root, args.event_id), args.json)
        elif args.trace_cmd == "graph":
            _emit(_graph(root), args.json)
        elif args.trace_cmd == "checkpoint":
            _emit(_checkpoint(root, args), args.json)
        elif args.trace_cmd == "branch":
            _emit(_branch(root, args), args.json)
        elif args.trace_cmd == "branch-delete":
            _emit(_branch_delete(root, args), args.json)
        elif args.trace_cmd == "resolve":
            _emit(_resolve(root, args), args.json)
        elif args.trace_cmd == "return-check":
            _emit(_return_check(root, args), args.json)
        elif args.trace_cmd == "return-execute":
            _emit(_return_execute(root, args), args.json)
        elif args.trace_cmd == "context":
            _emit(_context(root, args.event_id), args.json)
        elif args.trace_cmd == "source-check":
            _emit(_source_check(root, args), args.json)
        elif args.trace_cmd == "validate":
            result = _validate(root)
            _emit(result, args.json)
            return 0 if result["valid"] else 2
        elif args.trace_cmd == "worktree":
            _emit(_worktree(root, args), args.json)
        elif args.trace_cmd == "evaluation-point":
            _emit(_evaluation_point(root, args), args.json)
        else:
            raise ValueError(f"unknown trace command: {args.trace_cmd}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"xrefkit trace: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    return cmd_trace(_build_parser().parse_args(argv))
