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
    assigned_roles: dict[str, str] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "skill_id": self.skill_id,
            "skill_doc": self.skill_doc,
            "run_log": self.run_log,
            "errors": self.errors,
            "assigned_roles": self.assigned_roles or {},
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
REQUIRED_CLOSE_SECTIONS = ("Execution Role", "Check Role", "Handoff")
ACCEPTED_CLOSE_STATUSES = {"done", "escalated"}
PHASE_REQUIRED_ROLES = {
    "execution": "executor",
    "check": "checker",
    "handoff": "handoff_owner",
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
    execution_mode: str,
    assigned_roles: dict[str, str],
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

## Runtime Role Assignment

- execution_mode: `{execution_mode}`
- executor: `{assigned_roles["executor"]}`
- checker: `{assigned_roles["checker"]}`
- handoff_owner: `{assigned_roles["handoff_owner"]}`
- separation_rule: `execution and check must be advanced by different runtime roles`
- executor_context: `{assigned_roles["executor_context"]}`
- checker_context: `{assigned_roles["checker_context"]}`

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


def _append_phase_event(text: str, *, phase: str, status: str, role: str | None, note: str | None) -> str:
    if "## Phase Events\n" not in text:
        text = text.rstrip() + "\n\n## Phase Events\n\n"
    note_text = note or ""
    event = f"- {date.today().isoformat()} `{phase}` -> `{status}`"
    if role:
        event += f" role=`{role}`"
    if note_text:
        event += f": {note_text}"
    return text.rstrip() + "\n" + event + "\n"


def _section_status(text: str, section: str) -> str | None:
    marker = f"## {section}\n"
    start = text.find(marker)
    if start == -1:
        return None

    next_section = text.find("\n## ", start + len(marker))
    body = text[start:] if next_section == -1 else text[start:next_section]
    prefix = "- status: `"
    status_start = body.find(prefix)
    if status_start == -1:
        return None
    status_start += len(prefix)
    status_end = body.find("`", status_start)
    if status_end == -1:
        return None
    return body[status_start:status_end]


def _set_phase_status(text: str, *, phase: str, status: str) -> str:
    label = PHASE_LABELS[phase]
    checkbox = "x" if status == "done" else "!"
    new_worklist = f"- [{checkbox}] {label}:"
    for marker in (" ", "x", "!"):
        text, changed = _replace_line(text, f"- [{marker}] {label}:", new_worklist)
        if changed:
            break

    section = PHASE_SECTIONS.get(phase)
    if section:
        new_status = f"## {section}\n\n- status: `{status}`"
        for existing in VALID_PHASE_STATUSES:
            old_status = f"## {section}\n\n- status: `{existing}`"
            text, changed = _replace_line(text, old_status, new_status)
            if changed:
                break
    return text


def _assigned_role(text: str, role_name: str) -> str | None:
    prefix = f"- {role_name}: `"
    start = text.find(prefix)
    if start == -1:
        return None
    start += len(prefix)
    end = text.find("`", start)
    if end == -1:
        return None
    return text[start:end]


def _phase_has_role_event(text: str, *, phase: str, role: str) -> bool:
    marker = f"`{phase}` -> `"
    role_marker = f"role=`{role}`"
    return any(marker in line and role_marker in line for line in text.splitlines())


def _validate_phase_role(text: str, *, phase: str, role: str | None) -> list[str]:
    required_role_name = PHASE_REQUIRED_ROLES.get(phase)
    if not required_role_name:
        return []
    if not role:
        return [f"{phase} phase requires --role {required_role_name}"]

    assigned = _assigned_role(text, required_role_name)
    if not assigned:
        return [f"runtime role assignment is missing {required_role_name}"]
    if role != assigned:
        return [f"{phase} phase requires role {assigned}; got {role}"]
    return []


def _assign_runtime_roles(*, skill_id: str, execution_mode: str) -> dict[str, str]:
    if execution_mode == "subagent_required":
        executor_context = "isolated_subagent_required"
        checker_context = "independent_checker_subagent_required"
    elif execution_mode == "subagent_preferred":
        executor_context = "subagent_preferred"
        checker_context = "independent_checker_subagent_preferred"
    else:
        executor_context = "current_context_allowed"
        checker_context = "independent_check_required"

    return {
        "executor": f"{skill_id}:executor",
        "checker": f"{skill_id}:checker",
        "handoff_owner": f"{skill_id}:handoff_owner",
        "executor_context": executor_context,
        "checker_context": checker_context,
    }


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
    role_errors = _validate_phase_role(text, phase=phase, role=args.role)
    if role_errors:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=role_errors)

    text = _set_phase_status(text, phase=phase, status=status)
    text = _append_phase_event(text, phase=phase, status=status, role=args.role, note=args.note)
    log_path.write_text(text, encoding="utf-8")

    return SkillRunResult(ok=True, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[])


def close_skill_run(args) -> SkillRunResult:
    log_path = Path(args.log).resolve()
    if not log_path.exists():
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=[f"log not found: {log_path}"])

    text = log_path.read_text(encoding="utf-8")
    if "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`" not in text:
        return SkillRunResult(
            ok=False,
            skill_id=None,
            skill_doc=None,
            run_log=str(log_path),
            errors=["skill run log is missing an opened Skill Load Gate"],
        )

    errors: list[str] = []
    statuses: dict[str, str | None] = {}
    for section in REQUIRED_CLOSE_SECTIONS:
        status = _section_status(text, section)
        statuses[section] = status
        if status not in ACCEPTED_CLOSE_STATUSES:
            errors.append(f"{section} must be done or escalated before closure; current={status or 'missing'}")

    executor = _assigned_role(text, "executor")
    checker = _assigned_role(text, "checker")
    handoff_owner = _assigned_role(text, "handoff_owner")
    if not executor or not checker or not handoff_owner:
        errors.append("runtime role assignment is incomplete")
    elif executor == checker:
        errors.append("executor and checker roles must be different")
    else:
        if not _phase_has_role_event(text, phase="execution", role=executor):
            errors.append(f"execution phase must be advanced by executor role {executor}")
        if not _phase_has_role_event(text, phase="check", role=checker):
            errors.append(f"check phase must be advanced by checker role {checker}")
        if not _phase_has_role_event(text, phase="handoff", role=handoff_owner):
            errors.append(f"handoff phase must be advanced by handoff_owner role {handoff_owner}")

    if errors:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=errors)

    close_status = "escalated" if "escalated" in statuses.values() else "done"
    text = _set_phase_status(text, phase="closure", status=close_status)
    text = _append_phase_event(text, phase="closure", status=close_status, role="closure_gate", note=args.note)
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
    execution_mode = str(parsed.get("execution_mode"))
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
    assigned_roles = _assign_runtime_roles(skill_id=skill_id, execution_mode=execution_mode)

    out_path = Path(args.out) if args.out else _default_log_path(root, skill_id)
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log = _render_log(
        skill_id=skill_id,
        meta_path=meta_path.relative_to(root),
        skill_doc=skill_doc_path.relative_to(root),
        execution_mode=execution_mode,
        assigned_roles=assigned_roles,
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
        assigned_roles=assigned_roles,
    )


def cmd_skill_run(args) -> int:
    result = run_skill(args)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print(f"  skill_id: {result.skill_id}")
        print(f"  skill_doc: {result.skill_doc}")
        for key, value in (result.assigned_roles or {}).items():
            print(f"  {key}: {value}")
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


def cmd_skill_close(args) -> int:
    result = close_skill_run(args)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print("  closure: accepted")
    else:
        print("fail: skill close")
        for error in result.errors:
            print(f"  error: {error}")
    return 0 if result.ok else 1
