from __future__ import annotations

import json
import re
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
    work_items: list[dict[str, str]] | None = None
    artifacts: list[dict[str, str]] | None = None
    concerns: list[dict[str, str]] | None = None
    closure_checks: dict[str, str] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "skill_id": self.skill_id,
            "skill_doc": self.skill_doc,
            "run_log": self.run_log,
            "errors": self.errors,
            "assigned_roles": self.assigned_roles or {},
            "work_items": self.work_items or [],
            "artifacts": self.artifacts or [],
            "concerns": self.concerns or [],
            "closure_checks": self.closure_checks or {},
        }


VALID_PHASES = {"startup", "planning", "execution", "check", "closure", "handoff"}
VALID_PHASE_STATUSES = {"pending", "in_progress", "done", "blocked", "unknown", "escalated"}
VALID_WORKITEM_STATUSES = {"pending", "in_progress", "done", "blocked", "unknown", "escalated"}
VALID_ARTIFACT_STATUSES = {"pending", "in_progress", "done", "blocked", "unknown", "escalated"}
VALID_ARTIFACT_KINDS = {"output", "evidence", "check", "judgment", "source", "handoff"}
VALID_CONCERN_KINDS = {"unknown", "risk", "judgment"}
VALID_CONCERN_STATUSES = {"open", "resolved", "escalated"}
VALID_JUDGMENT_TYPES = {"trivial", "non_trivial"}
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
WORKITEM_RE = re.compile(
    r"^- \[(?P<checkbox>[ x!])\] (?P<item_id>[A-Za-z0-9_.-]+) "
    r"status=`(?P<status>[^`]+)` role=`(?P<role>[^`]+)`: (?P<text>.*)$"
)
ARTIFACT_RE = re.compile(
    r"^- \[(?P<checkbox>[ x!])\] (?P<artifact_id>[A-Za-z0-9_.-]+) "
    r"kind=`(?P<kind>[^`]+)` status=`(?P<status>[^`]+)` "
    r"role=`(?P<role>[^`]+)` target=`(?P<target>[^`]+)` item=`(?P<item_id>[^`]+)`: (?P<note>.*)$"
)
CONCERN_RE = re.compile(
    r"^- \[(?P<checkbox>[ x!])\] (?P<concern_id>[A-Za-z0-9_.-]+) "
    r"kind=`(?P<kind>[^`]+)` status=`(?P<status>[^`]+)` "
    r"judgment=`(?P<judgment>[^`]+)` role=`(?P<role>[^`]+)` "
    r"target=`(?P<target>[^`]+)`: (?P<text>.*)$"
)


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

## Concrete Work Items

- status: `pending`
- rule: task-specific work items must be added with `fm skill workitem` and closed as `done` or `escalated`

## Runtime Artifacts

- status: `pending`
- rule: outputs, evidence, checks, judgments, sources, and handoff links must be added with `fm skill artifact`

## Execution Role

- status: `pending`
- responsibility: perform the Skill procedure inside the declared flow, capability, and guard boundary

## Check Role

- status: `pending`
- responsibility: independently check evidence, boundaries, output quality, unknowns, closure, and handoff readiness

## Unknowns And Risks

- status: `pending`
- rule: unknowns, missing evidence, risks, and unsupported assumptions must remain explicit and must be resolved, escalated, or linked before closure

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


def _section_body(text: str, section: str) -> tuple[str | None, int, int]:
    marker = f"## {section}\n"
    start = text.find(marker)
    if start == -1:
        return None, -1, -1
    next_section = text.find("\n## ", start + len(marker))
    end = len(text) if next_section == -1 else next_section
    return text[start:end], start, end


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


def _workitem_checkbox(status: str) -> str:
    if status == "done":
        return "x"
    if status == "pending":
        return " "
    return "!"


def _status_checkbox(status: str) -> str:
    if status == "done":
        return "x"
    if status == "pending":
        return " "
    return "!"


def _concern_checkbox(status: str) -> str:
    if status == "resolved":
        return "x"
    if status == "open":
        return " "
    return "!"


def _parse_work_items(text: str) -> list[dict[str, str]]:
    body, _, _ = _section_body(text, "Concrete Work Items")
    if body is None:
        return []

    items: list[dict[str, str]] = []
    for line in body.splitlines():
        match = WORKITEM_RE.match(line)
        if not match:
            continue
        items.append(
            {
                "item_id": match.group("item_id"),
                "status": match.group("status"),
                "role": match.group("role"),
                "text": match.group("text"),
            }
        )
    return items


def _render_workitem_line(*, item_id: str, status: str, role: str, text: str) -> str:
    return f"- [{_workitem_checkbox(status)}] {item_id} status=`{status}` role=`{role}`: {text}"


def _overall_workitem_status(items: list[dict[str, str]]) -> str:
    if not items:
        return "pending"
    if all(item["status"] in ACCEPTED_CLOSE_STATUSES for item in items):
        if any(item["status"] == "escalated" for item in items):
            return "escalated"
        return "done"
    if any(item["status"] in {"blocked", "unknown", "escalated"} for item in items):
        return "blocked"
    return "in_progress"


def _replace_concrete_work_items_section(text: str, items: list[dict[str, str]]) -> str:
    body, start, end = _section_body(text, "Concrete Work Items")
    if body is None:
        insert_at = text.find("\n## Execution Role")
        if insert_at == -1:
            insert_at = len(text)
        section = "\n\n## Concrete Work Items\n\n- status: `pending`\n- rule: task-specific work items must be added with `fm skill workitem` and closed as `done` or `escalated`\n"
        text = text[:insert_at] + section + text[insert_at:]
        body, start, end = _section_body(text, "Concrete Work Items")
        if body is None:
            return text

    status = _overall_workitem_status(items)
    lines = [
        "## Concrete Work Items",
        "",
        f"- status: `{status}`",
        "- rule: task-specific work items must be added with `fm skill workitem` and closed as `done` or `escalated`",
    ]
    lines.extend(_render_workitem_line(**item) for item in items)
    new_body = "\n".join(lines) + "\n"
    return text[:start] + new_body + text[end:]


def update_work_item(args) -> SkillRunResult:
    log_path = Path(args.log).resolve()
    if not log_path.exists():
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=[f"log not found: {log_path}"])

    item_id = str(args.item).strip()
    status = str(args.status).lower()
    role = str(args.role).strip()
    item_text = str(args.text or "").strip()
    if not item_id:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["missing --item"])
    if status not in VALID_WORKITEM_STATUSES:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[f"invalid work item status: {status}"])
    if not role:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["missing --role"])

    text = log_path.read_text(encoding="utf-8")
    if "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`" not in text:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["skill run log is missing an opened Skill Load Gate"])

    items = _parse_work_items(text)
    existing = next((item for item in items if item["item_id"] == item_id), None)
    if existing:
        existing["status"] = status
        existing["role"] = role
        if item_text:
            existing["text"] = item_text
    else:
        if not item_text:
            return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["new work item requires --text"])
        items.append({"item_id": item_id, "status": status, "role": role, "text": item_text})

    text = _replace_concrete_work_items_section(text, items)
    text = _append_phase_event(text, phase=f"workitem:{item_id}", status=status, role=role, note=item_text or None)
    log_path.write_text(text, encoding="utf-8")
    return SkillRunResult(ok=True, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[], work_items=items)


def _parse_artifacts(text: str) -> list[dict[str, str]]:
    body, _, _ = _section_body(text, "Runtime Artifacts")
    if body is None:
        return []

    artifacts: list[dict[str, str]] = []
    for line in body.splitlines():
        match = ARTIFACT_RE.match(line)
        if not match:
            continue
        artifacts.append(
            {
                "artifact_id": match.group("artifact_id"),
                "kind": match.group("kind"),
                "status": match.group("status"),
                "role": match.group("role"),
                "target": match.group("target"),
                "item_id": match.group("item_id"),
                "note": match.group("note"),
            }
        )
    return artifacts


def _render_artifact_line(
    *,
    artifact_id: str,
    kind: str,
    status: str,
    role: str,
    target: str,
    item_id: str,
    note: str,
) -> str:
    return (
        f"- [{_status_checkbox(status)}] {artifact_id} kind=`{kind}` status=`{status}` "
        f"role=`{role}` target=`{target}` item=`{item_id}`: {note}"
    )


def _overall_artifact_status(artifacts: list[dict[str, str]]) -> str:
    if not artifacts:
        return "pending"
    if all(artifact["status"] in ACCEPTED_CLOSE_STATUSES for artifact in artifacts):
        if any(artifact["status"] == "escalated" for artifact in artifacts):
            return "escalated"
        return "done"
    if any(artifact["status"] in {"blocked", "unknown", "escalated"} for artifact in artifacts):
        return "blocked"
    return "in_progress"


def _replace_runtime_artifacts_section(text: str, artifacts: list[dict[str, str]]) -> str:
    body, start, end = _section_body(text, "Runtime Artifacts")
    if body is None:
        insert_at = text.find("\n## Execution Role")
        if insert_at == -1:
            insert_at = len(text)
        section = "\n\n## Runtime Artifacts\n\n- status: `pending`\n- rule: outputs, evidence, checks, judgments, sources, and handoff links must be added with `fm skill artifact`\n"
        text = text[:insert_at] + section + text[insert_at:]
        body, start, end = _section_body(text, "Runtime Artifacts")
        if body is None:
            return text

    status = _overall_artifact_status(artifacts)
    lines = [
        "## Runtime Artifacts",
        "",
        f"- status: `{status}`",
        "- rule: outputs, evidence, checks, judgments, sources, and handoff links must be added with `fm skill artifact`",
    ]
    lines.extend(_render_artifact_line(**artifact) for artifact in artifacts)
    new_body = "\n".join(lines) + "\n"
    return text[:start] + new_body + text[end:]


def update_artifact(args) -> SkillRunResult:
    log_path = Path(args.log).resolve()
    if not log_path.exists():
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=[f"log not found: {log_path}"])

    artifact_id = str(args.artifact).strip()
    kind = str(args.kind).lower()
    status = str(args.status).lower()
    role = str(args.role).strip()
    target = str(args.target or "").strip()
    item_id = str(args.item or "").strip()
    note = str(args.note or "").strip()
    if not artifact_id:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["missing --artifact"])
    if kind not in VALID_ARTIFACT_KINDS:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[f"invalid artifact kind: {kind}"])
    if status not in VALID_ARTIFACT_STATUSES:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[f"invalid artifact status: {status}"])
    if not role:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["missing --role"])

    text = log_path.read_text(encoding="utf-8")
    if "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`" not in text:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["skill run log is missing an opened Skill Load Gate"])

    artifacts = _parse_artifacts(text)
    existing = next((artifact for artifact in artifacts if artifact["artifact_id"] == artifact_id), None)
    if existing:
        existing["kind"] = kind
        existing["status"] = status
        existing["role"] = role
        if target:
            existing["target"] = target
        if item_id:
            existing["item_id"] = item_id
        if note:
            existing["note"] = note
    else:
        if not target:
            return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["new artifact requires --target"])
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "kind": kind,
                "status": status,
                "role": role,
                "target": target,
                "item_id": item_id or "-",
                "note": note or "-",
            }
        )

    text = _replace_runtime_artifacts_section(text, artifacts)
    text = _append_phase_event(text, phase=f"artifact:{artifact_id}", status=status, role=role, note=note or target)
    log_path.write_text(text, encoding="utf-8")
    return SkillRunResult(ok=True, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[], artifacts=artifacts)


def _parse_concerns(text: str) -> list[dict[str, str]]:
    body, _, _ = _section_body(text, "Unknowns And Risks")
    if body is None:
        return []

    concerns: list[dict[str, str]] = []
    for line in body.splitlines():
        match = CONCERN_RE.match(line)
        if not match:
            continue
        concerns.append(
            {
                "concern_id": match.group("concern_id"),
                "kind": match.group("kind"),
                "status": match.group("status"),
                "judgment": match.group("judgment"),
                "role": match.group("role"),
                "target": match.group("target"),
                "text": match.group("text"),
            }
        )
    return concerns


def _render_concern_line(
    *,
    concern_id: str,
    kind: str,
    status: str,
    judgment: str,
    role: str,
    target: str,
    text: str,
) -> str:
    return (
        f"- [{_concern_checkbox(status)}] {concern_id} kind=`{kind}` status=`{status}` "
        f"judgment=`{judgment}` role=`{role}` target=`{target}`: {text}"
    )


def _overall_concern_status(concerns: list[dict[str, str]]) -> str:
    if not concerns:
        return "pending"
    if all(concern["status"] in {"resolved", "escalated"} for concern in concerns):
        if any(concern["status"] == "escalated" for concern in concerns):
            return "escalated"
        return "done"
    return "blocked"


def _replace_unknowns_and_risks_section(text: str, concerns: list[dict[str, str]]) -> str:
    body, start, end = _section_body(text, "Unknowns And Risks")
    if body is None:
        insert_at = text.find("\n## Closure Gate")
        if insert_at == -1:
            insert_at = len(text)
        section = "\n\n## Unknowns And Risks\n\n- status: `pending`\n- rule: unknowns, missing evidence, risks, and unsupported assumptions must remain explicit and must be resolved, escalated, or linked before closure\n"
        text = text[:insert_at] + section + text[insert_at:]
        body, start, end = _section_body(text, "Unknowns And Risks")
        if body is None:
            return text

    lines = [
        "## Unknowns And Risks",
        "",
        f"- status: `{_overall_concern_status(concerns)}`",
        "- rule: unknowns, missing evidence, risks, and unsupported assumptions must remain explicit and must be resolved, escalated, or linked before closure",
    ]
    lines.extend(_render_concern_line(**concern) for concern in concerns)
    new_body = "\n".join(lines) + "\n"
    return text[:start] + new_body + text[end:]


def update_concern(args) -> SkillRunResult:
    log_path = Path(args.log).resolve()
    if not log_path.exists():
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=[f"log not found: {log_path}"])

    concern_id = str(args.concern).strip()
    kind = str(args.kind).lower()
    status = str(args.status).lower()
    judgment = str(args.judgment or "trivial").lower()
    role = str(args.role).strip()
    target = str(args.target or "").strip()
    concern_text = str(args.text or "").strip()
    if not concern_id:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["missing --concern"])
    if kind not in VALID_CONCERN_KINDS:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[f"invalid concern kind: {kind}"])
    if status not in VALID_CONCERN_STATUSES:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[f"invalid concern status: {status}"])
    if judgment not in VALID_JUDGMENT_TYPES:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[f"invalid judgment type: {judgment}"])
    if kind != "judgment" and judgment == "non_trivial":
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["non_trivial judgment marker is only valid for kind=judgment"])
    if not role:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["missing --role"])

    text = log_path.read_text(encoding="utf-8")
    if "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`" not in text:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["skill run log is missing an opened Skill Load Gate"])

    concerns = _parse_concerns(text)
    existing = next((concern for concern in concerns if concern["concern_id"] == concern_id), None)
    if existing:
        existing["kind"] = kind
        existing["status"] = status
        existing["judgment"] = judgment
        existing["role"] = role
        if target:
            existing["target"] = target
        if concern_text:
            existing["text"] = concern_text
    else:
        if not concern_text:
            return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["new concern requires --text"])
        concerns.append(
            {
                "concern_id": concern_id,
                "kind": kind,
                "status": status,
                "judgment": judgment,
                "role": role,
                "target": target or "-",
                "text": concern_text,
            }
        )

    text = _replace_unknowns_and_risks_section(text, concerns)
    text = _append_phase_event(text, phase=f"concern:{concern_id}", status=status, role=role, note=concern_text or None)
    log_path.write_text(text, encoding="utf-8")
    return SkillRunResult(ok=True, skill_id=None, skill_doc=None, run_log=str(log_path), errors=[], concerns=concerns)


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


def _has_work_judgment_reference(concerns: list[dict[str, str]], artifacts: list[dict[str, str]]) -> bool:
    refs = [concern["target"] for concern in concerns]
    refs.extend(artifact["target"] for artifact in artifacts)
    return any("work/judgments/" in ref.replace("\\", "/") for ref in refs)


def _evaluate_closure_linkage(
    *, concerns: list[dict[str, str]], artifacts: list[dict[str, str]]
) -> tuple[list[str], dict[str, str]]:
    errors: list[str] = []

    open_unknowns = [
        concern["concern_id"]
        for concern in concerns
        if concern["kind"] == "unknown" and concern["status"] != "resolved"
    ]
    if open_unknowns:
        errors.append(f"unresolved unknowns block closure: {', '.join(open_unknowns)}")
        unknown_check = "failed"
    else:
        unknown_check = "passed"

    open_risks = [
        concern["concern_id"]
        for concern in concerns
        if concern["kind"] == "risk" and concern["status"] not in {"resolved", "escalated"}
    ]
    escalated_risks = [
        concern["concern_id"]
        for concern in concerns
        if concern["kind"] == "risk" and concern["status"] == "escalated"
    ]
    if open_risks:
        errors.append(f"unresolved risks block closure unless escalated: {', '.join(open_risks)}")
        risk_check = "failed"
    else:
        risk_check = "passed"

    open_judgments = [
        concern["concern_id"]
        for concern in concerns
        if concern["kind"] == "judgment" and concern["status"] not in {"resolved", "escalated"}
    ]
    non_trivial_judgments = [
        concern["concern_id"]
        for concern in concerns
        if concern["kind"] == "judgment" and concern["judgment"] == "non_trivial"
    ]
    has_judgment_artifact = any(
        artifact["kind"] == "judgment" and artifact["status"] in ACCEPTED_CLOSE_STATUSES
        for artifact in artifacts
    )
    has_work_judgment_ref = _has_work_judgment_reference(concerns, artifacts)
    if non_trivial_judgments and not (has_judgment_artifact or has_work_judgment_ref):
        errors.append(
            "non-trivial judgments require a judgment artifact or work/judgments/ reference before closure: "
            + ", ".join(non_trivial_judgments)
        )
        judgment_check = "failed"
    elif open_judgments:
        errors.append(f"unresolved judgments block closure: {', '.join(open_judgments)}")
        judgment_check = "failed"
    else:
        judgment_check = "passed"

    return errors, {
        "unknown": unknown_check,
        "risk": risk_check,
        "judgment": judgment_check,
        "open_unknowns": ",".join(open_unknowns) or "-",
        "open_risks": ",".join(open_risks) or "-",
        "escalated_risks": ",".join(escalated_risks) or "-",
        "open_judgments": ",".join(open_judgments) or "-",
        "non_trivial_judgments": ",".join(non_trivial_judgments) or "-",
        "judgment_reference": "present" if has_judgment_artifact or has_work_judgment_ref else "not_required",
    }


def _replace_closure_checks(text: str, checks: dict[str, str]) -> str:
    body, start, end = _section_body(text, "Closure Gate")
    if body is None:
        return text

    lines = body.rstrip().splitlines()
    filtered: list[str] = []
    skip = False
    for line in lines:
        if line == "### Closure Checks":
            skip = True
            continue
        if skip and line.startswith("### "):
            skip = False
        if skip:
            continue
        filtered.append(line)

    filtered.extend(
        [
            "",
            "### Closure Checks",
            "",
            f"- unknown: `{checks['unknown']}` open=`{checks['open_unknowns']}`",
            f"- risk: `{checks['risk']}` open=`{checks['open_risks']}` escalated=`{checks['escalated_risks']}`",
            f"- judgment: `{checks['judgment']}` open=`{checks['open_judgments']}` non_trivial=`{checks['non_trivial_judgments']}` reference=`{checks['judgment_reference']}`",
        ]
    )
    new_body = "\n".join(filtered) + "\n"
    return text[:start] + new_body + text[end:]


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

    work_items = _parse_work_items(text)
    if not work_items:
        errors.append("at least one concrete work item is required before closure")
    for item in work_items:
        if item["status"] not in ACCEPTED_CLOSE_STATUSES:
            errors.append(
                f"work item {item['item_id']} must be done or escalated before closure; current={item['status']}"
            )

    artifacts = _parse_artifacts(text)
    artifact_kinds = {artifact["kind"] for artifact in artifacts}
    if "output" not in artifact_kinds:
        errors.append("at least one output artifact is required before closure")
    if "evidence" not in artifact_kinds:
        errors.append("at least one evidence artifact is required before closure")
    for artifact in artifacts:
        if artifact["status"] not in ACCEPTED_CLOSE_STATUSES:
            errors.append(
                f"artifact {artifact['artifact_id']} must be done or escalated before closure; current={artifact['status']}"
            )

    concerns = _parse_concerns(text)
    linkage_errors, closure_checks = _evaluate_closure_linkage(concerns=concerns, artifacts=artifacts)
    errors.extend(linkage_errors)

    if errors:
        return SkillRunResult(
            ok=False,
            skill_id=None,
            skill_doc=None,
            run_log=str(log_path),
            errors=errors,
            concerns=concerns,
            closure_checks=closure_checks,
        )

    has_escalation = (
        "escalated" in statuses.values()
        or any(item["status"] == "escalated" for item in work_items)
        or any(artifact["status"] == "escalated" for artifact in artifacts)
        or any(concern["status"] == "escalated" for concern in concerns)
    )
    close_status = "escalated" if has_escalation else "done"
    text = _set_phase_status(text, phase="closure", status=close_status)
    text = _replace_closure_checks(text, closure_checks)
    text = _append_phase_event(text, phase="closure", status=close_status, role="closure_gate", note=args.note)
    log_path.write_text(text, encoding="utf-8")
    return SkillRunResult(
        ok=True,
        skill_id=None,
        skill_doc=None,
        run_log=str(log_path),
        errors=[],
        concerns=concerns,
        closure_checks=closure_checks,
    )


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


def cmd_skill_workitem(args) -> int:
    result = update_work_item(args)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print(f"  item: {args.item}")
        print(f"  status: {args.status}")
    else:
        print("fail: skill workitem")
        for error in result.errors:
            print(f"  error: {error}")
    return 0 if result.ok else 1


def cmd_skill_artifact(args) -> int:
    result = update_artifact(args)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print(f"  artifact: {args.artifact}")
        print(f"  kind: {args.kind}")
        print(f"  status: {args.status}")
    else:
        print("fail: skill artifact")
        for error in result.errors:
            print(f"  error: {error}")
    return 0 if result.ok else 1


def cmd_skill_concern(args) -> int:
    result = update_concern(args)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print(f"  concern: {args.concern}")
        print(f"  kind: {args.kind}")
        print(f"  status: {args.status}")
    else:
        print("fail: skill concern")
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
