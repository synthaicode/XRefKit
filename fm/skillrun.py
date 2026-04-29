from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from fm.skillmeta import _parse_key_value_list, _parse_meta_lines, validate_skill_meta


@dataclass
class SkillRunResult:
    ok: bool
    skill_id: str | None
    skill_doc: str | None
    run_log: str | None
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "skill_id": self.skill_id,
            "skill_doc": self.skill_doc,
            "run_log": self.run_log,
            "errors": self.errors,
        }


VALID_PHASES = {"startup", "planning", "execution", "check", "closure", "handoff"}
VALID_PHASE_STATUSES = {"pending", "in_progress", "done", "blocked", "unknown", "escalated"}
PHASE_LABELS = {
    "startup": "Startup",
    "planning": "Planning",
    "execution": "Execution",
    "check": "Check",
    "closure": "Closure",
    "handoff": "Handoff",
}
PHASE_SECTIONS = {
    "execution": "Execution Role",
    "check": "Check Role",
    "closure": "Closure Gate",
    "handoff": "Handoff",
}


WORKLIST_ROWS = [
    ("Startup", "Confirm task, scope, active Skill, inputs, and loaded-context boundary."),
    ("Planning", "Create concrete work items, assumptions, target outputs, and handoff boundary."),
    ("Execution", "Execute the Skill procedure inside the declared capability and flow boundary."),
    ("Check", "Run the separate check role against evidence, output quality, unknowns, and handoff readiness."),
    ("Closure", "Apply the closure gate and keep pass, fail, unknown, and escalation states explicit."),
    ("Handoff", "Record outputs, unresolved items, next owner, and human decision points."),
]


def _safe_slug(value: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "_" for ch in value]
    slug = "".join(chars).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "skill"


def _read_task(args) -> tuple[str | None, list[str]]:
    if args.task and args.task_file:
        return None, ["use either --task or --task-file, not both"]
    if args.task_file:
        path = Path(args.task_file)
        if not path.exists():
            return None, [f"task file not found: {path}"]
        return path.read_text(encoding="utf-8").strip(), []
    if args.task:
        return str(args.task).strip(), []
    return None, ["missing --task or --task-file"]


def _default_log_path(root: Path, skill_id: str) -> Path:
    base = root / "work" / "sessions"
    filename = f"{date.today().isoformat()}_skill_run_{_safe_slug(skill_id)}.md"
    candidate = base / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    index = 2
    while True:
        numbered = base / f"{stem}_{index}{suffix}"
        if not numbered.exists():
            return numbered
        index += 1


def _render_log(
    *,
    skill_id: str,
    meta_path: Path,
    skill_doc: Path,
    task: str,
    os_contract: dict[str, str],
) -> str:
    contract_lines = "\n".join(f"- {key}: `{value}`" for key, value in os_contract.items())
    worklist_lines = "\n".join(
        f"- [ ] {name}: {description}" for name, description in WORKLIST_ROWS
    )
    return f"""# Skill Run Log

- date: `{date.today().isoformat()}`
- skill_id: `{skill_id}`
- meta: `{meta_path.as_posix()}`
- skill_doc: `{skill_doc.as_posix()}`
- task: {task}

## Skill Load Gate

- status: `opened_by_fm_skill_run`
- rule: do not open or execute the Skill procedure until this runtime envelope exists

## OS Contract

{contract_lines}

## Worklist

{worklist_lines}

## Execution Role

- status: `pending`
- responsibility: perform the Skill procedure inside the declared flow, capability, and guard boundary

## Check Role

- status: `pending`
- responsibility: independently check evidence, boundaries, output quality, unknowns, closure, and handoff readiness

## Unknowns And Risks

- status: `pending`
- rule: unknowns, missing evidence, risks, and unsupported assumptions must remain explicit

## Closure Gate

- status: `pending`
- rule: close only after execution, check, log, unknown/risk, and handoff rows are complete or explicitly escalated

## Handoff

- status: `pending`
- rule: record outputs, unresolved items, next owner, and human decision points
"""


def _replace_line(text: str, old: str, new: str) -> tuple[str, bool]:
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def _append_phase_event(text: str, *, phase: str, status: str, note: str | None) -> str:
    if "## Phase Events\n" not in text:
        text = text.rstrip() + "\n\n## Phase Events\n\n"
    note_text = note or ""
    event = f"- {date.today().isoformat()} `{phase}` -> `{status}`"
    if note_text:
        event += f": {note_text}"
    return text.rstrip() + "\n" + event + "\n"


def update_skill_phase(args) -> SkillRunResult:
    log_path = Path(args.log).resolve()
    if not log_path.exists():
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=[f"log not found: {log_path}"])

    phase = str(args.phase).lower()
    status = str(args.status).lower()
    if phase not in VALID_PHASES:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[f"invalid phase: {phase}"])
    if status not in VALID_PHASE_STATUSES:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[f"invalid status: {status}"])

    text = log_path.read_text(encoding="utf-8")
    label = PHASE_LABELS[phase]
    checkbox = "x" if status == "done" else "!"
    old_worklist = f"- [ ] {label}:"
    new_worklist = f"- [{checkbox}] {label}:"
    text, changed = _replace_line(text, old_worklist, new_worklist)
    if not changed:
        for marker in ("x", "!"):
            text, changed = _replace_line(text, f"- [{marker}] {label}:", new_worklist)
            if changed:
                break

    section = PHASE_SECTIONS.get(phase)
    if section:
        old_status = f"## {section}\n\n- status: `pending`"
        new_status = f"## {section}\n\n- status: `{status}`"
        text, status_changed = _replace_line(text, old_status, new_status)
        if not status_changed:
            for existing in VALID_PHASE_STATUSES:
                old_status = f"## {section}\n\n- status: `{existing}`"
                text, status_changed = _replace_line(text, old_status, new_status)
                if status_changed:
                    break

    text = _append_phase_event(text, phase=phase, status=status, note=args.note)
    log_path.write_text(text, encoding="utf-8")

    return SkillRunResult(ok=True, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[])


def run_skill(args) -> SkillRunResult:
    root = Path(args.root).resolve()
    meta_path = (root / args.meta).resolve()
    task, task_errors = _read_task(args)
    if task_errors:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=task_errors)

    if not meta_path.exists():
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=[f"meta not found: {meta_path}"])

    validation = validate_skill_meta(meta_path)
    if not validation.ok:
        return SkillRunResult(
            ok=False,
            skill_id=validation.skill_id,
            skill_doc=None,
            run_log=None,
            errors=validation.errors,
        )

    parsed = _parse_meta_lines(meta_path.read_text(encoding="utf-8"))
    skill_id = str(parsed.get("skill_id"))
    raw_skill_doc = str(parsed.get("skill_doc"))
    skill_doc_path = (meta_path.parent / raw_skill_doc).resolve()
    if not skill_doc_path.exists():
        return SkillRunResult(
            ok=False,
            skill_id=skill_id,
            skill_doc=str(skill_doc_path),
            run_log=None,
            errors=[f"skill_doc not found: {skill_doc_path}"],
        )
    os_contract = _parse_key_value_list(parsed.get("os_contract"))

    out_path = Path(args.out) if args.out else _default_log_path(root, skill_id)
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log = _render_log(
        skill_id=skill_id,
        meta_path=meta_path.relative_to(root),
        skill_doc=skill_doc_path.relative_to(root),
        task=str(task),
        os_contract=os_contract,
    )
    out_path.write_text(log, encoding="utf-8")

    return SkillRunResult(
        ok=True,
        skill_id=skill_id,
        skill_doc=str(skill_doc_path),
        run_log=str(out_path),
        errors=[],
    )


def cmd_skill_run(args) -> int:
    result = run_skill(args)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print(f"  skill_id: {result.skill_id}")
        print(f"  skill_doc: {result.skill_doc}")
        print("  next: open the Skill procedure from skill_doc and keep updating run_log with skill phase")
    else:
        print("fail: skill run")
        if result.skill_id:
            print(f"  skill_id: {result.skill_id}")
        for error in result.errors:
            print(f"  error: {error}")
    return 0 if result.ok else 1


def cmd_skill_phase(args) -> int:
    result = update_skill_phase(args)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print(f"  phase: {args.phase}")
        print(f"  status: {args.status}")
    else:
        print("fail: skill phase")
        for error in result.errors:
            print(f"  error: {error}")
    return 0 if result.ok else 1
