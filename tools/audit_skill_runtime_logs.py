from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fm.skillrun import (
    ACCEPTED_CLOSE_STATUSES,
    _assigned_role,
    _evaluate_closure_linkage,
    _parse_artifacts,
    _parse_concerns,
    _parse_work_items,
    _phase_has_role_event,
    _section_status,
)


DEFAULT_SESSIONS_DIR = REPO_ROOT / "work" / "sessions"


@dataclass
class SkillRuntimeAuditResult:
    checked: int
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _tracked_session_logs(root: Path, sessions_dir: Path) -> list[Path]:
    try:
        rel = sessions_dir.relative_to(root).as_posix()
    except ValueError:
        return []

    result = subprocess.run(
        ["git", "ls-files", rel],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [root / line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".md")]


def _all_session_logs(sessions_dir: Path) -> list[Path]:
    if not sessions_dir.exists():
        return []
    return sorted(path for path in sessions_dir.rglob("*.md") if path.is_file())


def _iter_session_logs(root: Path, sessions_dir: Path, *, tracked_only: bool) -> list[Path]:
    if tracked_only:
        return sorted(path for path in _tracked_session_logs(root, sessions_dir) if path.exists())
    return _all_session_logs(sessions_dir)


def _is_skill_run_log(text: str) -> bool:
    return text.lstrip().startswith("# Skill Run Log") or (
        "- skill_id: `" in text and "## OS Contract" in text and "## Closure Gate" in text
    )


def _format_error(path: Path, root: Path, message: str) -> str:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.as_posix()
    return f"{rel}: {message}"


def _audit_one(path: Path, root: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if not _is_skill_run_log(text):
        return []

    errors: list[str] = []
    if "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`" not in text:
        errors.append("missing fm skill run load gate")

    closure_status = _section_status(text, "Closure Gate")
    if closure_status not in ACCEPTED_CLOSE_STATUSES:
        errors.append(f"Closure Gate must be done or escalated; current={closure_status or 'missing'}")

    for section in ("Execution Role", "Check Role", "Handoff"):
        status = _section_status(text, section)
        if status not in ACCEPTED_CLOSE_STATUSES:
            errors.append(f"{section} must be done or escalated; current={status or 'missing'}")

    executor = _assigned_role(text, "executor")
    checker = _assigned_role(text, "checker")
    handoff_owner = _assigned_role(text, "handoff_owner")
    if not executor or not checker or not handoff_owner:
        errors.append("runtime role assignment is incomplete")
    elif executor == checker:
        errors.append("executor and checker roles must be different")
    else:
        if not _phase_has_role_event(text, phase="execution", role=executor):
            errors.append(f"execution phase was not completed by assigned executor role {executor}")
        if not _phase_has_role_event(text, phase="check", role=checker):
            errors.append(f"check phase was not completed by assigned checker role {checker}")
        if not _phase_has_role_event(text, phase="handoff", role=handoff_owner):
            errors.append(f"handoff phase was not completed by assigned handoff_owner role {handoff_owner}")

    work_items = _parse_work_items(text)
    if not work_items:
        errors.append("at least one concrete work item is required")
    for item in work_items:
        if item["status"] not in ACCEPTED_CLOSE_STATUSES:
            errors.append(
                f"work item {item['item_id']} must be done or escalated; current={item['status']}"
            )

    artifacts = _parse_artifacts(text)
    artifact_kinds = {artifact["kind"] for artifact in artifacts}
    if "output" not in artifact_kinds:
        errors.append("at least one output artifact is required")
    if "evidence" not in artifact_kinds:
        errors.append("at least one evidence artifact is required")
    for artifact in artifacts:
        if artifact["status"] not in ACCEPTED_CLOSE_STATUSES:
            errors.append(
                f"artifact {artifact['artifact_id']} must be done or escalated; current={artifact['status']}"
            )

    concerns = _parse_concerns(text)
    concern_errors, _ = _evaluate_closure_linkage(concerns=concerns, artifacts=artifacts)
    errors.extend(concern_errors)

    return [_format_error(path, root, error) for error in errors]


def audit_skill_runtime_logs(
    *, root: Path = REPO_ROOT, sessions_dir: Path = DEFAULT_SESSIONS_DIR, tracked_only: bool = False
) -> SkillRuntimeAuditResult:
    root = root.resolve()
    sessions_dir = sessions_dir.resolve()
    logs = _iter_session_logs(root, sessions_dir, tracked_only=tracked_only)

    checked = 0
    errors: list[str] = []
    for path in logs:
        text = path.read_text(encoding="utf-8")
        if not _is_skill_run_log(text):
            continue
        checked += 1
        errors.extend(_audit_one(path, root))

    return SkillRuntimeAuditResult(checked=checked, errors=errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Skill runtime envelope session logs")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root")
    parser.add_argument(
        "--sessions-dir",
        default=None,
        help="Session log directory; defaults to <root>/work/sessions",
    )
    parser.add_argument(
        "--tracked-only",
        action="store_true",
        help="Audit only Git-tracked session logs; intended for CI/quality gate use",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    sessions_dir = Path(args.sessions_dir).resolve() if args.sessions_dir else root / "work" / "sessions"
    result = audit_skill_runtime_logs(root=root, sessions_dir=sessions_dir, tracked_only=args.tracked_only)
    if result.errors:
        print(f"fail: skill runtime log audit checked={result.checked}")
        for error in result.errors:
            print(f"  error: {error}")
        return 1

    print(f"ok: skill runtime log audit checked={result.checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
