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
NON_XID_TOKEN_PREFIXES = ("WI-", "OUT-", "EVD-", "CHK-", "HND-", "UNK-", "RISK-", "JDG-")


@dataclass(frozen=True)
class DashboardRun:
    path: str
    name: str
    mtime: str
    skill_id: str
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

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "name": self.name,
            "mtime": self.mtime,
            "skill_id": self.skill_id,
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
        }


def _is_skill_run_log(text: str) -> bool:
    return text.lstrip().startswith("# Skill Run Log") or (
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


def _parse_one_run(path: Path, root: Path) -> DashboardRun | None:
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
    if "## Skill Load Gate\n\n- status: `opened_by_xrefkit_skill_run`" not in text:
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
    used_xids = sorted(set(selected_xids) | set(_runtime_used_xids(artifacts, concerns)))
    unused_xids = sorted(set(available_xids) - set(used_xids))
    skill_id = _log_skill_id(text) or "unknown"
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    return DashboardRun(
        path=_rel(path, root),
        name=path.name,
        mtime=mtime,
        skill_id=skill_id,
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
    )


def collect_runs(root: Path, sessions_dir: Path) -> list[DashboardRun]:
    root = root.resolve()
    sessions_dir = sessions_dir.resolve()
    if not sessions_dir.exists():
        return []
    runs: list[DashboardRun] = []
    for path in sorted(sessions_dir.rglob("*.md")):
        if not path.is_file():
            continue
        run = _parse_one_run(path, root)
        if run is not None:
            runs.append(run)
    runs.sort(key=lambda item: item.mtime, reverse=True)
    return runs


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


def build_payload(root: Path, sessions_dir: Path) -> dict[str, object]:
    runs = collect_runs(root, sessions_dir)
    return {
        "root": str(root.resolve()),
        "sessions_dir": str(sessions_dir.resolve()),
        "summary": _summary(runs),
        "unused_xid_ranking": _unused_xid_ranking(runs),
        "runs": [run.to_dict() for run in runs],
    }


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
    assert isinstance(summary, dict)
    assert isinstance(runs, list)
    cards = "".join(
        f"<div class='metric'><span>{html.escape(str(label))}</span><strong>{value}</strong></div>"
        for label, value in [
            ("Skill runs", summary["runs"]),
            ("Closed", summary["closed"]),
            ("Blocked", summary["blocked"]),
            ("Open", summary["open"]),
            ("Unknowns", summary["unknowns"]),
            ("Risks", summary["risks"]),
            ("Handoffs", summary["handoffs"]),
            ("Used XIDs", summary["used_xids"]),
            ("Unused XIDs", summary["unused_xids"]),
        ]
    )
    overview_rows = "\n".join(_overview_row(run) for run in runs[:30])
    attention_rows = "\n".join(_attention_card(run) for run in runs if isinstance(run, dict) and run.get("status") == "blocked")
    closure_rows = "\n".join(_closure_card(run) for run in runs)
    evidence_rows = "\n".join(_evidence_card(run) for run in runs if _has_observed_records(run))
    handoff_rows = "\n".join(_handoff_card(run) for run in runs if _has_handoff_records(run))
    xid_rows = "\n".join(_xid_usage_card(run) for run in runs if _has_xid_records(run))
    unused_xid_rows = _unused_xid_ranking_table(payload.get("unused_xid_ranking", []))
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
      margin: 0 0 18px;
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
    ul {{ margin: 8px 0 0; padding-left: 20px; }}
    li {{ margin: 3px 0; }}
    .empty {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 24px; color: var(--muted); }}
    @media (max-width: 780px) {{
      header, main {{ padding-left: 16px; padding-right: 16px; }}
      .grid {{ grid-template-columns: 1fr; }}
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
      <button class="tab" data-panel="attention">Attention</button>
      <button class="tab" data-panel="closure">Closure</button>
      <button class="tab" data-panel="evidence">Evidence</button>
      <button class="tab" data-panel="handoff">Handoff</button>
      <button class="tab" data-panel="xids">XID Usage</button>
    </nav>
    <section id="overview" class="panel active">
      <section class="metrics">{cards}</section>
      <p class="category-note">Recent Skill runs and aggregate status. Detailed records are split into the other categories.</p>
      <table class="table">
        <thead><tr><th>Skill</th><th>Status</th><th>Closure</th><th>Updated</th><th>Log</th></tr></thead>
        <tbody>{overview_rows}</tbody>
      </table>
    </section>
    <section id="attention" class="panel">
      <p class="category-note">Runs that need action before they can be treated as closed.</p>
      {attention_rows}
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
  </main>
  <script>
    const tabs = Array.from(document.querySelectorAll(".tab"));
    const panels = Array.from(document.querySelectorAll(".panel"));
    function showPanel(id) {{
      tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.panel === id));
      panels.forEach((panel) => panel.classList.toggle("active", panel.id === id));
    }}
    tabs.forEach((tab) => tab.addEventListener("click", () => showPanel(tab.dataset.panel)));
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
    return (
        "<tr>"
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
    return _category_card(status=status, skill_id=skill_id, path=path, mtime=mtime, body=body)


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
    return _category_card(status=status, skill_id=skill_id, path=path, mtime=mtime, body=body)


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
    return _category_card(status=status, skill_id=skill_id, path=path, mtime=mtime, body=body)


def _xid_usage_card(run: object) -> str:
    status, skill_id, path, mtime, _, _, _ = _base_run_parts(run)
    assert isinstance(run, dict)
    used_xids = run.get("used_xids") if isinstance(run.get("used_xids"), list) else []
    selected_xids = run.get("selected_xids") if isinstance(run.get("selected_xids"), list) else []
    available_xids = run.get("available_xids") if isinstance(run.get("available_xids"), list) else []
    unused_xids = run.get("unused_xids") if isinstance(run.get("unused_xids"), list) else []
    used = _xid_pills(used_xids, empty="No used XIDs recorded.")
    selected = _xid_pills(selected_xids, empty="No selected knowledge XIDs.")
    available = _xid_pills(available_xids, empty="No available base/local knowledge XIDs.")
    unused = _xid_pills(unused_xids, empty="No unused available base/local XIDs.")
    body = (
        f"<div class='box'><h3>Used XIDs</h3>{used}</div>"
        f"<div class='box'><h3>Selected Knowledge Inputs</h3>{selected}</div>"
        f"<div class='box'><h3>Available Knowledge XIDs (base/local)</h3>{available}</div>"
        f"<div class='box'><h3>Unused Available XIDs (base/local)</h3>{unused}</div>"
    )
    return _category_card(status=status, skill_id=skill_id, path=path, mtime=mtime, body=body)


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


def _unused_xid_row(row: dict[str, object]) -> str:
    xid = html.escape(str(row.get("xid", "")))
    count = html.escape(str(row.get("count", "")))
    skills_value = row.get("skills") if isinstance(row.get("skills"), list) else []
    runs_value = row.get("runs") if isinstance(row.get("runs"), list) else []
    skills = ", ".join(html.escape(str(value)) for value in skills_value[:8])
    runs = "<br>".join(html.escape(str(value)) for value in runs_value[:5])
    return f"<tr><td>{xid}</td><td>{count}</td><td>{skills}</td><td class='path'>{runs}</td></tr>"


def _category_card(*, status: str, skill_id: str, path: str, mtime: str, body: str) -> str:
    return f"""
<section class="run {status}">
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
        for name in ("available_xids", "selected_xids", "used_xids", "unused_xids")
    )


class DashboardServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler, *, root: Path, sessions_dir: Path) -> None:
        super().__init__(server_address, handler)
        self.root = root
        self.sessions_dir = sessions_dir


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardServer

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("dashboard: " + format % args + "\n")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/runs":
            payload = build_payload(self.server.root, self.server.sessions_dir)
            _json_response(self, payload)
            return
        if parsed.path == "/healthz":
            _json_response(self, {"ok": True})
            return
        if parsed.path in {"/", "/index.html"}:
            payload = build_payload(self.server.root, self.server.sessions_dir)
            body = _html_page(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        _json_response(self, {"error": "not found"}, status=404)


def serve_dashboard(*, root: Path, sessions_dir: Path, host: str, port: int, open_browser: bool) -> None:
    server = DashboardServer((host, port), DashboardHandler, root=root.resolve(), sessions_dir=sessions_dir.resolve())
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
    if args.dashboard_cmd == "data":
        payload = build_payload(root, sessions_dir)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.dashboard_cmd == "serve":
        serve_dashboard(
            root=root,
            sessions_dir=sessions_dir,
            host=args.host,
            port=args.port,
            open_browser=args.open_browser,
        )
        return 0
    return 2
