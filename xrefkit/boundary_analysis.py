"""Proposal-only Skill and Knowledge boundary analysis.

The first implementation consumes the JSON emitted by ``xrefkit dashboard
data``.  It intentionally produces observations and candidates only; it never
edits a Skill, Knowledge document, routing rule, or XID.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any


SCHEMA = "xrefkit.boundary_observation/v1"
_CORRELATION_LEVELS = ("exact", "bounded", "heuristic", "unknown")
_CANDIDATE_ORDER = {
    "knowledge_correction": 0,
    "skill_correction": 1,
    "split": 2,
    "merge": 3,
    "knowledge_usage_gap": 4,
}


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _string(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _strings(value: object) -> set[str]:
    return {item for item in (_string(raw) for raw in _as_list(value)) if item}


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _short_hash(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()[:16]


def load_dashboard_json(path: Path) -> tuple[dict[str, Any], str]:
    """Load and validate a dashboard JSON export, returning its source hash."""

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"could not read dashboard input: {exc}") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"dashboard input is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("dashboard input must be a JSON object")
    if not isinstance(payload.get("runs"), list):
        raise ValueError("dashboard input must contain a runs array")
    return payload, hashlib.sha256(raw).hexdigest()


def _correlation_level(run: dict[str, Any]) -> str:
    if all(_string(run.get(key)) for key in ("run_id", "mcp_session_id", "repository_fingerprint")):
        return "exact"
    if _string(run.get("run_id")):
        return "bounded"
    return "unknown"


def _run_xids(run: dict[str, Any]) -> set[str]:
    # Used XIDs are the strongest signal.  When they are unavailable, keep the
    # observation visible by falling back to the observed retrieval states.
    used = _strings(run.get("used_xids"))
    return used or (
        _strings(run.get("loaded_xids"))
        | _strings(run.get("queried_xids"))
        | _strings(run.get("selected_xids"))
    )


def _feedback_events(run: dict[str, Any], kind: str = "human") -> list[dict[str, Any]]:
    events = []
    for event in _as_list(run.get("observation_events")):
        item = _as_dict(event)
        if item.get("event") == f"{kind}.feedback":
            events.append(item)
    return events


def _event_target_xid(event: dict[str, Any], known_xids: set[str]) -> str | None:
    target = _string(event.get("target"))
    if target in known_xids:
        return target
    return None


def _new_skill_stat() -> dict[str, Any]:
    return {
        "run_count": 0,
        "closed": 0,
        "blocked": 0,
        "open": 0,
        "xids": set(),
        "used_xids": set(),
        "feedback": Counter(),
        "feedback_runs": defaultdict(list),
        "run_paths": [],
        "observed_sets": [],
        "missing_information": Counter(),
    }


def _new_xid_stat() -> dict[str, Any]:
    return {
        "run_count": 0,
        "skill_ids": set(),
        "available_count": 0,
        "selected_count": 0,
        "queried_count": 0,
        "loaded_count": 0,
        "used_count": 0,
        "unused_count": 0,
        "queried_not_loaded_count": 0,
        "loaded_not_applied_count": 0,
        "run_paths": [],
    }


def _correlation_counts(runs: list[dict[str, Any]]) -> dict[str, int]:
    counts = {level: 0 for level in _CORRELATION_LEVELS}
    for run in runs:
        counts[_correlation_level(run)] += 1
    return counts


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _candidate(
    *,
    category: str,
    subject_xids: set[str],
    skill_ids: set[str],
    support: int,
    evidence_refs: list[str],
    rationale: str,
    counterevidence: list[str],
    unknowns: list[str],
    verification_plan: list[str],
) -> dict[str, Any]:
    subject = sorted(subject_xids)
    skills = sorted(skill_ids)
    identity = {
        "category": category,
        "subject_xids": subject,
        "skill_ids": skills,
    }
    return {
        "proposal_id": f"bo-{_short_hash(identity)}",
        "proposal": "split" if category == "split" else "merge" if category == "merge" else "investigate",
        "category": category,
        "subject_xids": subject,
        "skill_ids": skills,
        "support": support,
        "evidence_refs": sorted(set(evidence_refs)),
        "rationale": rationale,
        "counterevidence": counterevidence,
        "unknowns": unknowns,
        "verification_plan": verification_plan,
        "decision": {"status": "pending", "owner": None},
    }


def _feedback_candidates(
    runs: list[dict[str, Any]],
    skill_stats: dict[str, dict[str, Any]],
    xid_stats: dict[str, dict[str, Any]],
    min_samples: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    known_xids = set(xid_stats)
    xid_feedback: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for run in runs:
        for event in _feedback_events(run):
            status = _string(event.get("status"))
            if status not in {"corrected", "rejected"}:
                continue
            target = _event_target_xid(event, known_xids)
            if target:
                xid_feedback[target].append((run, event))

    for xid, entries in sorted(xid_feedback.items()):
        if len(entries) < min_samples:
            continue
        refs = [_string(run.get("path")) for run, _ in entries]
        candidates.append(
            _candidate(
                category="knowledge_correction",
                subject_xids={xid},
                skill_ids={_string(run.get("skill_id")) for run, _ in entries},
                support=len(entries),
                evidence_refs=refs,
                rationale="Repeated human corrections or rejections target the same Knowledge XID.",
                counterevidence=["The correction may be task-specific rather than a defect in the Knowledge asset."],
                unknowns=["The dashboard does not prove whether the cause is content, routing, or Skill procedure."],
                verification_plan=[
                    "Review the affected outputs and source evidence.",
                    "Preserve the XID if its responsibility is unchanged.",
                    "Compare a bounded pre-change and post-change sample.",
                ],
            )
        )

    for skill_id, stat in sorted(skill_stats.items()):
        corrected = int(stat["feedback"].get("corrected", 0))
        rejected = int(stat["feedback"].get("rejected", 0))
        total = corrected + rejected
        if total < min_samples:
            continue
        refs = sorted({path for paths in stat["feedback_runs"].values() for path in paths})
        candidates.append(
            _candidate(
                category="skill_correction",
                subject_xids=set(stat["used_xids"]),
                skill_ids={skill_id},
                support=total,
                evidence_refs=refs,
                rationale=f"The Skill has repeated human feedback requiring correction or rejection ({total} events).",
                counterevidence=["Feedback may reflect varied task inputs or missing Knowledge rather than a stable Skill defect."],
                unknowns=["The dashboard does not contain the full task intent or private reasoning."],
                verification_plan=[
                    "Cluster the corrected outputs by task purpose and failure condition.",
                    "Update procedure, constraint, routing, or quality criteria only after human review.",
                    "Rerun the same bounded task population and compare quality outcomes.",
                ],
            )
        )
    return candidates


def _split_candidates(skill_stats: dict[str, dict[str, Any]], min_samples: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for skill_id, stat in sorted(skill_stats.items()):
        run_sets = [set(values) for values in stat["observed_sets"] if values]
        if len(run_sets) < min_samples * 2:
            continue
        xid_counts = Counter(xid for values in run_sets for xid in values)
        eligible = sorted(xid for xid, count in xid_counts.items() if count >= min_samples)
        for left, right in combinations(eligible, 2):
            cooccurrence = sum(left in values and right in values for values in run_sets)
            if cooccurrence != 0:
                continue
            support = min(xid_counts[left], xid_counts[right])
            candidates.append(
                _candidate(
                    category="split",
                    subject_xids={left, right},
                    skill_ids={skill_id},
                    support=support,
                    evidence_refs=sorted(stat["run_paths"]),
                    rationale=f"The Skill uses {left} and {right} in separate run clusters with no observed co-occurrence.",
                    counterevidence=["Separate XID usage does not by itself prove separate business responsibility."],
                    unknowns=["Task intent, authority, escalation, and quality ownership are not available in dashboard data."],
                    verification_plan=[
                        "Review the task and output clusters with the accountable owner.",
                        "Define child responsibilities, shared Knowledge, routing, and handoff contracts.",
                        "Compare routing and quality on a bounded post-split sample.",
                    ],
                )
            )
    return candidates


def _merge_candidates(skill_stats: dict[str, dict[str, Any]], min_samples: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    eligible = [
        (skill_id, stat)
        for skill_id, stat in sorted(skill_stats.items())
        if int(stat["run_count"]) >= min_samples and stat["xids"]
    ]
    for (left_id, left), (right_id, right) in combinations(eligible, 2):
        left_xids = set(left["xids"])
        right_xids = set(right["xids"])
        union = left_xids | right_xids
        overlap = len(left_xids & right_xids) / len(union) if union else 0.0
        if overlap < 0.8:
            continue
        candidates.append(
            _candidate(
                category="merge",
                subject_xids=union,
                skill_ids={left_id, right_id},
                support=min(int(left["run_count"]), int(right["run_count"])),
                evidence_refs=sorted(set(left["run_paths"]) | set(right["run_paths"])),
                rationale=f"{left_id} and {right_id} repeatedly observe substantially overlapping XID sets.",
                counterevidence=["Dashboard data cannot prove that authority, risk, approval, or quality ownership is the same."],
                unknowns=["Task purpose and handoff cost are not fully represented in the dashboard payload."],
                verification_plan=[
                    "Compare responsibilities, constraints, routing, and closure gates.",
                    "Confirm that a merged Skill would not weaken an approval or security boundary.",
                    "Run a bounded pre-change and post-merge comparison.",
                ],
            )
        )
    return candidates


def _usage_gap_candidates(xid_stats: dict[str, dict[str, Any]], min_samples: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for xid, stat in sorted(xid_stats.items()):
        gap_count = max(int(stat["loaded_not_applied_count"]), int(stat["queried_not_loaded_count"]))
        if gap_count < min_samples:
            continue
        evidence = [
            f"loaded_not_applied={stat['loaded_not_applied_count']}",
            f"queried_not_loaded={stat['queried_not_loaded_count']}",
        ]
        candidates.append(
            _candidate(
                category="knowledge_usage_gap",
                subject_xids={xid},
                skill_ids=set(stat["skill_ids"]),
                support=gap_count,
                evidence_refs=sorted(stat["run_paths"]),
                rationale=f"{xid} has repeated retrieval, loading, or application gaps.",
                counterevidence=["The gap may be an instrumentation or correlation defect, not a Knowledge defect."],
                unknowns=["Per-turn context assembly and exact XID attribution are not available in dashboard data."],
                verification_plan=[
                    "Check MCP audit and client-loaded XID records for the affected runs.",
                    "Repair observation or correlation before editing Knowledge.",
                    "If the Knowledge is genuinely unnecessary, review its routing or boundary with the owner.",
                ],
            )
        )
    return candidates


def _serialize_skill_stats(stats: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for skill_id, stat in sorted(stats.items()):
        rows.append(
            {
                "skill_id": skill_id,
                "run_count": stat["run_count"],
                "closed": stat["closed"],
                "blocked": stat["blocked"],
                "open": stat["open"],
                "xids": sorted(stat["xids"]),
                "used_xids": sorted(stat["used_xids"]),
                "feedback": dict(sorted(stat["feedback"].items())),
                "missing_information": dict(sorted(stat["missing_information"].items())),
                "run_paths": sorted(stat["run_paths"]),
            }
        )
    return rows


def _serialize_xid_stats(stats: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for xid, stat in sorted(stats.items()):
        rows.append(
            {
                "xid": xid,
                "run_count": stat["run_count"],
                "skill_ids": sorted(stat["skill_ids"]),
                "available_count": stat["available_count"],
                "selected_count": stat["selected_count"],
                "queried_count": stat["queried_count"],
                "loaded_count": stat["loaded_count"],
                "used_count": stat["used_count"],
                "unused_count": stat["unused_count"],
                "queried_not_loaded_count": stat["queried_not_loaded_count"],
                "loaded_not_applied_count": stat["loaded_not_applied_count"],
                "run_paths": sorted(stat["run_paths"]),
            }
        )
    return rows


def analyze_dashboard_payload(
    payload: dict[str, Any],
    *,
    source_hash: str | None = None,
    source_ref: str | None = None,
    min_samples: int = 2,
    max_candidates: int = 20,
) -> dict[str, Any]:
    """Create a deterministic proposal-only boundary report from dashboard data."""

    if min_samples < 1:
        raise ValueError("min_samples must be at least 1")
    if max_candidates < 1:
        raise ValueError("max_candidates must be at least 1")
    raw_runs = [item for item in _as_list(payload.get("runs")) if isinstance(item, dict)]
    skill_stats: dict[str, dict[str, Any]] = defaultdict(_new_skill_stat)
    xid_stats: dict[str, dict[str, Any]] = defaultdict(_new_xid_stat)

    for run in raw_runs:
        skill_id = _string(run.get("skill_id")) or "unknown"
        skill = skill_stats[skill_id]
        skill["run_count"] += 1
        status = _string(run.get("status")) or "open"
        if status in {"closed", "blocked", "open"}:
            skill[status] += 1
        observed_xids = _run_xids(run)
        skill["xids"].update(
            observed_xids
            | _strings(run.get("available_xids"))
            | _strings(run.get("selected_xids"))
        )
        skill["used_xids"].update(_strings(run.get("used_xids")))
        skill["run_paths"].append(_string(run.get("path")) or _string(run.get("name")))
        skill["observed_sets"].append(observed_xids)
        for item in _as_list(run.get("missing_information")):
            entry = _as_dict(item)
            code = _string(entry.get("code"))
            if code:
                skill["missing_information"][code] += 1
        for event in _feedback_events(run):
            status_value = _string(event.get("status")) or "unknown"
            skill["feedback"][status_value] += 1
            skill["feedback_runs"][status_value].append(_string(run.get("path")))

        available = _strings(run.get("available_xids"))
        selected = _strings(run.get("selected_xids"))
        queried = _strings(run.get("queried_xids"))
        loaded = _strings(run.get("loaded_xids"))
        used = _strings(run.get("used_xids"))
        unused = _strings(run.get("unused_xids"))
        queried_not_loaded = _strings(run.get("queried_not_loaded_xids"))
        loaded_not_applied = _strings(run.get("loaded_not_applied_xids"))
        all_xids = available | selected | queried | loaded | used | unused | queried_not_loaded | loaded_not_applied
        for xid in all_xids:
            stat = xid_stats[xid]
            stat["run_count"] += 1
            stat["skill_ids"].add(skill_id)
            stat["available_count"] += xid in available
            stat["selected_count"] += xid in selected
            stat["queried_count"] += xid in queried
            stat["loaded_count"] += xid in loaded
            stat["used_count"] += xid in used
            stat["unused_count"] += xid in unused
            stat["queried_not_loaded_count"] += xid in queried_not_loaded
            stat["loaded_not_applied_count"] += xid in loaded_not_applied
            stat["run_paths"].append(_string(run.get("path")) or _string(run.get("name")))

    candidates = (
        _feedback_candidates(raw_runs, skill_stats, xid_stats, min_samples)
        + _split_candidates(skill_stats, min_samples)
        + _merge_candidates(skill_stats, min_samples)
        + _usage_gap_candidates(xid_stats, min_samples)
    )
    unique_candidates = {item["proposal_id"]: item for item in candidates}
    ordered_candidates = sorted(
        unique_candidates.values(),
        key=lambda item: (
            _CANDIDATE_ORDER.get(str(item["category"]), 99),
            -int(item["support"]),
            str(item["proposal_id"]),
        ),
    )[:max_candidates]

    configuration = {"min_samples": min_samples, "max_candidates": max_candidates}
    source = {
        "source_kind": "xrefkit_dashboard_json",
        "source_ref": source_ref,
        "source_hash": source_hash or hashlib.sha256(_canonical_json(payload)).hexdigest(),
    }
    report_basis = {"source": source, "configuration": configuration, "runs": raw_runs}
    return {
        "schema": SCHEMA,
        "analysis_id": f"analysis-{_short_hash(report_basis)}",
        "status": "proposal_only",
        "source": source,
        "configuration": configuration,
        "sample_count": len(raw_runs),
        "correlation": _correlation_counts(raw_runs),
        "summary": {
            "skills": len(skill_stats),
            "xids": len(xid_stats),
            "proposals": len(ordered_candidates),
            "runs_with_feedback": sum(1 for run in raw_runs if _feedback_events(run)),
            "runs_with_missing_information": sum(1 for run in raw_runs if _as_list(run.get("missing_information"))),
        },
        "proposals": ordered_candidates,
        "skill_usage": _serialize_skill_stats(skill_stats),
        "xid_usage": _serialize_xid_stats(xid_stats),
        "data_quality": {
            "audit_errors": [str(item) for item in _as_list(payload.get("audit_errors"))],
            "unknown_correlation_runs": sum(1 for run in raw_runs if _correlation_level(run) == "unknown"),
            "excluded_records": len(_as_list(payload.get("runs"))) - len(raw_runs),
        },
        "decision": {"status": "pending", "owner": None},
    }


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(report: dict[str, Any]) -> str:
    """Render a human-reviewable proposal report."""

    lines = [
        "# Boundary Analysis Report",
        "",
        "> Proposal-only output. This report does not change Skills, Knowledge, routing, or XIDs.",
        "",
        f"- analysis_id: `{_md(report.get('analysis_id'))}`",
        f"- status: `{_md(report.get('status'))}`",
        f"- sample_count: `{_md(report.get('sample_count'))}`",
        f"- source_hash: `{_md(_as_dict(report.get('source')).get('source_hash'))}`",
        f"- min_samples: `{_md(_as_dict(report.get('configuration')).get('min_samples'))}`",
        "",
        "## How to read this report",
        "",
        "Review the evidence and counterevidence before accepting a proposal. A split, merge, or correction candidate is not a canonical decision. Unknown correlation or missing task context lowers confidence and must remain visible.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in _as_dict(report.get("summary")).items():
        lines.append(f"| {_md(key)} | {_md(value)} |")
    lines.extend(
        [
            "",
            "## Correlation",
            "",
            "| Level | Runs |",
            "| --- | ---: |",
        ]
    )
    for key in _CORRELATION_LEVELS:
        lines.append(f"| `{key}` | {_md(_as_dict(report.get('correlation')).get(key, 0))} |")

    proposals = _as_list(report.get("proposals"))
    lines.extend(["", "## Proposals", ""])
    if not proposals:
        lines.append("No proposal reached the configured minimum sample support.")
    else:
        for index, raw in enumerate(proposals, start=1):
            proposal = _as_dict(raw)
            title = f"{index}. {_md(proposal.get('category'))}: {_md(proposal.get('proposal_id'))}"
            lines.extend(
                [
                    f"### {title}",
                    "",
                    f"- proposal: `{_md(proposal.get('proposal'))}`",
                    f"- support: `{_md(proposal.get('support'))}`",
                    f"- skills: `{_md(', '.join(str(item) for item in _as_list(proposal.get('skill_ids'))))}`",
                    f"- XIDs: `{_md(', '.join(str(item) for item in _as_list(proposal.get('subject_xids'))))}`",
                    f"- rationale: {_md(proposal.get('rationale'))}",
                    "",
                    "#### Evidence",
                    "",
                ]
            )
            evidence = _as_list(proposal.get("evidence_refs"))
            lines.extend([f"- `{_md(item)}`" for item in evidence] or ["- No evidence reference."])
            lines.extend(["", "#### Counterevidence", ""])
            lines.extend([f"- {_md(item)}" for item in _as_list(proposal.get("counterevidence"))] or ["- None recorded."])
            lines.extend(["", "#### Unknowns", ""])
            lines.extend([f"- {_md(item)}" for item in _as_list(proposal.get("unknowns"))] or ["- None recorded."])
            lines.extend(["", "#### Verification plan", ""])
            lines.extend([f"1. {_md(item)}" for item in _as_list(proposal.get("verification_plan"))] or ["1. Define a human verification plan."])

    lines.extend(["", "## Skill Usage", "", "| Skill | Runs | Closed | Blocked | Open | Feedback | XIDs |", "| --- | ---: | ---: | ---: | ---: | --- | --- |"])
    for row in _as_list(report.get("skill_usage")):
        item = _as_dict(row)
        feedback = ", ".join(f"{key}={value}" for key, value in _as_dict(item.get("feedback")).items()) or "none"
        lines.append(
            f"| `{_md(item.get('skill_id'))}` | {_md(item.get('run_count'))} | {_md(item.get('closed'))} | {_md(item.get('blocked'))} | {_md(item.get('open'))} | {_md(feedback)} | {_md(', '.join(str(value) for value in _as_list(item.get('xids'))))} |"
        )

    lines.extend(["", "## XID Usage", "", "| XID | Runs | Selected | Loaded | Used | Unused | Load/Application gaps |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for row in _as_list(report.get("xid_usage")):
        item = _as_dict(row)
        gap = int(item.get("queried_not_loaded_count", 0)) + int(item.get("loaded_not_applied_count", 0))
        lines.append(
            f"| `{_md(item.get('xid'))}` | {_md(item.get('run_count'))} | {_md(item.get('selected_count'))} | {_md(item.get('loaded_count'))} | {_md(item.get('used_count'))} | {_md(item.get('unused_count'))} | {_md(gap)} |"
        )

    quality = _as_dict(report.get("data_quality"))
    lines.extend(
        [
            "",
            "## Data Quality",
            "",
            f"- unknown correlation runs: `{_md(quality.get('unknown_correlation_runs', 0))}`",
            f"- excluded records: `{_md(quality.get('excluded_records', 0))}`",
            f"- audit errors: `{_md(len(_as_list(quality.get('audit_errors'))))}`",
            "",
            "## Decision",
            "",
            "The decision remains `pending` until an accountable human reviews the evidence, counterevidence, unknowns, and verification plan.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cmd_analysis_boundary_report(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    try:
        payload, source_hash = load_dashboard_json(input_path)
        report = analyze_dashboard_payload(
            payload,
            source_hash=source_hash,
            source_ref=str(input_path),
            min_samples=args.min_samples,
            max_candidates=args.max_candidates,
        )
    except ValueError as exc:
        print(f"fail: analysis boundary report: {exc}")
        return 1

    markdown = render_markdown(report)
    if args.out:
        _write_text(Path(args.out).resolve(), markdown)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.out:
        print(f"ok: {Path(args.out).resolve()}")
        print(f"  proposals: {len(_as_list(report.get('proposals')))}")
        print(f"  analysis_id: {report['analysis_id']}")
    else:
        print(markdown)
    return 0


def cmd_analysis(args: argparse.Namespace) -> int:
    if args.analysis_cmd == "boundary" and args.boundary_cmd == "report":
        return cmd_analysis_boundary_report(args)
    return 2
