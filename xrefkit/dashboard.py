from __future__ import annotations

import argparse
import html
import json
import re
import sys
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from xrefkit.boundary_analysis import analyze_dashboard_payload
from xrefkit.mcp.audit import AUDIT_SCHEMA
from xrefkit.skillrun import (
    ACCEPTED_CLOSE_STATUSES,
    PHASE_SECTIONS,
    QUALITY_REQUIRED_TIERS,
    _log_model_tier,
    _log_skill_id,
    _parse_artifacts,
    _parse_concerns,
    _parse_work_items,
    _section_status,
)


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
PHASES = ("execution", "check", "quality", "closure", "handoff")
EXPLICIT_XID_RE = re.compile(
    r"(?:<!--\s*xid\s*:\s*|#xid-|xid-|XID\s+)([A-Za-z0-9][A-Za-z0-9_-]{5,})",
    re.IGNORECASE,
)
AVAILABLE_XID_RE = re.compile(r"^- xid: `(?P<xid>[^`]+)`", re.MULTILINE)
BACKTICK_TOKEN_RE = re.compile(r"`(?P<token>[A-Za-z0-9][A-Za-z0-9_-]{5,})`")
OBSERVATION_EVENT_RE = re.compile(r"^- event: (?P<event>\{.*\})$", re.MULTILINE)
NON_XID_TOKEN_PREFIXES = ("WI-", "OUT-", "EVD-", "CHK-", "HND-", "UNK-", "RISK-", "JDG-")
FIELD_RE_TEMPLATE = r"^- {name}:\s*`?(?P<value>[^`\r\n]+)`?\s*$"

MISSING_INFORMATION_DEFINITIONS = {
    "run_id": ("Run correlation ID", "No run_id is recorded for cross-log correlation."),
    "mcp_session_id": ("MCP session ID", "No MCP session ID links this run to server-side XID queries."),
    "repository_fingerprint": (
        "Repository fingerprint",
        "No repository fingerprint identifies the Knowledge source generation.",
    ),
    "skill_routing_trace": (
        "Skill routing trace",
        "Skill candidates, ranking, and the selection reason are not recorded.",
    ),
    "loaded_xid_trace": (
        "Loaded XID trace",
        "XIDs actually injected into model context are not recorded separately from selected XIDs.",
    ),
    "knowledge_application_trace": (
        "Knowledge application trace",
        "No explicit XID link from a runtime artifact or concern shows where Knowledge was applied.",
    ),
    "knowledge_search_trace": (
        "Knowledge search trace",
        "Knowledge search queries, misses, and fallback decisions are not recorded.",
    ),
    "human_feedback": (
        "Human feedback",
        "No human correction, rejection, or acceptance feedback is linked to this run.",
    ),
    "outcome_feedback": (
        "Outcome feedback",
        "No downstream or operational outcome is linked to this run.",
    ),
    "token_usage": ("Token usage", "Measured input, output, and total token usage is not recorded."),
}


@dataclass(frozen=True)
class DashboardRun:
    path: str
    name: str
    mtime: str
    skill_id: str
    run_id: str | None
    flow_id: str
    root_run_id: str | None
    parent_run_id: str | None
    work_item_id: str | None
    node_id: str | None
    mcp_session_id: str | None
    repository_fingerprint: str | None
    status: str
    closure_status: str
    quality_required: bool
    quality_status: str
    sections: dict[str, str]
    counts: dict[str, int]
    blockers: list[str]
    artifacts: list[dict[str, str]]
    concerns: list[dict[str, str]]
    work_items: list[dict[str, str]]
    available_xids: list[str]
    selected_xids: list[str]
    used_xids: list[str]
    unused_xids: list[str]
    queried_xids: list[str]
    loaded_xids: list[str]
    queried_not_loaded_xids: list[str]
    loaded_not_applied_xids: list[str]
    observation_events: list[dict[str, object]]
    mcp_events: list[dict[str, object]]
    missing_information: list[dict[str, str]]
    intake: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "name": self.name,
            "mtime": self.mtime,
            "skill_id": self.skill_id,
            "run_id": self.run_id,
            "flow_id": self.flow_id,
            "root_run_id": self.root_run_id,
            "parent_run_id": self.parent_run_id,
            "work_item_id": self.work_item_id,
            "node_id": self.node_id,
            "mcp_session_id": self.mcp_session_id,
            "repository_fingerprint": self.repository_fingerprint,
            "status": self.status,
            "closure_status": self.closure_status,
            "quality_required": self.quality_required,
            "quality_status": self.quality_status,
            "sections": self.sections,
            "counts": self.counts,
            "blockers": self.blockers,
            "artifacts": self.artifacts,
            "concerns": self.concerns,
            "work_items": self.work_items,
            "available_xids": self.available_xids,
            "selected_xids": self.selected_xids,
            "used_xids": self.used_xids,
            "unused_xids": self.unused_xids,
            "queried_xids": self.queried_xids,
            "loaded_xids": self.loaded_xids,
            "queried_not_loaded_xids": self.queried_not_loaded_xids,
            "loaded_not_applied_xids": self.loaded_not_applied_xids,
            "observation_events": self.observation_events,
            "mcp_events": self.mcp_events,
            "missing_information": self.missing_information,
            "intake": self.intake,
        }


def _is_skill_run_log(text: str) -> bool:
    return text.lstrip().startswith(("# Skill Run Log", "# Workflow Run Log")) or (
        "- skill_id: `" in text and "## Skill Load Gate" in text and "## Closure Gate" in text
    )


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _section_status_or_pending(text: str, section: str) -> str:
    return _section_status(text, section) or "pending"


def _status_from_blockers(blockers: list[str], closure_status: str) -> str:
    if closure_status in ACCEPTED_CLOSE_STATUSES and not blockers:
        return "closed"
    if blockers:
        return "blocked"
    return "open"


def _section_text(text: str, heading: str) -> str:
    marker = f"### {heading}\n"
    start = text.find(marker)
    if start == -1:
        return ""
    next_h3 = text.find("\n### ", start + len(marker))
    next_h2 = text.find("\n## ", start + len(marker))
    candidates = [value for value in (next_h3, next_h2) if value != -1]
    end = min(candidates) if candidates else len(text)
    return text[start:end]


def _field_value(text: str, name: str) -> str | None:
    pattern = re.compile(FIELD_RE_TEMPLATE.format(name=re.escape(name)), re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        return None
    value = match.group("value").strip()
    return None if value in {"", "-", "pending", "unknown", "unset"} else value


def _observation_events(text: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for match in OBSERVATION_EVENT_RE.finditer(text):
        try:
            event = json.loads(match.group("event"))
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and isinstance(event.get("event"), str):
            events.append(event)
    return events


def _load_mcp_audit(path: Path) -> tuple[dict[str, list[dict[str, object]]], list[str]]:
    by_run: dict[str, list[dict[str, object]]] = {}
    errors: list[str] = []
    if not path.exists():
        return by_run, errors
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read audit log: {exc}")
        return by_run, errors
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(event, dict):
            errors.append(f"{path}:{line_number}: audit event must be an object")
            continue
        run_id = str(event.get("run_id") or "").strip()
        if run_id:
            by_run.setdefault(run_id, []).append(event)
    return by_run, errors


def _validated_mcp_events(
    events: list[dict[str, object]],
    *,
    run_id: str | None,
    skill_id: str,
    mcp_session_id: str | None,
    repository_fingerprint: str | None,
    audit_errors: list[str],
    source_path: Path,
) -> list[dict[str, object]]:
    if not events:
        return []
    if not run_id or not mcp_session_id or not repository_fingerprint:
        audit_errors.append(f"{source_path}: audit events ignored because the Skill Run correlation is incomplete")
        return []
    expected = {
        "schema": AUDIT_SCHEMA,
        "run_id": run_id,
        "skill_id": skill_id,
        "mcp_session_id": mcp_session_id,
        "repository_fingerprint": repository_fingerprint,
    }
    valid = [
        event
        for event in events
        if all(event.get(field) == value for field, value in expected.items())
        and isinstance(event.get("event_type"), str)
    ]
    if len(valid) != len(events):
        audit_errors.append(f"{source_path}: ignored MCP audit events with mismatched correlation identity")
    if not any(event.get("event_type") == "run.bound" for event in valid):
        audit_errors.append(f"{source_path}: ignored MCP audit events without a matching run.bound event")
        return []
    return valid


def _missing_information(
    text: str,
    *,
    run_id: str | None,
    mcp_session_id: str | None,
    repository_fingerprint: str | None,
    selected_xids: list[str],
    queried_xids: list[str],
    loaded_xids: list[str],
    applied_xids: list[str],
    observation_events: list[dict[str, object]],
    mcp_events: list[dict[str, object]],
) -> list[dict[str, str]]:
    missing_codes: list[str] = []
    if run_id is None:
        missing_codes.append("run_id")
    if mcp_session_id is None:
        missing_codes.append("mcp_session_id")
    if repository_fingerprint is None:
        missing_codes.append("repository_fingerprint")

    local_types = {str(item.get("event")) for item in observation_events}
    mcp_types = {str(item.get("event_type")) for item in mcp_events}
    if "skill.routed" not in local_types and "skill.ranked" not in mcp_types:
        missing_codes.append("skill_routing_trace")
    if (selected_xids or queried_xids) and not loaded_xids:
        missing_codes.append("loaded_xid_trace")
    if loaded_xids and not applied_xids:
        missing_codes.append("knowledge_application_trace")
    if "knowledge.search" not in local_types and "knowledge.search" not in mcp_types:
        missing_codes.append("knowledge_search_trace")
    if "human.feedback" not in local_types:
        missing_codes.append("human_feedback")
    if "outcome.feedback" not in local_types:
        missing_codes.append("outcome_feedback")

    token_section = _section_text(text, "Token Usage")
    if not token_section:
        token_section = text[text.find("## Token Usage") :] if "## Token Usage" in text else ""
    if _field_value(token_section, "total") is None:
        missing_codes.append("token_usage")

    return [
        {"code": code, "label": MISSING_INFORMATION_DEFINITIONS[code][0], "detail": MISSING_INFORMATION_DEFINITIONS[code][1]}
        for code in missing_codes
    ]


def _normalize_xid(value: str) -> str:
    return value.strip("`.,;:()[]")


def _looks_like_xid(value: str) -> bool:
    xid = _normalize_xid(value)
    if len(xid) < 6:
        return False
    if any(separator in xid for separator in ("/", "\\", ".", ":", " ")):
        return False
    upper = xid.upper()
    if upper.startswith(NON_XID_TOKEN_PREFIXES):
        return False
    return any(char.isdigit() for char in xid)


def _extract_explicit_xids(value: str) -> list[str]:
    xids: set[str] = set()
    for match in EXPLICIT_XID_RE.finditer(value):
        xid = _normalize_xid(match.group(1))
        if _looks_like_xid(xid):
            xids.add(xid)
    return sorted(xids)


def _extract_backtick_xids(value: str) -> list[str]:
    xids: set[str] = set()
    for match in BACKTICK_TOKEN_RE.finditer(value):
        xid = _normalize_xid(match.group("token"))
        if _looks_like_xid(xid):
            xids.add(xid)
    return sorted(xids)


def _domain_available_xids(text: str) -> list[str]:
    section = _section_text(text, "Available Domain Knowledge")
    return sorted({match.group("xid").strip() for match in AVAILABLE_XID_RE.finditer(section)})


def _domain_selected_xids(text: str) -> list[str]:
    section = _section_text(text, "Selected Knowledge Inputs")
    return sorted(set(_extract_explicit_xids(section)) | set(_extract_backtick_xids(section)))


def _runtime_used_xids(artifacts: list[dict[str, str]], concerns: list[dict[str, str]]) -> list[str]:
    xids: set[str] = set()
    for artifact in artifacts:
        target = artifact.get("target", "")
        note = artifact.get("note", "")
        if _looks_like_xid(target):
            xids.add(_normalize_xid(target))
        xids.update(_extract_explicit_xids(note))
    for concern in concerns:
        target = concern.get("target", "")
        text = concern.get("text", "")
        if _looks_like_xid(target):
            xids.add(_normalize_xid(target))
        xids.update(_extract_explicit_xids(text))
    return sorted(xids)


def _parse_one_run(
    path: Path,
    root: Path,
    mcp_events_by_run: dict[str, list[dict[str, object]]],
    audit_errors: list[str],
) -> DashboardRun | None:
    text = path.read_text(encoding="utf-8")
    if not _is_skill_run_log(text):
        return None

    artifacts = _parse_artifacts(text)
    concerns = _parse_concerns(text)
    work_items = _parse_work_items(text)
    model_tier = _log_model_tier(text)
    quality_required = model_tier in QUALITY_REQUIRED_TIERS
    closure_status = _section_status_or_pending(text, "Closure Gate")
    quality_status = _section_status_or_pending(text, "Quality Gate")
    sections = {
        phase: _section_status_or_pending(text, section)
        for phase, section in PHASE_SECTIONS.items()
        if phase in PHASES
    }

    blockers: list[str] = []
    if not (
        "## Skill Load Gate\n\n- status: `opened_by_xrefkit_skill_run`" in text
        or "## Run Load Gate\n\n- status: `opened_by_xrefkit_workflow_run`" in text
    ):
        blockers.append("missing Skill Load Gate")
    for phase in ("execution", "check", "handoff"):
        status = sections.get(phase, "pending")
        if status not in ACCEPTED_CLOSE_STATUSES:
            blockers.append(f"{phase} is {status}")
    if quality_required and quality_status not in ACCEPTED_CLOSE_STATUSES:
        blockers.append(f"quality gate is {quality_status}")
    if not work_items:
        blockers.append("no work items")
    for item in work_items:
        if item["status"] not in ACCEPTED_CLOSE_STATUSES:
            blockers.append(f"work item {item['item_id']} is {item['status']}")
    artifact_kinds = {artifact["kind"] for artifact in artifacts}
    if "output" not in artifact_kinds:
        blockers.append("no output artifact")
    if "evidence" not in artifact_kinds:
        blockers.append("no evidence artifact")
    if quality_required and "check" not in artifact_kinds:
        blockers.append("no quality check artifact")
    for artifact in artifacts:
        if artifact["status"] not in ACCEPTED_CLOSE_STATUSES:
            blockers.append(f"artifact {artifact['artifact_id']} is {artifact['status']}")
    for concern in concerns:
        if concern["status"] not in {"resolved", "escalated"}:
            blockers.append(f"{concern['kind']} {concern['concern_id']} is {concern['status']}")

    counts = {
        "work_items": len(work_items),
        "artifacts": len(artifacts),
        "outputs": sum(1 for artifact in artifacts if artifact["kind"] == "output"),
        "evidence": sum(1 for artifact in artifacts if artifact["kind"] == "evidence"),
        "checks": sum(1 for artifact in artifacts if artifact["kind"] == "check"),
        "handoffs": sum(1 for artifact in artifacts if artifact["kind"] == "handoff"),
        "unknowns": sum(1 for concern in concerns if concern["kind"] == "unknown"),
        "risks": sum(1 for concern in concerns if concern["kind"] == "risk"),
        "judgments": sum(1 for concern in concerns if concern["kind"] == "judgment"),
    }
    available_xids = _domain_available_xids(text)
    selected_xids = _domain_selected_xids(text)
    run_id = _field_value(text, "run_id")
    flow_id = _field_value(text, "flow_id") or run_id or path.name
    root_run_id = _field_value(text, "root_run_id")
    parent_run_id = _field_value(text, "parent_run_id")
    work_item_id = _field_value(text, "work_item_id")
    node_id = _field_value(text, "node_id")
    skill_id = _log_skill_id(text) or "unknown"
    observation_events = _observation_events(text)
    mcp_session_id = _field_value(text, "mcp_session_id")
    repository_fingerprint = _field_value(text, "repository_fingerprint")
    mcp_events = _validated_mcp_events(
        mcp_events_by_run.get(run_id, []) if run_id else [],
        run_id=run_id,
        skill_id=skill_id,
        mcp_session_id=mcp_session_id,
        repository_fingerprint=repository_fingerprint,
        audit_errors=audit_errors,
        source_path=path,
    )
    loaded_pairs = {
        (str(event["xid"]), str(event["content_hash"]))
        for event in observation_events
        if event.get("event") == "knowledge.loaded"
        and event.get("xid")
        and event.get("content_hash")
    }
    resolved_pairs = {
        (str(event["xid"]), str(event["content_hash"]))
        for event in mcp_events
        if event.get("event_type") == "xid.resolved"
        and event.get("xid")
        and event.get("content_hash")
    }
    applied_pairs = {
        (str(event["xid"]), str(event["content_hash"]))
        for event in observation_events
        if event.get("event") == "knowledge.applied"
        and event.get("xid")
        and event.get("content_hash")
        and (str(event["xid"]), str(event["content_hash"])) in loaded_pairs
    }
    queried_xids = sorted({xid for xid, _ in resolved_pairs})
    loaded_xids = sorted({xid for xid, _ in loaded_pairs})
    applied_xids = sorted({xid for xid, _ in applied_pairs})
    used_xids = applied_xids
    unused_xids = sorted(set(available_xids) - set(used_xids))
    missing_information = _missing_information(
        text,
        run_id=run_id,
        mcp_session_id=mcp_session_id,
        repository_fingerprint=repository_fingerprint,
        selected_xids=selected_xids,
        queried_xids=queried_xids,
        loaded_xids=loaded_xids,
        applied_xids=applied_xids,
        observation_events=observation_events,
        mcp_events=mcp_events,
    )
    intake = {
        name: _field_value(text, name) or "unknown"
        for name in ("purpose", "scope_in", "scope_out", "owner", "authority", "expected_evidence", "stop_conditions")
    }
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    return DashboardRun(
        path=_rel(path, root),
        name=path.name,
        mtime=mtime,
        skill_id=skill_id,
        run_id=run_id,
        flow_id=flow_id,
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        work_item_id=work_item_id,
        node_id=node_id,
        mcp_session_id=mcp_session_id,
        repository_fingerprint=repository_fingerprint,
        status=_status_from_blockers(blockers, closure_status),
        closure_status=closure_status,
        quality_required=quality_required,
        quality_status=quality_status,
        sections=sections,
        counts=counts,
        blockers=blockers,
        artifacts=artifacts,
        concerns=concerns,
        work_items=work_items,
        available_xids=available_xids,
        selected_xids=selected_xids,
        used_xids=used_xids,
        unused_xids=unused_xids,
        queried_xids=queried_xids,
        loaded_xids=loaded_xids,
        queried_not_loaded_xids=sorted({xid for xid, content_hash in resolved_pairs if (xid, content_hash) not in loaded_pairs}),
        loaded_not_applied_xids=sorted({xid for xid, content_hash in loaded_pairs if (xid, content_hash) not in applied_pairs}),
        observation_events=observation_events,
        mcp_events=mcp_events,
        missing_information=missing_information,
        intake=intake,
    )


def collect_runs(
    root: Path,
    sessions_dir: Path,
    mcp_events_by_run: dict[str, list[dict[str, object]]] | None = None,
    audit_errors: list[str] | None = None,
) -> list[DashboardRun]:
    root = root.resolve()
    sessions_dir = sessions_dir.resolve()
    if not sessions_dir.exists():
        return []
    runs: list[DashboardRun] = []
    for path in sorted(sessions_dir.rglob("*.md")):
        if not path.is_file():
            continue
        run = _parse_one_run(path, root, mcp_events_by_run or {}, audit_errors if audit_errors is not None else [])
        if run is not None:
            runs.append(run)
    runs.sort(key=lambda item: item.mtime, reverse=True)
    return runs


def _flow_status(runs: list[DashboardRun]) -> str:
    if any(run.status == "blocked" for run in runs):
        return "blocked"
    if any(run.status == "open" for run in runs):
        return "open"
    if runs and all(run.status == "closed" for run in runs):
        return "closed"
    return "unknown"


def _flow_state(
    runs: list[DashboardRun],
    work_items: list[dict[str, str]],
    reconcile_event: dict[str, object] | None,
    blockers: list[str],
) -> str:
    """Derive only from recorded lifecycle evidence; never infer hidden intent."""
    if blockers or (reconcile_event and reconcile_event.get("status") == "blocked"):
        return "blocked"
    events = [event for run in runs for event in run.observation_events]
    if any(event.get("event") == "flow.routed" and event.get("status") == "needs_clarification" for event in events):
        return "needs_clarification"
    if runs and all(run.status == "closed" for run in runs):
        return "closed"
    has_child = any(run.parent_run_id for run in runs) or any(
        event.get("event") == "child_run.started" for event in events
    )
    if has_child:
        child_runs = [run for run in runs if run.parent_run_id]
        if any(run.status != "closed" for run in child_runs):
            return "waiting_for_child"
        if reconcile_event is None:
            return "reconciling"
        if reconcile_event.get("status") == "pass":
            return "verifying"
    if any(event.get("event") == "flow.routed" for event in events):
        return "executing" if work_items else "routing"
    return "planning" if work_items else "intake"


def collect_flows(runs: list[DashboardRun]) -> list[dict[str, object]]:
    grouped: dict[str, list[DashboardRun]] = {}
    for run in runs:
        grouped.setdefault(run.flow_id, []).append(run)
    flows: list[dict[str, object]] = []
    for flow_id, flow_runs in grouped.items():
        flow_runs.sort(key=lambda item: item.mtime, reverse=True)
        root = next((run for run in flow_runs if run.run_id == run.root_run_id), flow_runs[-1])
        work_items = [item for run in flow_runs for item in run.work_items]
        blockers = sorted({blocker for run in flow_runs for blocker in run.blockers})
        reconcile_events = [
            event
            for run in flow_runs
            for event in run.observation_events
            if event.get("event") == "flow.reconciled"
        ]
        recoveries = [
            {
                **event,
                "flow_id": event.get("flow_id") or flow_id,
                "run_id": event.get("run_id") or run.run_id,
                "skill_id": run.skill_id,
                "run_path": run.path,
            }
            for run in flow_runs
            for event in run.observation_events
            if event.get("event") == "workflow.recovery"
        ]
        recoveries.sort(key=lambda item: str(item.get("timestamp") or ""))
        latest_reconcile = reconcile_events[-1] if reconcile_events else None
        flow_status = _flow_status(flow_runs)
        if isinstance(latest_reconcile, dict) and latest_reconcile.get("status") == "blocked":
            flow_status = "blocked"
            blockers.extend(str(item) for item in latest_reconcile.get("findings", []) if item)
        flow_state = _flow_state(flow_runs, work_items, latest_reconcile, blockers)
        flows.append(
            {
                "flow_id": flow_id,
                "root_run_id": root.run_id,
                "prompt": root.name,
                "intake": root.intake,
                "status": flow_status,
                "state": flow_state,
                "run_ids": [run.run_id for run in flow_runs if run.run_id],
                "runs": [run.to_dict() for run in flow_runs],
                "skills": sorted({run.skill_id for run in flow_runs}),
                "work_items": work_items,
                "recoveries": recoveries,
                "blockers": blockers,
                "reconcile_status": latest_reconcile.get("status") if isinstance(latest_reconcile, dict) else "not_run",
                "last_updated": flow_runs[0].mtime,
            }
        )
    flows.sort(key=lambda item: str(item["last_updated"]), reverse=True)
    return flows


def collect_recoveries(runs: list[DashboardRun]) -> list[dict[str, object]]:
    recoveries: list[dict[str, object]] = []
    for run in runs:
        for event in run.observation_events:
            if event.get("event") != "workflow.recovery":
                continue
            recoveries.append(
                {
                    **event,
                    "flow_id": event.get("flow_id") or run.flow_id,
                    "run_id": event.get("run_id") or run.run_id,
                    "skill_id": run.skill_id,
                    "run_path": run.path,
                }
            )
    recoveries.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    return recoveries


def _summary(runs: list[DashboardRun]) -> dict[str, int]:
    return {
        "runs": len(runs),
        "closed": sum(1 for run in runs if run.status == "closed"),
        "blocked": sum(1 for run in runs if run.status == "blocked"),
        "open": sum(1 for run in runs if run.status == "open"),
        "unknowns": sum(run.counts["unknowns"] for run in runs),
        "risks": sum(run.counts["risks"] for run in runs),
        "handoffs": sum(run.counts["handoffs"] for run in runs),
        "used_xids": len({xid for run in runs for xid in run.used_xids}),
        "unused_xids": len({xid for run in runs for xid in run.unused_xids}),
        "runs_with_missing_information": sum(1 for run in runs if run.missing_information),
        "missing_information": sum(len(run.missing_information) for run in runs),
    }


def _unused_xid_ranking(runs: list[DashboardRun]) -> list[dict[str, object]]:
    ranking: dict[str, dict[str, object]] = {}
    for run in runs:
        for xid in run.unused_xids:
            entry = ranking.setdefault(xid, {"xid": xid, "count": 0, "skills": set(), "runs": []})
            entry["count"] = int(entry["count"]) + 1
            assert isinstance(entry["skills"], set)
            assert isinstance(entry["runs"], list)
            entry["skills"].add(run.skill_id)
            entry["runs"].append(run.path)
    rows: list[dict[str, object]] = []
    for entry in ranking.values():
        rows.append(
            {
                "xid": entry["xid"],
                "count": entry["count"],
                "skills": sorted(entry["skills"]),
                "runs": sorted(entry["runs"]),
            }
        )
    rows.sort(key=lambda item: (-int(item["count"]), str(item["xid"])))
    return rows


def _missing_information_ranking(runs: list[DashboardRun]) -> list[dict[str, object]]:
    ranking: dict[str, dict[str, object]] = {}
    for run in runs:
        for item in run.missing_information:
            code = item["code"]
            entry = ranking.setdefault(
                code,
                {
                    "code": code,
                    "label": item["label"],
                    "detail": item["detail"],
                    "count": 0,
                    "skills": set(),
                    "runs": [],
                },
            )
            entry["count"] = int(entry["count"]) + 1
            assert isinstance(entry["skills"], set)
            assert isinstance(entry["runs"], list)
            entry["skills"].add(run.skill_id)
            entry["runs"].append(run.path)
    rows = [
        {
            **entry,
            "skills": sorted(entry["skills"]),
            "runs": sorted(entry["runs"]),
        }
        for entry in ranking.values()
    ]
    rows.sort(key=lambda item: (-int(item["count"]), str(item["code"])))
    return rows


def _decision_trace_payload(root: Path) -> dict[str, object]:
    try:
        from xrefkit.decision_trace import _graph, _impact_group, _read_events, _validate

        events = _read_events(root)
        groups: dict[str, int] = {}
        for event in events:
            group = _impact_group(event)
            groups[group] = groups.get(group, 0) + 1
        return {
            "events": events,
            "graph": _graph(root),
            "validation": _validate(root),
            "summary": {"events": len(events), "groups": dict(sorted(groups.items()))},
        }
    except (OSError, ValueError) as exc:
        return {
            "events": [],
            "graph": "flowchart TD\n    empty[\"No decision-trace events\"]",
            "validation": {"valid": False, "event_count": 0, "issues": [str(exc)]},
            "summary": {"events": 0, "groups": {}},
        }


def _decision_trace_rows(trace: object) -> str:
    if not isinstance(trace, dict):
        return "<tr><td colspan='6'>No decision-trace records found.</td></tr>"
    events = trace.get("events", [])
    if not isinstance(events, list) or not events:
        return "<tr><td colspan='6'>No decision-trace records found.</td></tr>"
    rows: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(str(event.get('event_id') or '-'))}</code></td>"
            f"<td>{html.escape(str(event.get('event_type') or '-'))}</td>"
            f"<td>{html.escape(str(event.get('status') or '-'))}</td>"
            f"<td>{html.escape(str(event.get('resolution') or '-'))}</td>"
            f"<td>{html.escape(str(event.get('branch') or '-'))}</td>"
            f"<td>{html.escape(str(event.get('reason') or '-'))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='6'>No decision-trace records found.</td></tr>"

def _flow_rows(flows: object) -> str:
    if not isinstance(flows, list) or not flows:
        return "<tr><td colspan='9'>No Prompt Flows found.</td></tr>"
    rows: list[str] = []
    for flow in flows:
        if not isinstance(flow, dict):
            continue
        skills = ", ".join(str(skill) for skill in flow.get("skills", []))
        runs = flow.get("runs", [])
        run_count = len(runs) if isinstance(runs, list) else 0
        work_items = flow.get("work_items", [])
        work_count = len(work_items) if isinstance(work_items, list) else 0
        blockers = flow.get("blockers", [])
        blocker_text = ", ".join(str(item) for item in blockers) if isinstance(blockers, list) else ""
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(str(flow.get('flow_id', '-')))}</code></td>"
            f"<td><span class='status status-{html.escape(str(flow.get('status', 'unknown')))}'>{html.escape(str(flow.get('status', 'unknown')))}</span></td>"
            f"<td>{html.escape(str(flow.get('state', 'intake')))}</td>"
            f"<td>{run_count}</td><td>{work_count}</td>"
            f"<td>{html.escape(skills or '-')}</td>"
            f"<td>{html.escape(str(flow.get('reconcile_status', 'not_run')))}</td>"
            f"<td>{html.escape(blocker_text or '-')}</td>"
            f"<td>{html.escape(str(flow.get('last_updated', '-')))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='9'>No Prompt Flows found.</td></tr>"


def _flow_tree(flows: object) -> str:
    if not isinstance(flows, list) or not flows:
        return "<section class='empty'>No Prompt Flow execution trees found.</section>"
    cards: list[str] = []
    for flow in flows:
        if not isinstance(flow, dict):
            continue
        runs = flow.get("runs", [])
        if not isinstance(runs, list):
            runs = []
        intake = flow.get("intake", {})
        if not isinstance(intake, dict):
            intake = {}
        run_rows = []
        for run in runs:
            if not isinstance(run, dict):
                continue
            parent = run.get("parent_run_id") or "root"
            run_rows.append(
                "<li>"
                f"<code>{html.escape(str(run.get('run_id') or '-'))}</code> "
                f"<strong>{html.escape(str(run.get('skill_id') or '-'))}</strong> "
                f"status={html.escape(str(run.get('status') or '-'))} "
                f"parent={html.escape(str(parent))} "
                f"work_item={html.escape(str(run.get('work_item_id') or '-'))} "
                f"<small>{html.escape(str(run.get('mtime') or '-'))}</small>"
                "</li>"
            )
        cards.append(
            f"<details><summary><code>{html.escape(str(flow.get('flow_id') or '-'))}</code> "
            f"status={html.escape(str(flow.get('status') or '-'))} "
            f"state={html.escape(str(flow.get('state') or 'intake'))}</summary>"
            f"<ul>{''.join(run_rows) or '<li>No runs.</li>'}</ul></details>"
        )
    return "\n".join(cards) or "<section class='empty'>No Prompt Flow execution trees found.</section>"


def _flow_details(flows: object) -> str:
    if not isinstance(flows, list) or not flows:
        return "<section class='empty'>No Prompt Flow details found.</section>"
    cards: list[str] = []
    for flow in flows:
        if not isinstance(flow, dict):
            continue
        items = flow.get("work_items", [])
        if not isinstance(items, list):
            items = []
        runs = flow.get("runs", [])
        if not isinstance(runs, list):
            runs = []
        intake = flow.get("intake", {})
        if not isinstance(intake, dict):
            intake = {}
        rows: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            rows.append(
                "<tr>"
                f"<td><code>{html.escape(str(item.get('item_id') or '-'))}</code></td>"
                f"<td>{html.escape(str(item.get('text') or '-'))}</td>"
                f"<td>{html.escape(str(item.get('status') or '-'))}</td>"
                f"<td>{html.escape(str(item.get('criterion') or item.get('reason') or '-'))}</td>"
                "</tr>"
            )
        run_rows: list[str] = []
        activity_items: list[str] = []
        record_items: list[str] = []
        for run in runs:
            if not isinstance(run, dict):
                continue
            run_id = str(run.get("run_id") or "-")
            artifacts = run.get("artifacts", [])
            concerns = run.get("concerns", [])
            counts = run.get("counts", {})
            run_rows.append(
                "<tr>"
                f"<td><code>{html.escape(run_id)}</code></td>"
                f"<td>{html.escape(str(run.get('skill_id') or '-'))}</td>"
                f"<td>{html.escape(str(run.get('status') or '-'))}</td>"
                f"<td>{html.escape(str(run.get('parent_run_id') or 'root'))}</td>"
                f"<td>{html.escape(str(run.get('work_item_id') or '-'))}</td>"
                f"<td>{html.escape(str(run.get('node_id') or '-'))}</td>"
                f"<td>{html.escape(str(counts.get('outputs', 0) if isinstance(counts, dict) else 0))}/"
                f"{html.escape(str(counts.get('evidence', 0) if isinstance(counts, dict) else 0))}/"
                f"{html.escape(str(counts.get('checks', 0) if isinstance(counts, dict) else 0))}</td>"
                f"<td>{html.escape(str(counts.get('unknowns', 0) if isinstance(counts, dict) else 0))}/"
                f"{html.escape(str(counts.get('risks', 0) if isinstance(counts, dict) else 0))}/"
                f"{html.escape(str(counts.get('judgments', 0) if isinstance(counts, dict) else 0))}</td>"
                "</tr>"
            )
            if isinstance(artifacts, list):
                for artifact in artifacts:
                    if isinstance(artifact, dict):
                        record_items.append(
                            f"<li><strong>{html.escape(str(artifact.get('kind') or '-'))}</strong> "
                            f"{html.escape(str(artifact.get('artifact_id') or '-'))}: "
                            f"{html.escape(str(artifact.get('status') or '-'))} — "
                            f"{html.escape(str(artifact.get('target') or artifact.get('note') or '-'))}</li>"
                        )
            if isinstance(concerns, list):
                for concern in concerns:
                    if isinstance(concern, dict):
                        record_items.append(
                            f"<li><strong>{html.escape(str(concern.get('kind') or '-'))}</strong> "
                            f"{html.escape(str(concern.get('concern_id') or '-'))}: "
                            f"{html.escape(str(concern.get('status') or '-'))} — "
                            f"{html.escape(str(concern.get('note') or concern.get('reason') or '-'))}</li>"
                        )
            events = run.get("observation_events", [])
            if isinstance(events, list):
                for event in events:
                    if not isinstance(event, dict):
                        continue
                    event_name = str(event.get("event") or "-")
                    details = event.get("selected_skill") or event.get("recovery_id") or event.get("status") or ""
                    activity_items.append(
                        f"<li><code>{html.escape(run_id)}</code> "
                        f"<strong>{html.escape(event_name)}</strong> "
                        f"{html.escape(str(details))}</li>"
                    )
        blockers = flow.get("blockers", [])
        blocker_text = "; ".join(str(item) for item in blockers) if isinstance(blockers, list) else ""
        recoveries = flow.get("recoveries", [])
        if not isinstance(recoveries, list):
            recoveries = []
        recovery_text = "; ".join(
            f"{item.get('recovery_id') or '-'}:{item.get('status') or '-'}"
            for item in recoveries
            if isinstance(item, dict)
        )
        cards.append(
            "<details class='flow-detail'>"
            f"<summary><code>{html.escape(str(flow.get('flow_id') or '-'))}</code> "
            f"prompt={html.escape(str(flow.get('prompt') or '-'))} "
            f"state={html.escape(str(flow.get('state') or 'intake'))} "
            f"reconcile={html.escape(str(flow.get('reconcile_status') or 'not_run'))}</summary>"
            f"<p>root_run_id: <code>{html.escape(str(flow.get('root_run_id') or '-'))}</code></p>"
            "<h4>Minimum intake</h4>"
            "<table class='table'><thead><tr><th>Field</th><th>Recorded value</th></tr></thead><tbody>"
            + "".join(
                f"<tr><td>{html.escape(str(name))}</td><td>{html.escape(str(intake.get(name) or 'unknown'))}</td></tr>"
                for name in ("purpose", "scope_in", "scope_out", "owner", "authority", "expected_evidence", "stop_conditions")
            )
            + "</tbody></table>"
            "<table class='table'><thead><tr><th>Work Item</th><th>Task</th><th>Status</th><th>Criterion / Reason</th></tr></thead>"
            f"<tbody>{''.join(rows) or '<tr><td colspan=\"4\">No Work Items.</td></tr>'}</tbody></table>"
            "<h4>Execution records</h4>"
            "<table class='table'><thead><tr><th>Run</th><th>Skill</th><th>Status</th><th>Parent</th><th>Work Item</th><th>Node</th><th>Output / Evidence / Checks</th><th>Unknown / Risk / Judgment</th></tr></thead>"
            f"<tbody>{''.join(run_rows) or '<tr><td colspan=\"8\">No execution records.</td></tr>'}</tbody></table>"
            "<h4>Activity</h4>"
            f"<ul>{''.join(activity_items) or '<li>No activity events.</li>'}</ul>"
            "<h4>Evidence and concerns</h4>"
            f"<ul>{''.join(record_items) or '<li>No output, evidence, check, unknown, risk, or judgment records.</li>'}</ul>"
            f"<p><strong>Blockers:</strong> {html.escape(blocker_text or '-')}</p>"
            f"<p><strong>Recovery:</strong> {html.escape(recovery_text or '-')}</p>"
            "</details>"
        )
    return "\n".join(cards) or "<section class='empty'>No Prompt Flow details found.</section>"


def _recovery_rows(recoveries: object) -> str:
    if not isinstance(recoveries, list) or not recoveries:
        return "<tr><td colspan='14'>No Recovery Trace records found.</td></tr>"
    rows: list[str] = []
    for recovery in recoveries:
        if not isinstance(recovery, dict):
            continue
        status = str(recovery.get("status") or "unknown")
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(str(recovery.get('recovery_id') or '-'))}</code></td>"
            f"<td><span class='status status-{html.escape(status)}'>{html.escape(status)}</span></td>"
            f"<td><code>{html.escape(str(recovery.get('flow_id') or '-'))}</code></td>"
            f"<td><code>{html.escape(str(recovery.get('run_id') or '-'))}</code></td>"
            f"<td>{html.escape(str(recovery.get('resume_location') or '-'))}</td>"
            f"<td>{html.escape(str(recovery.get('reason') or '-'))}</td>"
            f"<td>{html.escape(str(recovery.get('next_action') or '-'))}</td>"
            f"<td>{html.escape(str(recovery.get('executable_action') or '-'))}</td>"
            f"<td>{html.escape(str(recovery.get('owner') or 'unknown'))}</td>"
            f"<td>{html.escape(str(recovery.get('verification_method') or 'unknown'))}</td>"
            f"<td>{html.escape(str(recovery.get('maximum_attempts') or 'unknown'))}</td>"
            f"<td>{html.escape('; '.join(str(item) for item in recovery.get('stop_conditions', [])) if isinstance(recovery.get('stop_conditions'), list) else str(recovery.get('stop_conditions') or 'unknown'))}</td>"
            f"<td>{html.escape(str(recovery.get('reviewer') or '-'))}</td>"
            f"<td>{html.escape(str(recovery.get('run_path') or '-'))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='14'>No Recovery Trace records found.</td></tr>"


def build_payload(
    root: Path,
    sessions_dir: Path,
    mcp_audit_log: Path | None = None,
) -> dict[str, object]:
    audit_path = (mcp_audit_log or (root / "work" / "mcp" / "xid_audit.jsonl")).resolve()
    mcp_events_by_run, audit_errors = _load_mcp_audit(audit_path)
    runs = collect_runs(root, sessions_dir, mcp_events_by_run, audit_errors)
    flows = collect_flows(runs)
    recoveries = collect_recoveries(runs)
    decision_trace = _decision_trace_payload(root)
    summary = _summary(runs)
    summary["flows"] = len(flows)
    summary["recoveries"] = len(recoveries)
    payload: dict[str, object] = {
        "root": str(root.resolve()),
        "sessions_dir": str(sessions_dir.resolve()),
        "mcp_audit_log": str(audit_path),
        "audit_errors": audit_errors,
        "summary": summary,
        "unused_xid_ranking": _unused_xid_ranking(runs),
        "missing_information_ranking": _missing_information_ranking(runs),
        "runs": [run.to_dict() for run in runs],
        "flows": flows,
        "recoveries": recoveries,
        "decision_trace": decision_trace,
    }
    payload["boundary_analysis"] = analyze_dashboard_payload(
        payload,
        source_ref="dashboard://current",
        min_samples=2,
        max_candidates=20,
    )
    return payload


def _json_response(handler: BaseHTTPRequestHandler, payload: object, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _html_page(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    runs = payload["runs"]
    flows = payload.get("flows", [])
    decision_trace = payload.get("decision_trace", {})
    assert isinstance(summary, dict)
    assert isinstance(runs, list)
    assert isinstance(decision_trace, dict)
    boundary_analysis = payload.get("boundary_analysis")
    if not isinstance(boundary_analysis, dict):
        boundary_analysis = {}
    analysis_summary = boundary_analysis.get("summary")
    if not isinstance(analysis_summary, dict):
        analysis_summary = {}
    analysis_correlation = boundary_analysis.get("correlation")
    if not isinstance(analysis_correlation, dict):
        analysis_correlation = {}
    analysis_proposals = boundary_analysis.get("proposals")
    if not isinstance(analysis_proposals, list):
        analysis_proposals = []
    cards = "".join(
        f"<div class='metric'><span>{html.escape(str(label))}</span><strong>{value}</strong></div>"
        for label, value in [
            ("Skill runs", summary["runs"]),
            ("Prompt Flows", summary.get("flows", 0)),
            ("Recoveries", summary.get("recoveries", 0)),
            ("Closed", summary["closed"]),
            ("Blocked", summary["blocked"]),
            ("Open", summary["open"]),
            ("Unknowns", summary["unknowns"]),
            ("Risks", summary["risks"]),
            ("Handoffs", summary["handoffs"]),
            ("Used XIDs", summary["used_xids"]),
            ("Unused XIDs", summary["unused_xids"]),
            ("Runs missing info", summary["runs_with_missing_information"]),
            ("Missing info items", summary["missing_information"]),
        ]
    )
    overview_rows = "\n".join(_overview_row(run) for run in runs)
    flow_rows = _flow_rows(flows)
    flow_tree = _flow_tree(flows)
    flow_details = _flow_details(flows)
    recovery_rows = _recovery_rows(payload.get("recoveries", []))
    attention_rows = "\n".join(_attention_card(run) for run in runs if isinstance(run, dict) and run.get("status") == "blocked")
    closure_rows = "\n".join(_closure_card(run) for run in runs)
    evidence_rows = "\n".join(_evidence_card(run) for run in runs if _has_observed_records(run))
    handoff_rows = "\n".join(_handoff_card(run) for run in runs if _has_handoff_records(run))
    xid_rows = "\n".join(_xid_usage_card(run) for run in runs if _has_xid_records(run))
    unused_xid_rows = _unused_xid_ranking_table(payload.get("unused_xid_ranking", []))
    missing_information_rows = _missing_information_ranking_table(payload.get("missing_information_ranking", []))
    decision_trace_summary = decision_trace.get("summary", {})
    if not isinstance(decision_trace_summary, dict):
        decision_trace_summary = {}
    decision_trace_rows = _decision_trace_rows(decision_trace)
    decision_trace_groups = decision_trace_summary.get("groups", {})
    if not isinstance(decision_trace_groups, dict):
        decision_trace_groups = {}
    decision_trace_group_rows = "".join(
        f"<tr><td>{html.escape(str(group))}</td><td>{html.escape(str(count))}</td></tr>"
        for group, count in sorted(decision_trace_groups.items())
    ) or "<tr><td colspan='2'>No impact groups found.</td></tr>"
    decision_trace_validation = decision_trace.get("validation", {})
    if not isinstance(decision_trace_validation, dict):
        decision_trace_validation = {}
    decision_trace_issues = decision_trace_validation.get("issues", [])
    if not isinstance(decision_trace_issues, list):
        decision_trace_issues = []
    decision_trace_issue_html = "" if not decision_trace_issues else "<ul>" + "".join(
        f"<li>{html.escape(str(issue))}</li>" for issue in decision_trace_issues[:10]
    ) + "</ul>"
    missing_information_cards = "\n".join(
        _missing_information_card(run)
        for run in runs
        if isinstance(run, dict) and run.get("missing_information")
    )
    analysis_cards = "".join(
        f"<div class='metric'><span>{html.escape(str(label))}</span><strong>{html.escape(str(value))}</strong></div>"
        for label, value in [
            ("Proposals", analysis_summary.get("proposals", len(analysis_proposals))),
            ("Samples", boundary_analysis.get("sample_count", 0)),
            ("Exact correlation", analysis_correlation.get("exact", 0)),
            ("Unknown correlation", analysis_correlation.get("unknown", 0)),
        ]
    )
    analysis_correlation_pills = "".join(
        f"<span class='pill'>{html.escape(str(level))}: {html.escape(str(analysis_correlation.get(level, 0)))}</span>"
        for level in ("exact", "bounded", "heuristic", "unknown")
    )
    if analysis_proposals:
        analysis_proposal_rows = "\n".join(
            _analysis_proposal_card(proposal)
            for proposal in analysis_proposals
            if isinstance(proposal, dict)
        )
    else:
        analysis_proposal_rows = (
            "<section class='empty'>No boundary proposals reached the configured minimum sample support. "
            "This is not proof that no issue exists.</section>"
        )
    if not analysis_proposal_rows:
        analysis_proposal_rows = "<section class='empty'>No usable boundary proposals were found.</section>"
    empty = "<section class='empty'>No Skill run logs found under the configured sessions directory.</section>"
    if not runs:
        overview_rows = empty
    if not attention_rows:
        attention_rows = "<section class='empty'>No blocked Skill runs.</section>"
    if not evidence_rows:
        evidence_rows = "<section class='empty'>No output, evidence, or check artifacts recorded.</section>"
    if not handoff_rows:
        handoff_rows = "<section class='empty'>No handoff, unknown, risk, or judgment records.</section>"
    if not xid_rows:
        xid_rows = "<section class='empty'>No XID usage records found in Skill run logs.</section>"
    if not missing_information_cards:
        missing_information_cards = "<section class='empty'>No missing tuning information detected.</section>"
    audit_errors = payload.get("audit_errors") if isinstance(payload.get("audit_errors"), list) else []
    audit_warning = ""
    if audit_errors:
        audit_items = "".join(f"<li>{html.escape(str(item))}</li>" for item in audit_errors[:5])
        audit_warning = (
            "<section class='audit-warning'><strong>MCP audit log contains unreadable records.</strong>"
            f"<ul>{audit_items}</ul></section>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Skill Run Observation Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fb;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #5b6577;
      --line: #d6deea;
      --blue: #2563eb;
      --green: #15803d;
      --amber: #b45309;
      --red: #be123c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "BIZ UDPGothic", "Meiryo", "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    header {{
      padding: 28px 32px 18px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 2;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    .sub {{ margin: 0; color: var(--muted); font-size: 14px; }}
    main {{ padding: 24px 32px 48px; max-width: 1400px; margin: 0 auto; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 20px; }}
    .tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin: 0 0 20px;
    }}
    .tab {{
      appearance: none;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      color: var(--muted);
      cursor: pointer;
      font: inherit;
      font-size: 14px;
      padding: 9px 12px;
    }}
    .tab.active {{
      border-color: var(--blue);
      color: var(--blue);
      background: #eaf1fb;
      font-weight: 700;
    }}
    .controls {{
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto auto;
      gap: 12px;
      align-items: center;
      margin: 0 0 18px;
    }}
    .search {{
      min-height: 42px;
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      color: var(--ink);
      font: inherit;
      padding: 9px 12px;
    }}
    .status-filters {{ display: flex; flex-wrap: wrap; gap: 6px; min-width: 0; }}
    .status-filter, .refresh-button, .clear-selection {{
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      color: var(--muted);
      cursor: pointer;
      font: inherit;
      padding: 9px 12px;
    }}
    .status-filter.active {{ border-color: var(--blue); color: var(--blue); background: #eaf1fb; font-weight: 700; }}
    .refresh-button {{ color: white; background: var(--blue); border-color: var(--blue); font-weight: 700; }}
    .refresh-button:disabled {{ cursor: wait; opacity: .7; }}
    .refresh-button, .status-filter {{ white-space: nowrap; }}
    .selection-bar {{ display: none; align-items: center; gap: 10px; margin: 0 0 16px; color: var(--muted); }}
    .selection-bar.active {{ display: flex; }}
    .result-count {{ margin: -8px 0 16px; color: var(--muted); font-size: 13px; }}
    .audit-warning {{ margin: 0 0 18px; padding: 14px 16px; border: 1px solid #f0b7c8; border-radius: 8px; background: #fff1f5; color: var(--red); }}
    .audit-warning ul {{ color: var(--ink); }}
    .filterable-run[hidden] {{ display: none !important; }}
    .selectable-run {{ cursor: pointer; }}
    tr.selectable-run:focus, tr.selectable-run:hover {{ outline: 2px solid #93b4ef; outline-offset: -2px; }}
    .run.selected {{ box-shadow: 0 0 0 2px #93b4ef; }}
    .panel {{ display: none; }}
    .panel.active {{ display: block; }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
    }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 6px; }}
    .metric strong {{ font-size: 26px; }}
    .category-note {{ color: var(--muted); margin: 0 0 14px; }}
    .run {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-left: 6px solid var(--blue);
      border-radius: 8px;
      padding: 18px;
      margin: 14px 0;
    }}
    .run.closed {{ border-left-color: var(--green); }}
    .run.blocked {{ border-left-color: var(--red); }}
    .run.open {{ border-left-color: var(--amber); }}
    .run-head {{ display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; }}
    .run h2 {{ margin: 0; font-size: 20px; }}
    .path {{ color: var(--muted); font-size: 13px; margin-top: 4px; word-break: break-all; }}
    .badge {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 700; background: #eaf1fb; color: var(--blue); }}
    .badge.closed {{ background: #e8f5ee; color: var(--green); }}
    .badge.blocked {{ background: #fde8ef; color: var(--red); }}
    .badge.open {{ background: #fff3df; color: var(--amber); }}
    .table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      display: table;
    }}
    .table th, .table td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }}
    .table th {{ color: var(--muted); background: #fbfcff; font-weight: 700; }}
    .table tr:last-child td {{ border-bottom: 0; }}
    .grid {{ display: grid; grid-template-columns: minmax(260px, 1fr) minmax(260px, 1fr); gap: 14px; margin-top: 14px; }}
    .box {{ border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fbfcff; }}
    .box h3 {{ margin: 0 0 8px; font-size: 14px; }}
    .kv {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .pill {{ border: 1px solid var(--line); border-radius: 6px; padding: 5px 8px; color: var(--muted); background: white; font-size: 12px; }}
    .analysis-intro {{ margin: 0 0 14px; color: var(--muted); }}
    .analysis-correlation {{ margin-bottom: 18px; }}
    .proposal {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-left: 6px solid var(--blue);
      border-radius: 8px;
      padding: 18px;
      margin: 14px 0;
    }}
    .proposal.split {{ border-left-color: var(--amber); }}
    .proposal.merge {{ border-left-color: #7c3aed; }}
    .proposal.investigate {{ border-left-color: var(--blue); }}
    .proposal-head {{ display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; }}
    .proposal-head h2 {{ margin: 4px 0 0; font-size: 18px; }}
    .proposal-kicker {{ color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }}
    .badge.pending {{ background: #eef2ff; color: #4338ca; }}
    .proposal-rationale {{ margin: 16px 0 0; }}
    .analysis-grid {{ display: grid; grid-template-columns: repeat(2, minmax(260px, 1fr)); gap: 14px; margin-top: 14px; }}
    .analysis-grid .box {{ min-width: 0; }}
    .analysis-grid code {{ word-break: break-all; }}
    ul {{ margin: 8px 0 0; padding-left: 20px; }}
    li {{ margin: 3px 0; }}
    .empty {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 24px; color: var(--muted); }}
    @media (max-width: 900px) {{
      header, main {{ padding-left: 16px; padding-right: 16px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .analysis-grid {{ grid-template-columns: 1fr; }}
      .controls {{
        grid-template-columns: minmax(0, 1fr) auto;
        grid-template-areas:
          "search search"
          "status refresh";
        gap: 8px;
      }}
      .search {{ grid-area: search; }}
      .status-filters {{ grid-area: status; }}
      .refresh-button {{ grid-area: refresh; }}
    }}
    @media (max-width: 560px) {{
      .controls {{
        grid-template-columns: 1fr;
        grid-template-areas:
          "search"
          "status"
          "refresh";
      }}
      .refresh-button {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Skill Run Observation Dashboard</h1>
    <p class="sub">Root: {html.escape(str(payload["root"]))} | Sessions: {html.escape(str(payload["sessions_dir"]))} | <a href="/api/runs">JSON</a></p>
  </header>
  <main>
    <nav class="tabs" aria-label="Dashboard categories">
      <button class="tab active" data-panel="overview">Overview</button>
      <button class="tab" data-panel="flows">Prompt Flows</button>
      <button class="tab" data-panel="recovery">Recovery</button>
      <button class="tab" data-panel="attention">Attention</button>
      <button class="tab" data-panel="closure">Closure</button>
      <button class="tab" data-panel="evidence">Evidence</button>
      <button class="tab" data-panel="handoff">Handoff</button>
      <button class="tab" data-panel="xids">XID Usage</button>
      <button class="tab" data-panel="analysis">Analysis</button>
      <button class="tab" data-panel="missing-information">Missing Information</button>
      <button class="tab" data-panel="decision-trace">Decision Trace</button>
    </nav>
    <section class="controls" aria-label="Skill run filters">
      <input id="run-search" class="search" type="search" placeholder="Search skill, path, run ID, session, repository, or status" aria-label="Search Skill runs">
      <div class="status-filters" aria-label="Status filter">
        <button class="status-filter active" data-status="all">All</button>
        <button class="status-filter" data-status="blocked">Blocked</button>
        <button class="status-filter" data-status="open">Open</button>
        <button class="status-filter" data-status="closed">Closed</button>
      </div>
      <button id="refresh-runs" class="refresh-button" type="button">Refresh</button>
    </section>
    <div id="selection-bar" class="selection-bar"><span id="selection-label"></span><button id="clear-selection" class="clear-selection" type="button">Show all runs</button></div>
    <p id="result-count" class="result-count"></p>
    {audit_warning}
    <section id="overview" class="panel active">
      <section class="metrics">{cards}</section>
      <p class="category-note">Recent Skill runs and aggregate status. Detailed records are split into the other categories.</p>
      <table class="table">
        <thead><tr><th>Skill</th><th>Status</th><th>Closure</th><th>Updated</th><th>Log</th></tr></thead>
        <tbody>{overview_rows}</tbody>
      </table>
    </section>
    <section id="flows" class="panel">
      <p class="category-note">One prompt-rooted flow across generic workflow runs and delegated Skill Runs.</p>
      <table class="table">
        <thead><tr><th>Flow</th><th>Status</th><th>State</th><th>Runs</th><th>Work items</th><th>Skills</th><th>Reconcile</th><th>Blockers</th><th>Updated</th></tr></thead>
        <tbody>{flow_rows}</tbody>
      </table>
      <div class="box"><h3>Execution tree</h3>{flow_tree}</div>
      <div class="box"><h3>Flow details</h3>{flow_details}</div>
    </section>
    <section id="attention" class="panel">
      <p class="category-note">Runs that need action before they can be treated as closed.</p>
      {attention_rows}
    </section>
    <section id="recovery" class="panel">
      <p class="category-note">Recovery proposals and human confirmations. The dashboard records the proposed resume point; it does not execute recovery.</p>
      <table class="table">
        <thead><tr><th>Recovery ID</th><th>Status</th><th>Flow</th><th>Run</th><th>Resume location</th><th>Reason</th><th>Next action</th><th>Executable action</th><th>Owner</th><th>Verification</th><th>Max attempts</th><th>Stop conditions</th><th>Reviewer</th><th>Log</th></tr></thead>
        <tbody>{recovery_rows}</tbody>
      </table>
    </section>
    <section id="closure" class="panel">
      <p class="category-note">Runtime phase, closure gate, and quality gate state.</p>
      {closure_rows}
    </section>
    <section id="evidence" class="panel">
      <p class="category-note">Outputs, evidence artifacts, and quality-check artifacts recorded by Skill runs.</p>
      {evidence_rows}
    </section>
    <section id="handoff" class="panel">
      <p class="category-note">Handoff records plus unknown, risk, and judgment records that affect continuity.</p>
      {handoff_rows}
    </section>
    <section id="xids" class="panel">
      <p class="category-note">Base and local XIDs selected or used by each Skill run, plus available XIDs that were not used.</p>
      <div class="box"><h3>Unused XID Ranking</h3>{unused_xid_rows}</div>
      {xid_rows}
    </section>
    <section id="analysis" class="panel">
      <p class="analysis-intro">Proposal-only analysis. Review evidence, counterevidence, unknowns, and the verification plan before changing canonical Skills, Knowledge, routing, or XIDs.</p>
      <section class="metrics">{analysis_cards}</section>
      <div class="box analysis-correlation">
        <h3>Correlation coverage</h3>
        <div class="kv">{analysis_correlation_pills}</div>
      </div>
      {analysis_proposal_rows}
    </section>
    <section id="decision-trace" class="panel">
      <p class="category-note">AI decision-trace events, provisional resolutions, branches, and the current dependency graph. This panel observes records; it does not execute adoption or return operations.</p>
      <section class="metrics"><div class="metric"><span>Trace events</span><strong>{html.escape(str(decision_trace_summary.get('events', 0)))}</strong></div><div class="metric"><span>Validation</span><strong>{html.escape(str(decision_trace_validation.get('valid', False)))}</strong></div></section>
      <table class="table">
        <thead><tr><th>Event</th><th>Type</th><th>Status</th><th>Resolution</th><th>Branch</th><th>Reason</th></tr></thead>
        <tbody>{decision_trace_rows}</tbody>
      </table>
      <div class="box"><h3>Impact groups</h3><table class="table"><thead><tr><th>Group</th><th>Events</th></tr></thead><tbody>{decision_trace_group_rows}</tbody></table></div>
      <div class="box"><h3>Dependency graph (Mermaid)</h3><pre>{html.escape(str(decision_trace.get('graph') or ''))}</pre></div>
      {decision_trace_issue_html}
    </section>
    <section id="missing-information" class="panel">
      <p class="category-note">Information required to correlate Skill execution, MCP access, Knowledge application, and downstream feedback.</p>
      <div class="box"><h3>Missing Information Ranking</h3>{missing_information_rows}</div>
      {missing_information_cards}
    </section>
  </main>
  <script>
    let activePanel = "overview";
    let statusFilter = "all";
    let searchQuery = "";
    let selectedRun = null;
    function showPanel(id) {{
      activePanel = id;
      const tabs = Array.from(document.querySelectorAll(".tab"));
      const panels = Array.from(document.querySelectorAll(".panel"));
      tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.panel === id));
      panels.forEach((panel) => panel.classList.toggle("active", panel.id === id));
    }}
    function applyFilters() {{
      const query = searchQuery.trim().toLowerCase();
      const runs = Array.from(document.querySelectorAll(".filterable-run"));
      let visible = 0;
      const visiblePaths = new Set();
      runs.forEach((run) => {{
        const matchesStatus = statusFilter === "all" || run.dataset.status === statusFilter;
        const matchesSearch = !query || (run.dataset.search || "").includes(query);
        const matchesSelection = !selectedRun || run.dataset.runPath === selectedRun;
        const show = matchesStatus && matchesSearch && matchesSelection;
        run.hidden = !show;
        run.classList.toggle("selected", Boolean(selectedRun && run.dataset.runPath === selectedRun));
        if (show && run.dataset.runPath) visiblePaths.add(run.dataset.runPath);
      }});
      visible = visiblePaths.size;
      document.getElementById("result-count").textContent = `${{visible}} matching run${{visible === 1 ? "" : "s"}}`;
      const selectionBar = document.getElementById("selection-bar");
      selectionBar.classList.toggle("active", Boolean(selectedRun));
      document.getElementById("selection-label").textContent = selectedRun ? `Focused run: ${{selectedRun}}` : "";
    }}
    function selectRun(path) {{ selectedRun = path; applyFilters(); }}
    function bindDashboard() {{
      document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => showPanel(tab.dataset.panel)));
      const search = document.getElementById("run-search");
      search.value = searchQuery;
      search.addEventListener("input", () => {{ searchQuery = search.value; applyFilters(); }});
      document.querySelectorAll(".status-filter").forEach((button) => {{
        button.classList.toggle("active", button.dataset.status === statusFilter);
        button.addEventListener("click", () => {{
          statusFilter = button.dataset.status;
          document.querySelectorAll(".status-filter").forEach((item) => item.classList.toggle("active", item === button));
          applyFilters();
        }});
      }});
      document.querySelectorAll(".selectable-run").forEach((run) => {{
        run.addEventListener("click", () => selectRun(run.dataset.runPath));
        run.addEventListener("keydown", (event) => {{ if (event.key === "Enter" || event.key === " ") selectRun(run.dataset.runPath); }});
      }});
      document.getElementById("clear-selection").addEventListener("click", () => {{ selectedRun = null; applyFilters(); }});
      document.getElementById("refresh-runs").addEventListener("click", refreshDashboard);
      showPanel(activePanel);
      applyFilters();
    }}
    async function refreshDashboard() {{
      const button = document.getElementById("refresh-runs");
      button.disabled = true;
      button.textContent = "Refreshing";
      try {{
        const probe = await fetch(`/api/runs?t=${{Date.now()}}`, {{ cache: "no-store" }});
        if (!probe.ok) throw new Error(`JSON refresh failed: ${{probe.status}}`);
        const response = await fetch(`/?t=${{Date.now()}}`, {{ cache: "no-store" }});
        if (!response.ok) throw new Error(`Dashboard refresh failed: ${{response.status}}`);
        const next = new DOMParser().parseFromString(await response.text(), "text/html");
        document.querySelector("header").replaceWith(next.querySelector("header"));
        document.querySelector("main").replaceWith(next.querySelector("main"));
        bindDashboard();
      }} catch (error) {{
        button.textContent = "Refresh failed";
        button.title = String(error);
        button.disabled = false;
      }}
    }}
    bindDashboard();
  </script>
</body>
</html>"""


def _base_run_parts(run: object) -> tuple[str, str, str, str, dict, dict, list]:
    assert isinstance(run, dict)
    status = html.escape(str(run["status"]))
    skill_id = html.escape(str(run["skill_id"]))
    path = html.escape(str(run["path"]))
    mtime = html.escape(str(run["mtime"]))
    sections = run.get("sections") if isinstance(run.get("sections"), dict) else {}
    counts = run.get("counts") if isinstance(run.get("counts"), dict) else {}
    blockers = run.get("blockers") if isinstance(run.get("blockers"), list) else []
    return status, skill_id, path, mtime, sections, counts, blockers


def _overview_row(run: object) -> str:
    status, skill_id, path, mtime, _, _, _ = _base_run_parts(run)
    closure = html.escape(str(run["closure_status"])) if isinstance(run, dict) else ""
    attributes = _run_data_attributes(run)
    return (
        f"<tr class='filterable-run selectable-run' tabindex='0' {attributes}>"
        f"<td>{skill_id}</td>"
        f"<td><span class='badge {status}'>{status}</span></td>"
        f"<td>{closure}</td>"
        f"<td>{mtime}</td>"
        f"<td class='path'>{path}</td>"
        "</tr>"
    )


def _attention_card(run: object) -> str:
    status, skill_id, path, mtime, _, _, blockers = _base_run_parts(run)
    blocker_html = "<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in blockers[:16]) + "</ul>"
    return _category_card(
        run=run,
        status=status,
        skill_id=skill_id,
        path=path,
        mtime=mtime,
        body=f"<div class='box'><h3>Blockers</h3>{blocker_html}</div>",
    )


def _closure_card(run: object) -> str:
    status, skill_id, path, mtime, sections, _, _ = _base_run_parts(run)
    phase_pills = "".join(
        f"<span class='pill'>{html.escape(str(name))}: {html.escape(str(value))}</span>"
        for name, value in sections.items()
    )
    closure = html.escape(str(run["closure_status"])) if isinstance(run, dict) else ""
    quality = html.escape(str(run["quality_status"])) if isinstance(run, dict) else ""
    required = html.escape(str(run["quality_required"])) if isinstance(run, dict) else ""
    body = (
        f"<div class='box'><h3>Runtime State</h3><div class='kv'>{phase_pills}</div></div>"
        f"<div class='box'><h3>Closure</h3><div class='kv'><span class='pill'>closure: {closure}</span>"
        f"<span class='pill'>quality: {quality}</span><span class='pill'>quality required: {required}</span></div></div>"
    )
    return _category_card(run=run, status=status, skill_id=skill_id, path=path, mtime=mtime, body=body)


def _evidence_card(run: object) -> str:
    status, skill_id, path, mtime, _, counts, _ = _base_run_parts(run)
    count_pills = "".join(
        f"<span class='pill'>{html.escape(str(name))}: {html.escape(str(counts.get(name, 0)))}</span>"
        for name in ("outputs", "evidence", "checks", "artifacts")
    )
    artifacts = run.get("artifacts") if isinstance(run, dict) and isinstance(run.get("artifacts"), list) else []
    artifact_items = "".join(
        "<li>"
        f"{html.escape(str(item.get('artifact_id', '-')))} "
        f"{html.escape(str(item.get('kind', '-')))} "
        f"{html.escape(str(item.get('status', '-')))}: "
        f"{html.escape(str(item.get('target', '-')))}"
        "</li>"
        for item in artifacts[:8]
        if isinstance(item, dict) and item.get("kind") in {"output", "evidence", "check"}
    )
    if not artifact_items:
        artifact_items = "<li>No output/evidence/check artifacts.</li>"
    body = (
        f"<div class='box'><h3>Artifact Counts</h3><div class='kv'>{count_pills}</div></div>"
        f"<div class='box'><h3>Recent Records</h3><ul>{artifact_items}</ul></div>"
    )
    return _category_card(run=run, status=status, skill_id=skill_id, path=path, mtime=mtime, body=body)


def _handoff_card(run: object) -> str:
    status, skill_id, path, mtime, _, counts, _ = _base_run_parts(run)
    count_pills = "".join(
        f"<span class='pill'>{html.escape(str(name))}: {html.escape(str(counts.get(name, 0)))}</span>"
        for name in ("handoffs", "unknowns", "risks", "judgments")
    )
    artifacts = run.get("artifacts") if isinstance(run, dict) and isinstance(run.get("artifacts"), list) else []
    concerns = run.get("concerns") if isinstance(run, dict) and isinstance(run.get("concerns"), list) else []
    handoff_items = "".join(
        f"<li>{html.escape(str(item.get('artifact_id', '-')))}: {html.escape(str(item.get('target', '-')))}</li>"
        for item in artifacts[:8]
        if isinstance(item, dict) and item.get("kind") == "handoff"
    )
    concern_items = "".join(
        "<li>"
        f"{html.escape(str(item.get('concern_id', '-')))} "
        f"{html.escape(str(item.get('kind', '-')))} "
        f"{html.escape(str(item.get('status', '-')))}: "
        f"{html.escape(str(item.get('text', '-')))}"
        "</li>"
        for item in concerns[:8]
        if isinstance(item, dict)
    )
    if not handoff_items:
        handoff_items = "<li>No handoff artifacts.</li>"
    if not concern_items:
        concern_items = "<li>No unknown/risk/judgment records.</li>"
    body = (
        f"<div class='box'><h3>Continuity Counts</h3><div class='kv'>{count_pills}</div></div>"
        f"<div class='box'><h3>Handoff</h3><ul>{handoff_items}</ul></div>"
        f"<div class='box'><h3>Unknown / Risk / Judgment</h3><ul>{concern_items}</ul></div>"
    )
    return _category_card(run=run, status=status, skill_id=skill_id, path=path, mtime=mtime, body=body)


def _xid_usage_card(run: object) -> str:
    status, skill_id, path, mtime, _, _, _ = _base_run_parts(run)
    assert isinstance(run, dict)
    used_xids = run.get("used_xids") if isinstance(run.get("used_xids"), list) else []
    selected_xids = run.get("selected_xids") if isinstance(run.get("selected_xids"), list) else []
    queried_xids = run.get("queried_xids") if isinstance(run.get("queried_xids"), list) else []
    loaded_xids = run.get("loaded_xids") if isinstance(run.get("loaded_xids"), list) else []
    available_xids = run.get("available_xids") if isinstance(run.get("available_xids"), list) else []
    unused_xids = run.get("unused_xids") if isinstance(run.get("unused_xids"), list) else []
    used = _xid_pills(used_xids, empty="No used XIDs recorded.")
    selected = _xid_pills(selected_xids, empty="No selected knowledge XIDs.")
    queried = _xid_pills(queried_xids, empty="No MCP-resolved XIDs.")
    loaded = _xid_pills(loaded_xids, empty="No client-loaded XIDs.")
    available = _xid_pills(available_xids, empty="No available base/local knowledge XIDs.")
    unused = _xid_pills(unused_xids, empty="No unused available base/local XIDs.")
    body = (
        f"<div class='box'><h3>Used XIDs</h3>{used}</div>"
        f"<div class='box'><h3>Selected Knowledge Inputs</h3>{selected}</div>"
        f"<div class='box'><h3>MCP-resolved XIDs</h3>{queried}</div>"
        f"<div class='box'><h3>Client-loaded XIDs</h3>{loaded}</div>"
        f"<div class='box'><h3>Available Knowledge XIDs (base/local)</h3>{available}</div>"
        f"<div class='box'><h3>Unused Available XIDs (base/local)</h3>{unused}</div>"
    )
    return _category_card(run=run, status=status, skill_id=skill_id, path=path, mtime=mtime, body=body)


def _missing_information_card(run: object) -> str:
    status, skill_id, path, mtime, _, _, _ = _base_run_parts(run)
    assert isinstance(run, dict)
    values = run.get("missing_information") if isinstance(run.get("missing_information"), list) else []
    items = "".join(
        "<li>"
        f"<strong>{html.escape(str(item.get('label', item.get('code', '-'))))}</strong>: "
        f"{html.escape(str(item.get('detail', '-')))}"
        "</li>"
        for item in values
        if isinstance(item, dict)
    )
    body = f"<div class='box'><h3>Missing Tuning Information</h3><ul>{items}</ul></div>"
    return _category_card(run=run, status=status, skill_id=skill_id, path=path, mtime=mtime, body=body)


def _xid_pills(values: object, *, empty: str) -> str:
    if not isinstance(values, list) or not values:
        return f"<p class='path'>{html.escape(empty)}</p>"
    return "<div class='kv'>" + "".join(
        f"<span class='pill'>{html.escape(str(value))}</span>" for value in values[:20]
    ) + "</div>"


def _unused_xid_ranking_table(rows: object) -> str:
    if not isinstance(rows, list) or not rows:
        return "<p class='path'>No unused available base/local XIDs were found.</p>"
    body = "".join(_unused_xid_row(row) for row in rows[:50] if isinstance(row, dict))
    return (
        "<table class='table'>"
        "<thead><tr><th>XID</th><th>Unused Count</th><th>Skills</th><th>Runs</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def _missing_information_ranking_table(rows: object) -> str:
    if not isinstance(rows, list) or not rows:
        return "<p class='path'>No missing tuning information was detected.</p>"
    body = "".join(
        "<tr>"
        f"<td>{html.escape(str(row.get('label', row.get('code', ''))))}</td>"
        f"<td>{html.escape(str(row.get('count', '')))}</td>"
        f"<td>{html.escape(', '.join(str(value) for value in row.get('skills', [])[:8]))}</td>"
        f"<td>{html.escape(str(row.get('detail', '')))}</td>"
        "</tr>"
        for row in rows[:50]
        if isinstance(row, dict)
    )
    return (
        "<table class='table'>"
        "<thead><tr><th>Information</th><th>Runs</th><th>Skills</th><th>Reason</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def _unused_xid_row(row: dict[str, object]) -> str:
    xid = html.escape(str(row.get("xid", "")))
    count = html.escape(str(row.get("count", "")))
    skills_value = row.get("skills") if isinstance(row.get("skills"), list) else []
    runs_value = row.get("runs") if isinstance(row.get("runs"), list) else []
    skills = ", ".join(html.escape(str(value)) for value in skills_value[:8])
    runs = "<br>".join(html.escape(str(value)) for value in runs_value[:5])
    return f"<tr><td>{xid}</td><td>{count}</td><td>{skills}</td><td class='path'>{runs}</td></tr>"


_ANALYSIS_CATEGORY_LABELS = {
    "knowledge_correction": "Knowledge correction candidate",
    "skill_correction": "Skill correction candidate",
    "split": "Skill split candidate",
    "merge": "Skill merge candidate",
    "knowledge_usage_gap": "Knowledge usage gap",
}


def _analysis_list(value: object, *, empty: str, code: bool = False, limit: int = 8) -> str:
    values = value if isinstance(value, list) else []
    if not values:
        return f"<p class='path'>{html.escape(empty)}</p>"
    items = []
    for item in values[:limit]:
        rendered = html.escape(str(item))
        items.append(f"<li><code>{rendered}</code></li>" if code else f"<li>{rendered}</li>")
    if len(values) > limit:
        items.append(f"<li>... and {len(values) - limit} more</li>")
    return "<ul>" + "".join(items) + "</ul>"


def _analysis_value_text(value: object, *, empty: str) -> str:
    values = value if isinstance(value, list) else []
    if not values:
        return html.escape(empty)
    rendered = [html.escape(str(item)) for item in values[:12]]
    if len(values) > 12:
        rendered.append(f"... and {len(values) - 12} more")
    return ", ".join(rendered)


def _analysis_proposal_card(proposal: dict[str, object]) -> str:
    category = str(proposal.get("category", "")).strip()
    category_label = _ANALYSIS_CATEGORY_LABELS.get(category, "Boundary investigation candidate")
    proposal_kind = str(proposal.get("proposal", "investigate")).strip() or "investigate"
    proposal_class = proposal_kind if proposal_kind in {"split", "merge"} else "investigate"
    proposal_id = str(proposal.get("proposal_id", "unnamed-proposal"))
    decision = proposal.get("decision") if isinstance(proposal.get("decision"), dict) else {}
    decision_status = str(decision.get("status", "pending"))
    skills = proposal.get("skill_ids") if isinstance(proposal.get("skill_ids"), list) else []
    xids = proposal.get("subject_xids") if isinstance(proposal.get("subject_xids"), list) else []
    rationale = str(proposal.get("rationale", "No rationale recorded."))
    return f"""
<article class="proposal {proposal_class}">
  <div class="proposal-head">
    <div>
      <div class="proposal-kicker">{html.escape(category_label)}</div>
      <h2>{html.escape(proposal_id)}</h2>
    </div>
    <span class="badge pending">decision: {html.escape(decision_status)}</span>
  </div>
  <div class="kv" style="margin-top: 14px;">
    <span class="pill">type: {html.escape(proposal_kind)}</span>
    <span class="pill">support: {html.escape(str(proposal.get("support", 0)))}</span>
    <span class="pill">Skills: {_analysis_value_text(skills, empty="none")}</span>
    <span class="pill">XIDs: {_analysis_value_text(xids, empty="none")}</span>
  </div>
  <p class="proposal-rationale"><strong>Rationale:</strong> {html.escape(rationale)}</p>
  <div class="analysis-grid">
    <div class="box"><h3>Evidence</h3>{_analysis_list(proposal.get("evidence_refs"), empty="No evidence reference.", code=True)}</div>
    <div class="box"><h3>Counterevidence</h3>{_analysis_list(proposal.get("counterevidence"), empty="None recorded.")}</div>
    <div class="box"><h3>Unknowns</h3>{_analysis_list(proposal.get("unknowns"), empty="None recorded.")}</div>
    <div class="box"><h3>Verification plan</h3>{_analysis_list(proposal.get("verification_plan"), empty="Define a human verification plan.")}</div>
  </div>
</article>"""


def _category_card(*, run: object, status: str, skill_id: str, path: str, mtime: str, body: str) -> str:
    attributes = _run_data_attributes(run)
    return f"""
<section class="run {status} filterable-run selectable-run" tabindex="0" {attributes}>
  <div class="run-head">
    <div>
      <h2>{skill_id}</h2>
      <div class="path">{path}</div>
      <div class="path">updated {mtime}</div>
    </div>
    <span class="badge {status}">{status}</span>
  </div>
  <div class="grid">{body}</div>
</section>"""


def _run_data_attributes(run: object) -> str:
    if not isinstance(run, dict):
        return 'data-run-path="" data-status="" data-search=""'
    missing = run.get("missing_information") if isinstance(run.get("missing_information"), list) else []
    missing_text = " ".join(
        f"{item.get('code', '')} {item.get('label', '')}"
        for item in missing
        if isinstance(item, dict)
    )
    values = [
        run.get("skill_id", ""),
        run.get("path", ""),
        run.get("run_id", ""),
        run.get("mcp_session_id", ""),
        run.get("repository_fingerprint", ""),
        run.get("status", ""),
        run.get("closure_status", ""),
        run.get("quality_status", ""),
        missing_text,
    ]
    search = " ".join(str(value) for value in values if value).lower()
    return (
        f'data-run-path="{html.escape(str(run.get("path", "")), quote=True)}" '
        f'data-status="{html.escape(str(run.get("status", "")), quote=True)}" '
        f'data-search="{html.escape(search, quote=True)}"'
    )


def _has_observed_records(run: object) -> bool:
    if not isinstance(run, dict) or not isinstance(run.get("counts"), dict):
        return False
    counts = run["counts"]
    return any(int(counts.get(name, 0)) > 0 for name in ("outputs", "evidence", "checks"))


def _has_handoff_records(run: object) -> bool:
    if not isinstance(run, dict) or not isinstance(run.get("counts"), dict):
        return False
    counts = run["counts"]
    return any(int(counts.get(name, 0)) > 0 for name in ("handoffs", "unknowns", "risks", "judgments"))


def _has_xid_records(run: object) -> bool:
    if not isinstance(run, dict):
        return False
    return any(
        isinstance(run.get(name), list) and len(run.get(name)) > 0
        for name in (
            "available_xids",
            "selected_xids",
            "queried_xids",
            "loaded_xids",
            "used_xids",
            "unused_xids",
        )
    )


class DashboardServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler,
        *,
        root: Path,
        sessions_dir: Path,
        mcp_audit_log: Path,
    ) -> None:
        super().__init__(server_address, handler)
        self.root = root
        self.sessions_dir = sessions_dir
        self.mcp_audit_log = mcp_audit_log


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardServer

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("dashboard: " + format % args + "\n")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/runs":
            payload = build_payload(self.server.root, self.server.sessions_dir, self.server.mcp_audit_log)
            _json_response(self, payload)
            return
        if parsed.path == "/healthz":
            _json_response(self, {"ok": True})
            return
        if parsed.path in {"/", "/index.html"}:
            payload = build_payload(self.server.root, self.server.sessions_dir, self.server.mcp_audit_log)
            body = _html_page(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        _json_response(self, {"error": "not found"}, status=404)


def serve_dashboard(
    *,
    root: Path,
    sessions_dir: Path,
    mcp_audit_log: Path,
    host: str,
    port: int,
    open_browser: bool,
) -> None:
    server = DashboardServer(
        (host, port),
        DashboardHandler,
        root=root.resolve(),
        sessions_dir=sessions_dir.resolve(),
        mcp_audit_log=mcp_audit_log.resolve(),
    )
    url = f"http://{host}:{server.server_port}/"
    print(f"Skill Run Observation Dashboard: {url}")
    print(f"root: {root.resolve()}")
    print(f"sessions: {sessions_dir.resolve()}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


def cmd_dashboard(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    sessions_dir = Path(args.sessions_dir).resolve() if args.sessions_dir else root / "work" / "sessions"
    mcp_audit_log = Path(args.mcp_audit_log).resolve() if args.mcp_audit_log else root / "work" / "mcp" / "xid_audit.jsonl"
    if args.dashboard_cmd == "data":
        payload = build_payload(root, sessions_dir, mcp_audit_log)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.dashboard_cmd == "serve":
        serve_dashboard(
            root=root,
            sessions_dir=sessions_dir,
            mcp_audit_log=mcp_audit_log,
            host=args.host,
            port=args.port,
            open_browser=args.open_browser,
        )
        return 0
    return 2
