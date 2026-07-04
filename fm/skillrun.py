from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from fm.skillmeta import (
    REQUIRED_OS_CONTRACT,
    VALID_CAPABILITY_LAYERING_POLICIES,
    VALID_WORKFLOW_PROTOCOL_POLICIES,
    TRIAL_DEFAULT_EXECUTION_MODE,
    TRIAL_DEFAULT_GUARD_POLICY,
    _parse_key_value_list,
    _parse_meta_lines,
    _resolve_maturity,
    resolve_os_contract,
    validate_skill_meta,
)


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
    handoff_sources: list[dict[str, str]] | None = None
    domain_knowledge: dict[str, object] | None = None

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
            "handoff_sources": self.handoff_sources or [],
            "domain_knowledge": self.domain_knowledge or {},
        }


VALID_PHASES = {"startup", "planning", "execution", "check", "quality", "closure", "handoff"}
VALID_PHASE_STATUSES = {"pending", "in_progress", "done", "blocked", "unknown", "escalated"}
VALID_WORKITEM_STATUSES = {"pending", "in_progress", "done", "blocked", "unknown", "escalated"}
VALID_ARTIFACT_STATUSES = {"pending", "in_progress", "done", "blocked", "unknown", "escalated"}
VALID_ARTIFACT_KINDS = {"output", "evidence", "check", "judgment", "source", "handoff"}
VALID_CONCERN_KINDS = {"unknown", "risk", "judgment"}
VALID_CONCERN_STATUSES = {"open", "resolved", "escalated"}
VALID_JUDGMENT_TYPES = {"trivial", "non_trivial"}
# model_tier values that make the quality gate mandatory at closure.
QUALITY_REQUIRED_TIERS = {"standard", "heavy"}
PHASE_LABELS = {
    "startup": "Startup",
    "planning": "Planning",
    "execution": "Execution",
    "check": "Check",
    "quality": "Quality",
    "closure": "Closure",
    "handoff": "Handoff",
}
PHASE_SECTIONS = {
    "execution": "Execution Role",
    "check": "Check Role",
    "quality": "Quality Gate",
    "closure": "Closure Gate",
    "handoff": "Handoff",
}
REQUIRED_CLOSE_SECTIONS = ("Execution Role", "Check Role", "Handoff")
ACCEPTED_CLOSE_STATUSES = {"done", "escalated"}
PHASE_REQUIRED_ROLES = {
    "execution": "executor",
    "check": "checker",
    "quality": "quality_reviewer",
    "handoff": "handoff_owner",
}
CLIENT_HIDDEN_DOMAIN_CATALOG_KEYS = {"path", "file", "content_path", "local_path", "source_path"}


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


def _parse_semicolon_fields(value: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_field in value.split(";"):
        field = raw_field.strip()
        if not field:
            continue
        if "=" in field:
            key, raw_value = field.split("=", 1)
            fields[key.strip()] = raw_value.strip().strip("`")
        else:
            fields[field] = "true"
    if "name" in fields and "slot" not in fields:
        fields["slot"] = fields["name"]
    return fields


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "required"}


def _parse_knowledge_input_requirements(parsed: dict[str, object]) -> list[dict[str, object]]:
    value = parsed.get("knowledge_inputs")
    if not isinstance(value, list):
        return []
    requirements: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, str):
            fields = _parse_semicolon_fields(item)
            name = fields.get("slot") or fields.get("name")
            if not name:
                continue
            requirements.append(
                {
                    "name": name,
                    "required": _parse_bool(fields.get("required")),
                    "accepts": [
                        part.strip()
                        for part in str(fields.get("accepts") or "").split(",")
                        if part.strip()
                    ],
                    "purpose": fields.get("purpose") or "",
                }
            )
    return requirements


def _load_domain_knowledge_catalog(path_value: str | None) -> tuple[list[dict[str, object]], list[str]]:
    if not path_value:
        return [], []
    path = Path(path_value)
    if not path.exists():
        return [], [f"domain knowledge catalog not found: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [f"domain knowledge catalog is not valid JSON: {exc}"]
    raw_entries = payload.get("entries") if isinstance(payload, dict) else payload
    if not isinstance(raw_entries, list):
        return [], ["domain knowledge catalog must be a JSON object with entries[] or a JSON array"]

    entries: list[dict[str, object]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for index, raw_entry in enumerate(raw_entries, start=1):
        if not isinstance(raw_entry, dict):
            errors.append(f"domain knowledge entry {index} must be an object")
            continue
        xid = str(raw_entry.get("xid") or "").strip()
        if not xid:
            errors.append(f"domain knowledge entry {index} is missing xid")
            continue
        if xid in seen:
            errors.append(f"duplicate domain knowledge xid in catalog: {xid}")
            continue
        hidden_keys = sorted(CLIENT_HIDDEN_DOMAIN_CATALOG_KEYS.intersection(raw_entry))
        if hidden_keys:
            errors.append(
                f"domain knowledge entry {xid} exposes local-path-like keys: {', '.join(hidden_keys)}"
            )
            continue
        seen.add(xid)
        entries.append(
            {
                "xid": xid,
                "kind": str(raw_entry.get("kind") or "").strip() or "unspecified",
                "title": str(raw_entry.get("title") or "").strip() or xid,
                "summary": str(raw_entry.get("summary") or "").strip(),
                "domain": str(raw_entry.get("domain") or "").strip(),
                "tags": raw_entry.get("tags") if isinstance(raw_entry.get("tags"), list) else [],
                "content_hash": str(raw_entry.get("content_hash") or "").strip(),
                "version": str(raw_entry.get("version") or "").strip(),
                "last_verified": str(raw_entry.get("last_verified") or "").strip(),
                "validity_conditions": str(raw_entry.get("validity_conditions") or "").strip(),
            }
        )
    return entries, errors


def _parse_selected_knowledge_inputs(values: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    selected: dict[str, list[str]] = {}
    errors: list[str] = []
    for value in values:
        if "=" not in value:
            errors.append(f"knowledge input must be name=XID[,XID]: {value}")
            continue
        name, raw_xids = value.split("=", 1)
        name = name.strip()
        xids = [part.strip() for part in raw_xids.split(",") if part.strip()]
        if not name:
            errors.append(f"knowledge input name is empty: {value}")
            continue
        if not xids:
            errors.append(f"knowledge input has no XIDs: {value}")
            continue
        selected.setdefault(name, []).extend(xids)
    return selected, errors


def _prepare_domain_knowledge_context(
    *,
    parsed_meta: dict[str, object],
    catalog_path: str | None,
    selected_values: list[str],
) -> tuple[dict[str, object], list[str]]:
    entries, catalog_errors = _load_domain_knowledge_catalog(catalog_path)
    selected, selected_errors = _parse_selected_knowledge_inputs(selected_values)
    errors = catalog_errors + selected_errors
    if selected_values and not catalog_path:
        errors.append("--knowledge-input requires --domain-knowledge-catalog")

    available_xids = {str(entry["xid"]) for entry in entries}
    for input_name, xids in selected.items():
        for xid in xids:
            if xid not in available_xids:
                errors.append(f"knowledge input {input_name} references XID not in catalog: {xid}")

    requirements = _parse_knowledge_input_requirements(parsed_meta)
    for requirement in requirements:
        name = str(requirement["name"])
        if requirement.get("required") and not selected.get(name):
            errors.append(f"required knowledge input is not selected: {name}")

    return {
        "available": entries,
        "selected": selected,
        "requirements": requirements,
    }, errors


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
    maturity: str,
    meta_path: Path,
    skill_doc: Path,
    execution_mode: str,
    guard_policy: str,
    capability_layering: str,
    workflow_protocol: str,
    capability: str,
    tuning: str,
    role_responsibilities: dict[str, str],
    capability_refs: list[str],
    assigned_roles: dict[str, str],
    task: str,
    os_contract: dict[str, str],
    handoff_sources: list[dict[str, str]],
    model_tier: str | None,
    domain_knowledge: dict[str, object],
) -> str:
    tier_label = model_tier or "unset"
    quality_policy = "required" if model_tier in QUALITY_REQUIRED_TIERS else "optional"
    contract_lines = "\n".join(f"- {key}: `{value}`" for key, value in os_contract.items())
    capability_ref_lines = "\n".join(
        f"- `{ref}`" for ref in capability_refs
    ) or "- none declared"
    protocol_role_responsibilities = {
        "quality_reviewer": "protocol-owned output-content acceptance when the quality gate is required",
        "handoff_owner": "protocol-owned explicit handoff progression",
    }
    role_responsibility_lines = "\n".join(
        f"- {role}: `{role_responsibilities.get(role) or protocol_role_responsibilities.get(role, 'not declared')}`"
        for role in ("executor", "quality_reviewer", "handoff_owner")
    )
    worklist_lines = "\n".join(
        f"- [ ] {name}: {description}" for name, description in WORKLIST_ROWS
    )
    handoff_source_lines = "\n".join(
        f"- source_log: `{source['source_log']}` skill_id=`{source['skill_id']}` closure=`{source['closure']}` handoff=`{source['handoff']}`"
        for source in handoff_sources
    ) or "- none"
    available_domain_entries = domain_knowledge.get("available", [])
    if isinstance(available_domain_entries, list) and available_domain_entries:
        available_domain_lines = "\n".join(
            "\n".join(
                [
                    f"- xid: `{entry.get('xid')}`",
                    f"  kind: `{entry.get('kind')}`",
                    f"  domain: `{entry.get('domain') or '-'}`",
                    f"  title: `{entry.get('title')}`",
                    f"  summary: {entry.get('summary') or '-'}",
                    f"  content_hash: `{entry.get('content_hash') or entry.get('version') or 'unknown'}`",
                    f"  last_verified: `{entry.get('last_verified') or 'unknown'}`",
                    f"  validity_conditions: {entry.get('validity_conditions') or 'unknown'}",
                ]
            )
            for entry in available_domain_entries
            if isinstance(entry, dict)
        )
    else:
        available_domain_lines = "- none supplied"
    selected_domain_inputs = domain_knowledge.get("selected", {})
    if isinstance(selected_domain_inputs, dict) and selected_domain_inputs:
        selected_domain_lines = "\n".join(
            "\n".join([f"- {name}:"] + [f"  - `{xid}`" for xid in xids])
            for name, xids in selected_domain_inputs.items()
            if isinstance(xids, list)
        )
    else:
        selected_domain_lines = "- none selected"
    domain_requirements = domain_knowledge.get("requirements", [])
    if isinstance(domain_requirements, list) and domain_requirements:
        requirement_lines = "\n".join(
            "\n".join(
                [
                    f"- name: `{requirement.get('name')}`",
                    f"  required: `{str(requirement.get('required')).lower()}`",
                    f"  accepts: `{', '.join(requirement.get('accepts') or []) if isinstance(requirement.get('accepts'), list) else '-'}`",
                    f"  purpose: `{requirement.get('purpose') or '-'}`",
                ]
            )
            for requirement in domain_requirements
            if isinstance(requirement, dict)
        )
    else:
        requirement_lines = "- none declared"
    return f"""# Skill Run Log

- date: `{date.today().isoformat()}`
- skill_id: `{skill_id}`
- maturity: `{maturity}`
- meta: `{meta_path.as_posix()}`
- skill_doc: `{skill_doc.as_posix()}`
- task: {task}

## Skill Load Gate

- status: `opened_by_fm_skill_run`
- rule: do not open or execute the Skill procedure until this runtime envelope exists

## Runtime Role Assignment

- guard_policy: `{guard_policy}`
- capability_layering: `{capability_layering}`
- workflow_protocol: `{workflow_protocol}`
- capability: `{capability}`
- tuning: `{tuning}`
- execution_mode: `{execution_mode}`
- model_tier: `{tier_label}`
- executor: `{assigned_roles["executor"]}`
- checker: `{assigned_roles["checker"]}`
- quality_reviewer: `{assigned_roles["quality_reviewer"]}`
- handoff_owner: `{assigned_roles["handoff_owner"]}`
- separation_rule: `execution, check, and quality must be advanced by different runtime roles from the executor`
- executor_context: `{assigned_roles["executor_context"]}`
- checker_context: `{assigned_roles["checker_context"]}`
- quality_reviewer_context: `{assigned_roles["quality_reviewer_context"]}`

## Role Responsibilities

{role_responsibility_lines}

## Workflow Protocol

- workflow_protocol: `{workflow_protocol}`
- checker: `protocol-owned deterministic workflow-progression verification via fm skill verify`
- rule: checker responsibility is assigned by the runtime workflow protocol, not repeated in Skill meta

## OS Contract

{contract_lines}

## Capability Layering

- capability_layering: `{capability_layering}`
- capability: `{capability}`
- tuning: `{tuning}`
- rule: execute the Skill inside the declared capability / tuning / responsibility boundary; capability definitions are control definitions, not evidence
- capability_refs:
{capability_ref_lines}

## Startup Inputs

- rule: when work starts from a prior handoff, the receiving startup must name the handoff source log and verify that its closure gate already passed
{handoff_source_lines}

## Domain Knowledge Inputs

- rule: available and selected brownfield domain knowledge is recorded by XID only; load full bodies through XID resolution, not local paths
- requirements:
{requirement_lines}

### Available Domain Knowledge

{available_domain_lines}

### Selected Knowledge Inputs

{selected_domain_lines}

### Used Knowledge Refs

- rule: record actually consulted domain knowledge XIDs as runtime artifacts or evidence before handoff
- none recorded yet

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
- responsibility: deterministically verify workflow-progression records (worklist, work items, artifact recording and linkage, concerns, role separation) with `fm skill verify`; output quality is the quality gate's responsibility, not this one

## Quality Gate

- status: `pending`
- model_tier: `{tier_label}`
- policy: `{quality_policy}`
- rule: declare acceptance check items as `check`-kind artifacts at planning; an independent quality reviewer sets each to `done` (pass) or `blocked` (fail) with `fm skill artifact`; domain reviews run as separate review Skills orchestrated by the main session and linked here. Required when model_tier is `standard` or `heavy`; optional otherwise

## Unknowns And Risks

- status: `pending`
- rule: unknowns, missing evidence, risks, and unsupported assumptions must remain explicit and must be resolved, escalated, or linked before closure

## Closure Gate

- status: `pending`
- rule: close only after execution, check, log, unknown/risk, and handoff rows are complete or explicitly escalated

## Handoff

- status: `pending`
- rule: record outputs, unresolved items, next owner, and human decision points

## Token Usage

- status: `pending`
- input: `-`
- output: `-`
- total: `-`
- rule: record tokens consumed by this skill run with `fm skill tokens` (informational; does not gate closure)
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


def _log_skill_id(text: str) -> str | None:
    prefix = "- skill_id: `"
    start = text.find(prefix)
    if start == -1:
        return None
    start += len(prefix)
    end = text.find("`", start)
    if end == -1:
        return None
    return text[start:end]


def _log_model_tier(text: str) -> str | None:
    prefix = "- model_tier: `"
    start = text.find(prefix)
    if start == -1:
        return None
    start += len(prefix)
    end = text.find("`", start)
    if end == -1:
        return None
    value = text[start:end]
    return None if value in {"", "unset"} else value


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


def _assign_runtime_roles(*, skill_id: str, execution_mode: str, model_tier: str | None) -> dict[str, str]:
    # execution_mode governs the executor side only. The check phase is
    # workflow-progression verification, which `fm skill verify` performs
    # deterministically; deterministic code is context-independent by
    # construction, so no checker subagent is assigned.
    if execution_mode == "subagent_required":
        executor_context = "isolated_subagent_required"
    elif execution_mode == "subagent_preferred":
        executor_context = "subagent_preferred"
    else:
        executor_context = "current_context_allowed"
    checker_context = "deterministic_fm_verification"

    # The quality phase is the quality axis: output acceptance and domain
    # review, exercised by an independent quality reviewer separate from the
    # executor. It runs in an independent subagent when the quality gate is
    # mandatory for this tier; otherwise it is optional.
    if model_tier in QUALITY_REQUIRED_TIERS:
        quality_reviewer_context = "independent_quality_subagent_required"
    else:
        quality_reviewer_context = "optional_for_this_tier"

    return {
        "executor": f"{skill_id}:executor",
        "checker": f"{skill_id}:checker",
        "quality_reviewer": f"{skill_id}:quality_reviewer",
        "handoff_owner": f"{skill_id}:handoff_owner",
        "executor_context": executor_context,
        "checker_context": checker_context,
        "quality_reviewer_context": quality_reviewer_context,
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


def _validate_handoff_sources(root: Path, source_logs: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    validated: list[dict[str, str]] = []
    errors: list[str] = []
    for raw_source in source_logs:
        source_path = Path(raw_source)
        if not source_path.is_absolute():
            source_path = root / source_path
        source_path = source_path.resolve()
        if not source_path.exists():
            errors.append(f"handoff source log not found: {source_path}")
            continue
        text = source_path.read_text(encoding="utf-8")
        if "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`" not in text:
            errors.append(f"handoff source log was not opened by fm skill run: {source_path}")
            continue
        closure_status = _section_status(text, "Closure Gate")
        if closure_status not in ACCEPTED_CLOSE_STATUSES:
            errors.append(
                f"handoff source log must have Closure Gate done or escalated before startup: {source_path} current={closure_status or 'missing'}"
            )
            continue
        handoff_status = _section_status(text, "Handoff")
        if handoff_status not in ACCEPTED_CLOSE_STATUSES:
            errors.append(
                f"handoff source log must have Handoff done or escalated before startup: {source_path} current={handoff_status or 'missing'}"
            )
            continue
        validated.append(
            {
                "source_log": source_path.relative_to(root).as_posix() if source_path.is_relative_to(root) else str(source_path),
                "skill_id": _log_skill_id(text) or "-",
                "closure": closure_status,
                "handoff": handoff_status,
            }
        )
    return validated, errors


def _progression_record_errors(
    text: str,
) -> tuple[list[str], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, str]]:
    """Deterministic work-item / artifact / concern checks shared by verify and close."""
    errors: list[str] = []

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

    return errors, work_items, artifacts, concerns, closure_checks


def verify_progression_run(args) -> SkillRunResult:
    """Deterministically verify workflow progression and advance the check phase.

    This replaces the LLM checker subagent for the check phase. The check is
    record-level only (worklist completion, work items, artifact recording and
    linkage, concern resolution, role separation); it does not open artifact
    targets, judge content, or assess output quality. Quality is a separate
    axis owned by review-oriented Skills.
    """
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
    executor = _assigned_role(text, "executor")
    checker = _assigned_role(text, "checker")
    if not executor or not checker:
        errors.append("runtime role assignment is incomplete")
    elif executor == checker:
        errors.append("executor and checker roles must be different")
    elif not _phase_has_role_event(text, phase="execution", role=executor):
        errors.append(f"execution phase must be advanced by executor role {executor}")

    record_errors, work_items, artifacts, concerns, closure_checks = _progression_record_errors(text)
    errors.extend(record_errors)

    new_status = "blocked" if errors else "done"
    role = checker or "fm:progression_checker"
    note = args.note or ("progression record verified" if not errors else "progression record incomplete")
    text = _set_phase_status(text, phase="check", status=new_status)
    text = _append_phase_event(text, phase="check", status=new_status, role=role, note=note)
    log_path.write_text(text, encoding="utf-8")

    return SkillRunResult(
        ok=not errors,
        skill_id=_log_skill_id(text),
        skill_doc=None,
        run_log=str(log_path),
        errors=errors,
        work_items=work_items,
        artifacts=artifacts,
        concerns=concerns,
        closure_checks=closure_checks,
    )


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

    record_errors, work_items, artifacts, concerns, closure_checks = _progression_record_errors(text)
    errors.extend(record_errors)

    # Tier-conditional quality gate. For standard/heavy tiers the quality axis
    # is mandatory: the quality phase must be advanced and at least one
    # acceptance `check`-kind artifact must exist. Light/untiered skills may
    # close without a quality gate. Artifact statuses themselves are already
    # enforced by _progression_record_errors.
    model_tier = _log_model_tier(text)
    quality_status = _section_status(text, "Quality Gate")
    statuses["Quality Gate"] = quality_status
    if model_tier in QUALITY_REQUIRED_TIERS:
        quality_reviewer = _assigned_role(text, "quality_reviewer")
        if quality_status not in ACCEPTED_CLOSE_STATUSES:
            errors.append(
                f"Quality Gate must be done or escalated before closure for model_tier {model_tier}; current={quality_status or 'missing'}"
            )
        if not any(artifact["kind"] == "check" for artifact in artifacts):
            errors.append(
                f"at least one acceptance check artifact is required before closure for model_tier {model_tier}"
            )
        if quality_reviewer and executor and quality_reviewer == executor:
            errors.append("executor and quality_reviewer roles must be different")
        if quality_reviewer and not _phase_has_role_event(text, phase="quality", role=quality_reviewer):
            errors.append(f"quality phase must be advanced by quality_reviewer role {quality_reviewer}")

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


def _parse_token_usage(text: str) -> dict[str, str] | None:
    body, _, _ = _section_body(text, "Token Usage")
    if body is None:
        return None

    def field(key: str) -> str | None:
        match = re.search(rf"^- {key}: `([^`]*)`", body, re.MULTILINE)
        return match.group(1) if match else None

    return {
        "status": field("status") or "",
        "input": field("input") or "",
        "output": field("output") or "",
        "total": field("total") or "",
    }


def _render_token_usage_section(
    *, input_value: str, output_value: str, total_value: str, note: str | None
) -> str:
    lines = [
        "## Token Usage",
        "",
        "- status: `recorded`",
        f"- input: `{input_value}`",
        f"- output: `{output_value}`",
        f"- total: `{total_value}`",
        "- rule: record tokens consumed by this skill run with `fm skill tokens` (informational; does not gate closure)",
    ]
    if note:
        lines.append(f"- note: {note}")
    return "\n".join(lines) + "\n"


def _replace_token_usage_section(text: str, new_body: str) -> str:
    body, start, end = _section_body(text, "Token Usage")
    if body is None:
        # Older logs created before this section existed: insert it just before
        # the Phase Events log, or append it at the end.
        block = "\n" + new_body.rstrip() + "\n"
        insert_at = text.find("\n## Phase Events")
        if insert_at == -1:
            return text.rstrip() + "\n\n" + new_body.rstrip() + "\n"
        return text[:insert_at] + "\n" + block + text[insert_at:]
    return text[:start] + new_body + text[end:]


def update_token_usage(args) -> SkillRunResult:
    log_path = Path(args.log).resolve()
    if not log_path.exists():
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=[f"log not found: {log_path}"])

    def _coerce(name: str, value) -> tuple[int | None, str | None]:
        if value is None:
            return None, None
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None, f"{name} must be an integer: {value}"
        if number < 0:
            return None, f"{name} must be >= 0: {value}"
        return number, None

    input_tokens, e_in = _coerce("input", args.input)
    output_tokens, e_out = _coerce("output", args.output)
    total_arg, e_total = _coerce("total", args.total)
    coerce_errors = [error for error in (e_in, e_out, e_total) if error]
    if coerce_errors:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=coerce_errors)
    if input_tokens is None and output_tokens is None and total_arg is None:
        return SkillRunResult(
            ok=False, skill_id=None, skill_doc=None, run_log=str(log_path),
            errors=["provide at least one of --input, --output, or --total"],
        )

    text = log_path.read_text(encoding="utf-8")
    if "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`" not in text:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=str(log_path), errors=["skill run log is missing an opened Skill Load Gate"])

    total_tokens = total_arg if total_arg is not None else (input_tokens or 0) + (output_tokens or 0)
    note = str(args.note or "").strip() or None
    new_body = _render_token_usage_section(
        input_value=str(input_tokens) if input_tokens is not None else "-",
        output_value=str(output_tokens) if output_tokens is not None else "-",
        total_value=str(total_tokens),
        note=note,
    )
    text = _replace_token_usage_section(text, new_body)
    text = _append_phase_event(
        text, phase="tokens", status="recorded", role=None,
        note=note or f"input={input_tokens if input_tokens is not None else '-'} output={output_tokens if output_tokens is not None else '-'} total={total_tokens}",
    )
    log_path.write_text(text, encoding="utf-8")
    return SkillRunResult(ok=True, skill_id=_log_skill_id(text), skill_doc=None, run_log=str(log_path), errors=[])


def run_skill(args) -> SkillRunResult:
    root = Path(args.root).resolve()
    meta_path = (root / args.meta).resolve()
    task, task_errors = _read_task(args)
    if task_errors:
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=task_errors)
    handoff_source_logs = [str(value).strip() for value in getattr(args, "handoff_source_log", []) if str(value).strip()]

    if not meta_path.exists():
        return SkillRunResult(ok=False, skill_id=None, skill_doc=None, run_log=None, errors=[f"meta not found: {meta_path}"])

    parsed = _parse_meta_lines(meta_path.read_text(encoding="utf-8"))
    domain_knowledge, domain_knowledge_errors = _prepare_domain_knowledge_context(
        parsed_meta=parsed,
        catalog_path=getattr(args, "domain_knowledge_catalog", None),
        selected_values=getattr(args, "knowledge_input", []),
    )
    if domain_knowledge_errors:
        return SkillRunResult(
            ok=False,
            skill_id=str(parsed.get("skill_id")) if parsed.get("skill_id") else None,
            skill_doc=None,
            run_log=None,
            errors=domain_knowledge_errors,
            domain_knowledge=domain_knowledge,
        )
    maturity, _ = _resolve_maturity(parsed)
    maturity = maturity or "stable"

    if maturity == "draft":
        return SkillRunResult(
            ok=False,
            skill_id=str(parsed.get("skill_id")) if parsed.get("skill_id") else None,
            skill_doc=None,
            run_log=None,
            errors=[
                "draft skills are not load-ready; promote the skill to trial with provisional runtime fields before fm skill run"
            ],
        )
    if maturity == "deprecated":
        return SkillRunResult(
            ok=False,
            skill_id=str(parsed.get("skill_id")) if parsed.get("skill_id") else None,
            skill_doc=None,
            run_log=None,
            errors=["deprecated skills cannot be opened with fm skill run"],
        )

    validation_level = "trial" if maturity == "trial" else "stable"
    validation = validate_skill_meta(meta_path, check_level=validation_level)
    if maturity == "trial":
        allowed_trial_errors = {"trial-or-higher skills must include at least one observation_refs entry"}
        blocking_errors = [error for error in validation.errors if error not in allowed_trial_errors]
    else:
        blocking_errors = list(validation.errors)

    if blocking_errors:
        return SkillRunResult(
            ok=False,
            skill_id=validation.skill_id,
            skill_doc=None,
            run_log=None,
            errors=blocking_errors,
        )

    skill_id = str(parsed.get("skill_id"))
    raw_execution_mode = parsed.get("execution_mode")
    execution_mode = str(raw_execution_mode) if raw_execution_mode else TRIAL_DEFAULT_EXECUTION_MODE
    if execution_mode not in {"local_default", "subagent_preferred", "subagent_required"}:
        return SkillRunResult(
            ok=False,
            skill_id=skill_id,
            skill_doc=None,
            run_log=None,
            errors=[f"invalid execution_mode for skill run: {execution_mode}"],
        )
    raw_guard_policy = parsed.get("guard_policy")
    guard_policy = str(raw_guard_policy) if raw_guard_policy else TRIAL_DEFAULT_GUARD_POLICY
    raw_capability_layering = parsed.get("capability_layering")
    capability_layering = str(raw_capability_layering) if raw_capability_layering else "required"
    if capability_layering not in VALID_CAPABILITY_LAYERING_POLICIES:
        return SkillRunResult(
            ok=False,
            skill_id=skill_id,
            skill_doc=None,
            run_log=None,
            errors=[f"invalid capability_layering for skill run: {capability_layering}"],
        )
    raw_workflow_protocol = parsed.get("workflow_protocol")
    workflow_protocol = str(raw_workflow_protocol) if raw_workflow_protocol else "required"
    if workflow_protocol not in VALID_WORKFLOW_PROTOCOL_POLICIES:
        return SkillRunResult(
            ok=False,
            skill_id=skill_id,
            skill_doc=None,
            run_log=None,
            errors=[f"invalid workflow_protocol for skill run: {workflow_protocol}"],
        )
    raw_capability_refs = parsed.get("capability_refs", [])
    capability_refs = [str(ref) for ref in raw_capability_refs] if isinstance(raw_capability_refs, list) else []
    capability = str(parsed.get("capability") or "not declared")
    tuning = str(parsed.get("tuning") or "not declared")
    role_responsibilities = _parse_key_value_list(parsed.get("role_responsibilities"))
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
    os_contract = resolve_os_contract(parsed.get("os_contract"))
    if maturity == "trial":
        merged_os_contract = dict(REQUIRED_OS_CONTRACT)
        merged_os_contract.update(os_contract)
        os_contract = merged_os_contract
    validated_handoff_sources, handoff_source_errors = _validate_handoff_sources(root, handoff_source_logs)
    if handoff_source_errors:
        return SkillRunResult(
            ok=False,
            skill_id=skill_id,
            skill_doc=None,
            run_log=None,
            errors=handoff_source_errors,
            handoff_sources=validated_handoff_sources,
        )
    raw_model_tier = parsed.get("model_tier")
    model_tier = str(raw_model_tier) if raw_model_tier else None
    assigned_roles = _assign_runtime_roles(
        skill_id=skill_id, execution_mode=execution_mode, model_tier=model_tier
    )

    out_path = Path(args.out) if args.out else _default_log_path(root, skill_id)
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log = _render_log(
        skill_id=skill_id,
        maturity=maturity,
        meta_path=meta_path.relative_to(root),
        skill_doc=skill_doc_path.relative_to(root),
        execution_mode=execution_mode,
        guard_policy=guard_policy,
        capability_layering=capability_layering,
        workflow_protocol=workflow_protocol,
        capability=capability,
        tuning=tuning,
        role_responsibilities=role_responsibilities,
        capability_refs=capability_refs,
        assigned_roles=assigned_roles,
        task=str(task),
        os_contract=os_contract,
        handoff_sources=validated_handoff_sources,
        model_tier=model_tier,
        domain_knowledge=domain_knowledge,
    )
    out_path.write_text(log, encoding="utf-8")

    return SkillRunResult(
        ok=True,
        skill_id=skill_id,
        skill_doc=str(skill_doc_path),
        run_log=str(out_path),
        errors=[],
        assigned_roles=assigned_roles,
        handoff_sources=validated_handoff_sources,
        domain_knowledge=domain_knowledge,
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


def cmd_skill_tokens(args) -> int:
    result = update_token_usage(args)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print("  token usage: recorded")
    else:
        print("fail: skill tokens")
        for error in result.errors:
            print(f"  error: {error}")
    return 0 if result.ok else 1


def cmd_skill_verify(args) -> int:
    result = verify_progression_run(args)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print("  check: progression verified")
    else:
        print("fail: skill verify")
        for error in result.errors:
            print(f"  error: {error}")
    return 0 if result.ok else 1
