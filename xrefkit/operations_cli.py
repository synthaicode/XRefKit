from __future__ import annotations

import argparse
import json
import sys

from xrefkit.xref import XrefConfig, cmd_xref


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xrefkit", description="XRefKit control CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    xref = subparsers.add_parser("xref", help="Stable cross-file links by ID")
    xref_sub = xref.add_subparsers(dest="xref_cmd", required=True)

    def add_common_config(p: argparse.ArgumentParser) -> None:
        p.add_argument("--root", default=".", help="Project root (default: .)")
        p.add_argument(
            "--include",
            nargs="*",
            default=None,
            help="Top-level folders to include (default: docs agent knowledge capabilities skills packs tools)",
        )
        p.add_argument(
            "--exclude",
            nargs="*",
            default=None,
            help="Folder names to exclude (default: .git .xref node_modules .venv venv)",
        )

    p_init = xref_sub.add_parser("init", help="Add missing XIDs to markdown files")
    add_common_config(p_init)
    p_init.add_argument("--dry-run", action="store_true", help="Show changes only")

    p_check = xref_sub.add_parser("check", help="Validate XIDs and managed links")
    add_common_config(p_check)
    p_check.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_check.add_argument(
        "--review",
        action="store_true",
        help="Emit human review hints for XID-bearing docs (best-effort)",
    )

    p_rewrite = xref_sub.add_parser("rewrite", help="Rewrite managed links to correct paths")
    add_common_config(p_rewrite)
    p_rewrite.add_argument("--dry-run", action="store_true", help="Show changes only")

    p_fix = xref_sub.add_parser("fix", help="Run init + rewrite + check in one command")
    add_common_config(p_fix)
    p_fix.add_argument("--dry-run", action="store_true", help="Show changes only")
    p_fix.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_fix.add_argument(
        "--review",
        action="store_true",
        help="Include human review hints from check phase (best-effort)",
    )

    p_index = xref_sub.add_parser("index", help="Print XID -> path mapping")
    add_common_config(p_index)
    p_index.add_argument("--json", action="store_true", help="Emit JSON (default)")

    p_search = xref_sub.add_parser("search", help="Search docs and return matching XIDs")
    add_common_config(p_search)
    p_search.add_argument("query", help="Substring or /regex/ (case-insensitive)")
    p_search.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    p_search.add_argument("--json", action="store_true", help="Emit JSON")

    p_show = xref_sub.add_parser("show", help="Show a doc by XID (for on-demand context loading)")
    add_common_config(p_show)
    p_show.add_argument("xid", help="XID to show")
    p_show.add_argument("--max-bytes", type=int, default=20000, help="Truncate output (default: 20000)")
    p_show.add_argument("--json", action="store_true", help="Emit JSON")

    p_deprecate = xref_sub.add_parser(
        "deprecate",
        help="Mark an old XID doc as deprecated and link to its successor (best-effort)",
    )
    add_common_config(p_deprecate)
    p_deprecate.add_argument("old_xid", help="Deprecated XID (keep the page, add successor link)")
    p_deprecate.add_argument("new_xid", help="Successor XID (add predecessor link)")
    p_deprecate.add_argument("--note", default=None, help="Optional note to include (human-facing)")

    ctx = subparsers.add_parser("ctx", help="Build compact context packs")
    ctx_sub = ctx.add_subparsers(dest="ctx_cmd", required=True)

    p_pack = ctx_sub.add_parser("pack", help="Create a compact context pack from seed XIDs")
    add_common_config(p_pack)
    p_pack.add_argument("--seed", action="append", default=[], help="Seed XID (repeatable)")
    p_pack.add_argument("--depth", type=int, default=1, help="Link traversal depth (default: 1)")
    p_pack.add_argument("--max-bytes", type=int, default=40000, help="Max output size (default: 40000)")
    p_pack.add_argument("--per-doc-bytes", type=int, default=8000, help="Max bytes per doc extract (default: 8000)")
    p_pack.add_argument("--out", default=None, help="Write to file instead of stdout")
    p_pack.add_argument("--json", action="store_true", help="Emit JSON (and still write --out if set)")

    goal = subparsers.add_parser(
        "goal",
        help="Manage goal-mode continuation packets, wake state, and leases after semantic routing selected the goal_mode Skill",
    )
    goal_sub = goal.add_subparsers(dest="goal_cmd", required=True)

    p_goal_define = goal_sub.add_parser("define", help="Define desired state and acceptance conditions")
    p_goal_define.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_define.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_define.add_argument("--state", required=True, help="Desired realized state")
    p_goal_define.add_argument(
        "--acceptance", action="append", default=[], required=True,
        help="Acceptance condition as id:text; repeatable",
    )
    p_goal_define.add_argument("--owner", default=None, help="Goal acceptance owner")
    p_goal_define.add_argument("--json", action="store_true", help="Emit JSON")

    p_goal_show = goal_sub.add_parser("show", help="Show desired, observed, and acceptance state")
    p_goal_show.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_show.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_show.add_argument("--json", action="store_true", help="Emit JSON")

    p_goal_complete = goal_sub.add_parser("complete", help="Complete only with acceptance evidence")
    p_goal_complete.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_complete.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_complete.add_argument(
        "--evidence", action="append", default=[],
        help="Acceptance evidence as condition_id=reference; repeatable",
    )
    p_goal_complete.add_argument("--observed-state", required=True, help="Observed realized state")
    p_goal_complete.add_argument("--json", action="store_true", help="Emit JSON")

    p_goal_packet = goal_sub.add_parser("packet", help="Manage append-only continuation packets")
    p_goal_packet_sub = p_goal_packet.add_subparsers(dest="packet_cmd", required=True)

    p_goal_packet_append = p_goal_packet_sub.add_parser("append", help="Append one continuation packet")
    p_goal_packet_append.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_packet_append.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_packet_append.add_argument("--summary", required=True, help="Goal state summary")
    p_goal_packet_append.add_argument("--next-action", required=True, help="Exact next first action after resume")
    p_goal_packet_append.add_argument("--created-by", default=None, help="Optional packet author label")
    p_goal_packet_append.add_argument("--continuation-log", default=None, help="Continuation log path or reference")
    p_goal_packet_append.add_argument("--artifact", action="append", default=[], help="Artifact path or reference; repeatable")
    p_goal_packet_append.add_argument("--boundary", default=None, help="Current allowed continuation boundary")
    p_goal_packet_append.add_argument("--stop-condition", action="append", default=[], help="Stop condition; repeatable")
    p_goal_packet_append.add_argument("--drift-check", action="append", default=[], help="Drift-check point; repeatable")
    p_goal_packet_append.add_argument(
        "--status",
        choices=sorted({"valid", "superseded", "blocked", "cancelled"}),
        default="valid",
        help="Packet status (default: valid)",
    )
    p_goal_packet_append.add_argument("--source-run-key", default=None, help="Optional source run key")
    p_goal_packet_append.add_argument("--trace-id", default=None, help="Optional trace id")
    p_goal_packet_append.add_argument("--parent-packet", default=None, help="Optional parent packet id")
    p_goal_packet_append.add_argument("--subgoal", default=None, help="Optional subgoal id")
    p_goal_packet_append.add_argument("--resume-blocker", action="append", default=[], help="Resume blocker; repeatable")
    p_goal_packet_append.add_argument("--expiry-hint", default=None, help="Optional expiry hint")
    p_goal_packet_append.add_argument("--json", action="store_true", help="Emit JSON")

    p_goal_packet_latest = p_goal_packet_sub.add_parser("latest", help="Show the latest continuation packet")
    p_goal_packet_latest.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_packet_latest.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_packet_latest.add_argument("--valid-only", action="store_true", help="Return only the latest valid packet")
    p_goal_packet_latest.add_argument("--json", action="store_true", help="Emit JSON")

    p_goal_lease = goal_sub.add_parser("lease", help="Manage goal leases")
    p_goal_lease_sub = p_goal_lease.add_subparsers(dest="lease_cmd", required=True)

    p_goal_lease_acquire = p_goal_lease_sub.add_parser("acquire", help="Acquire the active lease for one goal")
    p_goal_lease_acquire.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_lease_acquire.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_lease_acquire.add_argument("--owner", required=True, help="Lease owner id")
    p_goal_lease_acquire.add_argument("--source-packet", default=None, help="Optional packet id; defaults to latest valid packet")
    p_goal_lease_acquire.add_argument("--ttl-hours", type=int, default=6, help="Lease duration in hours (default: 6)")
    p_goal_lease_acquire.add_argument("--json", action="store_true", help="Emit JSON")

    p_goal_lease_release = p_goal_lease_sub.add_parser("release", help="Release the active lease for one goal")
    p_goal_lease_release.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_lease_release.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_lease_release.add_argument("--owner", default=None, help="Lease owner id")
    p_goal_lease_release.add_argument("--force", action="store_true", help="Force release even if owner does not match")
    p_goal_lease_release.add_argument("--note", default=None, help="Optional release note")
    p_goal_lease_release.add_argument("--json", action="store_true", help="Emit JSON")

    p_goal_lease_show = p_goal_lease_sub.add_parser("show", help="Show the current lease state for one goal")
    p_goal_lease_show.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_lease_show.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_lease_show.add_argument("--json", action="store_true", help="Emit JSON")

    p_goal_wake = goal_sub.add_parser("wake", help="Manage goal wake observation state")
    p_goal_wake_sub = p_goal_wake.add_subparsers(dest="wake_cmd", required=True)

    p_goal_wake_observe = p_goal_wake_sub.add_parser("observe", help="Record one wakeup observation for a goal")
    p_goal_wake_observe.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_wake_observe.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_wake_observe.add_argument("--source", required=True, help="Observer id such as provider poller or dashboard")
    p_goal_wake_observe.add_argument(
        "--recovery-type",
        required=True,
        choices=sorted({"five_hour", "weekly", "unknown"}),
        help="Observed recovery type",
    )
    p_goal_wake_observe.add_argument("--note", default=None, help="Optional observation note")
    p_goal_wake_observe.add_argument("--json", action="store_true", help="Emit JSON")

    p_goal_wake_show = p_goal_wake_sub.add_parser("show", help="Show the current wake state for one goal")
    p_goal_wake_show.add_argument("--root", default=".", help="Project root (default: .)")
    p_goal_wake_show.add_argument("--goal", required=True, help="Stable goal id")
    p_goal_wake_show.add_argument("--json", action="store_true", help="Emit JSON")

    from xrefkit.decision_trace import add_trace_parser

    add_trace_parser(subparsers)

    gate = subparsers.add_parser(
        "gate",
        help="Agent diff review gate: deterministic, machine-only diff-content checks before CI",
    )
    gate_sub = gate.add_subparsers(dest="gate_cmd", required=True)

    p_gate_eval = gate_sub.add_parser(
        "eval",
        help="Run deterministic small evals over a diff and emit a pre-CI eval verdict",
    )
    p_gate_eval.add_argument("--root", default=".", help="Project root (default: .)")
    p_gate_eval.add_argument(
        "--diff",
        default=None,
        help="Unified diff file to inspect, or - for stdin; omit to use git diff",
    )
    p_gate_eval.add_argument("--base", default=None, help="git diff base ref (e.g. main); used when --diff is omitted")
    p_gate_eval.add_argument("--staged", action="store_true", help="Inspect staged changes (git diff --cached)")
    p_gate_eval.add_argument(
        "--scope",
        nargs="*",
        default=None,
        help="Declared change-scope globs; files outside are flagged out_of_scope",
    )
    p_gate_eval.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_gate_eval.add_argument(
        "--profile",
        default=None,
        choices=["command-cutover-readiness"],
        help="Run a named repository readiness profile instead of diff checks",
    )

    pack = subparsers.add_parser("pack", help="Validate Business Pack manifests (pack.md)")
    pack_sub = pack.add_subparsers(dest="pack_cmd", required=True)

    p_pack_lint = pack_sub.add_parser(
        "lint",
        help="Validate pack manifests: ownership, OS-core contract version, asset resolution, boundary",
    )
    p_pack_lint.add_argument("--root", default=".", help="Project root (default: .)")
    p_pack_lint.add_argument(
        "--manifest",
        default=None,
        help="Relative path to a single pack.md to validate (default: all skills/packs/*/pack.md and packs/*/pack.md)",
    )
    p_pack_lint.add_argument("--json", action="store_true", help="Emit JSON")

    p_pack_list = pack_sub.add_parser(
        "list",
        help="List Business Packs (pack_id, summary, owned skills) derived from manifests for job-first routing",
    )
    p_pack_list.add_argument("--root", default=".", help="Project root (default: .)")
    p_pack_list.add_argument("--json", action="store_true", help="Emit JSON")

    dashboard = subparsers.add_parser(
        "dashboard",
        help="Observe Skill run logs through a local Python dashboard",
    )
    dashboard_sub = dashboard.add_subparsers(dest="dashboard_cmd", required=True)

    p_dashboard_serve = dashboard_sub.add_parser("serve", help="Serve the Skill Run Observation Dashboard")
    p_dashboard_serve.add_argument("--root", default=".", help="Project root (default: .)")
    p_dashboard_serve.add_argument(
        "--sessions-dir",
        default=None,
        help="Session log directory; defaults to <root>/work/sessions",
    )
    p_dashboard_serve.add_argument(
        "--mcp-audit-log",
        default=None,
        help="MCP audit JSONL; defaults to <root>/work/mcp/xid_audit.jsonl",
    )
    p_dashboard_serve.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    p_dashboard_serve.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765)")
    p_dashboard_serve.add_argument("--open-browser", action="store_true", help="Open the dashboard in a browser")

    p_dashboard_data = dashboard_sub.add_parser("data", help="Emit dashboard data as JSON")
    p_dashboard_data.add_argument("--root", default=".", help="Project root (default: .)")
    p_dashboard_data.add_argument(
        "--sessions-dir",
        default=None,
        help="Session log directory; defaults to <root>/work/sessions",
    )
    p_dashboard_data.add_argument(
        "--mcp-audit-log",
        default=None,
        help="MCP audit JSONL; defaults to <root>/work/mcp/xid_audit.jsonl",
    )

    analysis = subparsers.add_parser(
        "analysis",
        help="Generate proposal-only analysis reports from observed runtime data",
    )
    analysis_sub = analysis.add_subparsers(dest="analysis_cmd", required=True)
    boundary = analysis_sub.add_parser(
        "boundary",
        help="Analyze Skill and Knowledge boundary evidence",
    )
    boundary_sub = boundary.add_subparsers(dest="boundary_cmd", required=True)
    p_boundary_report = boundary_sub.add_parser(
        "report",
        help="Create a proposal-only boundary report from dashboard JSON",
    )
    p_boundary_report.add_argument(
        "--input",
        required=True,
        help="Dashboard JSON emitted by `xrefkit dashboard data`",
    )
    p_boundary_report.add_argument(
        "--out",
        default=None,
        help="Write the Markdown report to this path",
    )
    p_boundary_report.add_argument(
        "--min-samples",
        type=int,
        default=2,
        help="Minimum repeated support for a proposal (default: 2)",
    )
    p_boundary_report.add_argument(
        "--max-candidates",
        type=int,
        default=20,
        help="Maximum candidates in the report (default: 20)",
    )
    p_boundary_report.add_argument("--json", action="store_true", help="Emit the report as JSON")

    skill = subparsers.add_parser("skill", help="Validate skill metadata before loading")
    skill_sub = skill.add_subparsers(dest="skill_cmd", required=True)

    p_skill_import = skill_sub.add_parser(
        "import",
        help="Import an external file-based Skill into XRefKit Skill + Knowledge files",
    )
    p_skill_import.add_argument("source_dir", help="External Skill directory or batch root")
    p_skill_import.add_argument("--root", default=".", help="Project root (default: .)")
    p_skill_import.add_argument("--skill-id", help="Target XRefKit skill id")
    p_skill_import.add_argument("--batch", action="store_true", help="Treat source_dir as a root containing skills/ and knowledge/")
    p_skill_import.add_argument("--skill-id-prefix", default=None, help="Prefix for generated skill ids in --batch mode")
    p_skill_import.add_argument("--source-skill-doc", default=None, help="Source skill document path relative to source_dir")
    p_skill_import.add_argument("--target-skill-dir", default=None, help="Target Skill directory")
    p_skill_import.add_argument("--target-skill-root", default=None, help="Batch target Skill root")
    p_skill_import.add_argument("--target-knowledge-dir", default=None, help="Target Knowledge directory")
    p_skill_import.add_argument("--dry-run", action="store_true", help="Show planned output without writing files")
    p_skill_import.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_check = skill_sub.add_parser("check", help="Validate skill meta guard compliance")
    p_skill_check.add_argument("--root", default=".", help="Project root (default: .)")
    p_skill_check.add_argument("--meta", default=None, help="Relative path to a single meta.md to validate")
    p_skill_check.add_argument(
        "--scope",
        choices=["skills", "all"],
        default="skills",
        help="Validation scope when --meta is omitted (default: skills)",
    )
    p_skill_check.add_argument(
        "--level",
        choices=["auto", "draft", "trial", "stable", "governed"],
        default="auto",
        help="Validation level; auto uses declared maturity/status (default: auto)",
    )
    p_skill_check.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_list = skill_sub.add_parser(
        "list",
        help="List skills with publication boundary (public/private) and detect private-leak violations",
    )
    p_skill_list.add_argument("--root", default=".", help="Project root (default: .)")
    p_skill_list.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_index = skill_sub.add_parser(
        "index",
        help="Generate skills/_index.md from catalog-visible skill metadata",
    )
    p_skill_index.add_argument("--root", default=".", help="Project root (default: .)")
    p_skill_index.add_argument("--write", action="store_true", help="Write skills/_index.md instead of printing")
    p_skill_index.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_merge_plan = skill_sub.add_parser(
        "merge-plan",
        help="Create a deterministic report for importing an older Skill asset",
    )
    p_skill_merge_plan.add_argument("--root", default=".", help="Project root (default: .)")
    p_skill_merge_plan.add_argument("--source", required=True, help="Source Skill folder or import bundle")
    p_skill_merge_plan.add_argument("--target-skill", default=None, help="Optional intended current target skill_id")
    p_skill_merge_plan.add_argument("--source-version", default=None, help="Optional source version label")
    p_skill_merge_plan.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_run = skill_sub.add_parser("run", help="Create a Skill runtime envelope and session log")
    p_skill_run.add_argument("--root", default=".", help="Project root (default: .)")
    p_skill_run.add_argument("--meta", required=True, help="Relative path to the Skill meta.md to run")
    p_skill_run.add_argument("--task", default=None, help="Task text for the Skill run")
    p_skill_run.add_argument("--task-file", default=None, help="Read task text from a UTF-8 file")
    p_skill_run.add_argument("--out", default=None, help="Write run log to this path")
    p_skill_run.add_argument("--run-id", default=None, help="Caller-supplied UUID used to correlate MCP and client logs")
    p_skill_run.add_argument("--flow-id", default=None, help="Prompt Flow ID shared with a parent workflow")
    p_skill_run.add_argument("--root-run-id", default=None, help="Root run ID of the Prompt Flow")
    p_skill_run.add_argument("--parent-run-id", default=None, help="Parent run ID for delegated Skill work")
    p_skill_run.add_argument("--work-item-id", default=None, help="Parent work item ID represented by this Skill Run")
    p_skill_run.add_argument("--node-id", default=None, help="Prompt Flow node ID for Dashboard traceability")
    p_skill_run.add_argument(
        "--domain-knowledge-catalog",
        default=None,
        help="JSON fixture/catalog of available domain knowledge metadata for this run",
    )
    p_skill_run.add_argument(
        "--knowledge-input",
        action="append",
        default=[],
        help="Selected domain knowledge input as name=XID[,XID]; may be repeated",
    )
    p_skill_run.add_argument(
        "--handoff-source-log",
        action="append",
        default=[],
        help="Prior Skill run log that handed work into this startup; may be repeated",
    )
    p_skill_run.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_correlate = skill_sub.add_parser("correlate", help="Bind a Skill run log to its MCP session")
    p_skill_correlate.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_correlate.add_argument("--run-id", default=None, help="Expected run_id returned by bind_skill_run")
    p_skill_correlate.add_argument("--mcp-session-id", required=True, help="MCP session ID returned by bind_skill_run")
    p_skill_correlate.add_argument(
        "--repository-fingerprint",
        required=True,
        help="Repository fingerprint returned by bind_skill_run",
    )
    p_skill_correlate.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_routing = skill_sub.add_parser("routing", help="Record Skill routing candidates and selection evidence")
    p_skill_routing.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_routing.add_argument("--selected-skill", default=None, help="Selected Skill ID; omit when selection-mode=needs_clarification")
    p_skill_routing.add_argument("--candidate", action="append", default=[], help="Candidate Skill ID; repeatable")
    p_skill_routing.add_argument(
        "--selection-mode",
        choices=["semantic", "explicit", "handoff", "fallback", "quality_review", "needs_clarification"],
        default="semantic",
        help="Routing decision mode",
    )
    p_skill_routing.add_argument("--reason", required=True, help="Evidence-bound selection reason")
    p_skill_routing.add_argument("--target-work-item", default=None, help="Work item receiving the routing decision")
    p_skill_routing.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_knowledge = skill_sub.add_parser("knowledge", help="Record Knowledge search, load, or application evidence")
    p_skill_knowledge.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_knowledge.add_argument("--action", required=True, choices=["search", "load", "apply"])
    p_skill_knowledge.add_argument("--query", default=None, help="Search query for action=search")
    p_skill_knowledge.add_argument("--xid", action="append", default=[], help="Knowledge XID; repeatable for search results")
    p_skill_knowledge.add_argument("--content-hash", default=None, help="Document content hash for action=load or action=apply")
    p_skill_knowledge.add_argument(
        "--status",
        choices=["hit", "miss", "fallback"],
        default="hit",
        help="Search result for action=search",
    )
    p_skill_knowledge.add_argument("--source", default="client", help="Observation source such as mcp or filesystem")
    p_skill_knowledge.add_argument("--target", default=None, help="Judgment or artifact target for action=apply")
    p_skill_knowledge.add_argument("--decisive", action="store_true", help="Mark the XID as decision-changing evidence")
    p_skill_knowledge.add_argument("--note", default=None, help="Optional observation note")
    p_skill_knowledge.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_feedback = skill_sub.add_parser("feedback", help="Record human or downstream outcome feedback")
    p_skill_feedback.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_feedback.add_argument("--kind", required=True, choices=["human", "outcome"])
    p_skill_feedback.add_argument(
        "--status",
        required=True,
        choices=["accepted", "corrected", "rejected", "successful", "failed", "mixed", "unknown"],
    )
    p_skill_feedback.add_argument("--target", default=None, help="Feedback target artifact, judgment, or deployment")
    p_skill_feedback.add_argument("--note", required=True, help="Observed feedback or outcome")
    p_skill_feedback.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_evaluate = skill_sub.add_parser(
        "evaluate",
        help="Optionally record a human-confirmed evaluation and next-request relationship for a closed run",
    )
    p_skill_evaluate.add_argument("--log", required=True, help="Completed preceding run log to update")
    p_skill_evaluate.add_argument("--decision", required=True, choices=[
        "accepted", "accepted_with_conditions", "correction",
        "rejected_or_returned_to_human", "needs_clarification",
    ])
    p_skill_evaluate.add_argument("--classification", required=True, choices=[
        "continuation", "correction", "scope_change", "new_work", "needs_clarification",
    ], help="Human-confirmed relationship of the subsequent request to the preceding run")
    p_skill_evaluate.add_argument("--next-handling", required=True, choices=[
        "continue_next_step", "repair_previous_run", "human_takeover",
    ])
    p_skill_evaluate.add_argument("--purpose-fit", required=True, help="Human-stated fit to the preceding purpose/intent")
    p_skill_evaluate.add_argument("--verified", action="append", default=[], help="Verified artifact/check basis; repeatable, or use 'none'")
    p_skill_evaluate.add_argument("--uncertainty", action="append", default=[], help="Remaining uncertainty/risk; repeatable, or use 'none'")
    p_skill_evaluate.add_argument("--carry-forward", action="append", default=[], help="Constraint or added context for the next run; repeatable")
    p_skill_evaluate.add_argument("--link", action="append", default=[], help="Preceding artifact, check, or evidence link; repeatable")
    p_skill_evaluate.add_argument("--scope-finding", action="append", default=[], help="Scoped finding as TARGET|DECISION|NOTE; repeatable")
    p_skill_evaluate.add_argument("--scope-link", action="append", default=[], help="Scoped evidence link as TARGET|LINK; repeatable")
    p_skill_evaluate.add_argument("--proposed-classification", choices=[
        "continuation", "correction", "scope_change", "new_work", "needs_clarification",
    ], help="Optional AI proposal; --classification remains human-confirmed")
    p_skill_evaluate.add_argument("--reviewer", default=None, help="Optional human reviewer identifier")
    p_skill_evaluate.add_argument("--evaluated-at", default=None, help="Optional ISO-8601 evaluation timestamp")
    p_skill_evaluate.add_argument("--context-ref", action="append", default=[], help="Versioned/declarative prior-run context reference; repeatable")
    p_skill_evaluate.add_argument("--comparability", choices=["comparable", "gap", "not_assessed"], default="not_assessed")
    p_skill_evaluate.add_argument("--comparability-gap", action="append", default=[], help="Why prior and current evidence/criteria are not comparable; repeatable")
    p_skill_evaluate.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_phase = skill_sub.add_parser("phase", help="Update a Skill run log phase state")
    p_skill_phase.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_phase.add_argument(
        "--phase",
        required=True,
        choices=["startup", "planning", "execution", "check", "quality", "closure", "handoff"],
        help="Phase to update",
    )
    p_skill_phase.add_argument(
        "--status",
        required=True,
        choices=["pending", "in_progress", "done", "blocked", "unknown", "escalated"],
        help="Phase status",
    )
    p_skill_phase.add_argument("--note", default=None, help="Optional phase event note")
    p_skill_phase.add_argument(
        "--role",
        default=None,
        help="Runtime role assigned by xrefkit skill run; required for execution, check, and handoff phases",
    )
    p_skill_phase.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_workitem = skill_sub.add_parser("workitem", help="Add or update a concrete Skill work item")
    p_skill_workitem.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_workitem.add_argument("--item", required=True, help="Stable work item id, such as WI-001")
    p_skill_workitem.add_argument("--text", default=None, help="Work item text; required when adding a new item")
    p_skill_workitem.add_argument("--completion-criterion", default=None, help="Observable procedural condition for this work item")
    p_skill_workitem.add_argument("--criterion-unknown-reason", default=None, help="Why the completion criterion cannot yet be defined for unknown/blocked/escalated work")
    p_skill_workitem.add_argument("--supersedes", default=None, help="Existing work item whose criterion is being replaced by this new item")
    p_skill_workitem.add_argument(
        "--status",
        required=True,
        choices=["pending", "in_progress", "done", "blocked", "unknown", "escalated"],
        help="Work item status",
    )
    p_skill_workitem.add_argument("--role", required=True, help="Runtime role updating the work item")
    p_skill_workitem.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_artifact = skill_sub.add_parser("artifact", help="Add or update a Skill runtime artifact/evidence link")
    p_skill_artifact.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_artifact.add_argument("--artifact", required=True, help="Stable artifact id, such as OUT-001")
    p_skill_artifact.add_argument(
        "--kind",
        required=True,
        choices=["output", "evidence", "check", "judgment", "source", "handoff"],
        help="Artifact kind",
    )
    p_skill_artifact.add_argument(
        "--status",
        required=True,
        choices=["pending", "in_progress", "done", "blocked", "unknown", "escalated"],
        help="Artifact status",
    )
    p_skill_artifact.add_argument("--target", default=None, help="Path, XID, command, URL, or other trace target")
    p_skill_artifact.add_argument("--item", default=None, help="Optional related concrete work item id")
    p_skill_artifact.add_argument("--role", required=True, help="Runtime role updating the artifact")
    p_skill_artifact.add_argument("--note", default=None, help="Optional artifact note")
    p_skill_artifact.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_concern = skill_sub.add_parser("concern", help="Add or update unknown, risk, or judgment closure linkage")
    p_skill_concern.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_concern.add_argument("--concern", required=True, help="Stable concern id, such as UNK-001")
    p_skill_concern.add_argument(
        "--kind",
        required=True,
        choices=["unknown", "risk", "judgment"],
        help="Concern kind",
    )
    p_skill_concern.add_argument(
        "--status",
        required=True,
        choices=["open", "resolved", "escalated"],
        help="Concern status",
    )
    p_skill_concern.add_argument(
        "--judgment",
        default="trivial",
        choices=["trivial", "non_trivial"],
        help="Judgment significance; only non_trivial judgments require artifact/reference linkage",
    )
    p_skill_concern.add_argument("--target", default=None, help="Optional path, XID, command, URL, or judgment reference")
    p_skill_concern.add_argument("--text", default=None, help="Concern text; required when adding a new concern")
    p_skill_concern.add_argument("--role", required=True, help="Runtime role recording the concern")
    p_skill_concern.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_tokens = skill_sub.add_parser("tokens", help="Record token usage consumed by a Skill run")
    p_skill_tokens.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_tokens.add_argument("--input", type=int, default=None, help="Input (prompt) tokens consumed")
    p_skill_tokens.add_argument("--output", type=int, default=None, help="Output (completion) tokens consumed")
    p_skill_tokens.add_argument("--total", type=int, default=None, help="Total tokens; defaults to input + output")
    p_skill_tokens.add_argument("--note", default=None, help="Optional token usage note")
    p_skill_tokens.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_close = skill_sub.add_parser("close", help="Apply the Skill run closure gate")
    p_skill_close.add_argument("--log", required=True, help="Skill run log to close")
    p_skill_close.add_argument("--note", default=None, help="Optional closure event note")
    p_skill_close.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_verify = skill_sub.add_parser(
        "verify",
        help="Deterministically verify workflow progression and advance the check phase",
    )
    p_skill_verify.add_argument("--log", required=True, help="Skill run log to verify")
    p_skill_verify.add_argument("--note", default=None, help="Optional check event note")
    p_skill_verify.add_argument("--json", action="store_true", help="Emit JSON")

    workflow = subparsers.add_parser(
        "workflow",
        help="Run the generic workflow protocol for an instruction without a Skill",
    )
    workflow_sub = workflow.add_subparsers(dest="workflow_cmd", required=True)

    host = subparsers.add_parser("host", help="Run host-compatibility evidence checks")
    host_sub = host.add_subparsers(dest="host_cmd", required=True)
    p_host_precheck = host_sub.add_parser(
        "precheck", help="Evaluate repeatable, observable Skill-routing compatibility evidence"
    )
    p_host_precheck.add_argument("--input", required=True, help="UTF-8 JSON pre-check input")
    p_host_precheck.add_argument("--out", default=None, help="Optional JSON report path")
    p_workflow_run = workflow_sub.add_parser(
        "run",
        help="Open an instruction- or general-Skill-backed workflow run",
    )
    p_workflow_run.add_argument("--root", default=".", help="Project root (default: .)")
    p_workflow_run.add_argument("--work-type", choices=["instruction", "general_skill"], default="instruction", help="Protocol input type (default: instruction)")
    p_workflow_run.add_argument("--task", default=None, help="Instruction text")
    p_workflow_run.add_argument("--task-file", default=None, help="Read instruction text from a UTF-8 file")
    p_workflow_run.add_argument("--skill-source", default=None, help="Local path for an ordinary Skill when --work-type general_skill is selected")
    p_workflow_run.add_argument("--out", default=None, help="Write workflow run log to this path")
    p_workflow_run.add_argument("--run-id", default=None, help="Caller-supplied UUID")
    p_workflow_run.add_argument("--flow-id", default=None, help="Prompt Flow ID; defaults to the root run ID")
    p_workflow_run.add_argument("--root-run-id", default=None, help="Root run ID of the Prompt Flow")
    p_workflow_run.add_argument("--parent-run-id", default=None, help="Parent run ID when this is a nested workflow")
    p_workflow_run.add_argument("--work-item-id", default=None, help="Parent work item ID represented by this workflow")
    p_workflow_run.add_argument("--node-id", default=None, help="Prompt Flow node ID for Dashboard traceability")
    p_workflow_run.add_argument("--purpose", default=None, help="Prompt purpose; omitted values are recorded as unknown")
    p_workflow_run.add_argument("--scope-in", action="append", default=[], help="In-scope boundary; repeatable")
    p_workflow_run.add_argument("--scope-out", action="append", default=[], help="Out-of-scope boundary; repeatable")
    p_workflow_run.add_argument("--owner", default=None, help="Accountable owner; omitted values are recorded as unknown")
    p_workflow_run.add_argument("--authority", default=None, help="Authority or approval boundary")
    p_workflow_run.add_argument("--expected-evidence", action="append", default=[], help="Expected evidence; repeatable")
    p_workflow_run.add_argument("--stop-condition", action="append", default=[], help="Stop or clarification condition; repeatable")
    p_workflow_run.add_argument(
        "--completion-condition",
        action="append",
        default=[],
        help="Explicit procedural completion condition; may be repeated",
    )
    p_workflow_run.add_argument(
        "--use-default-completion-conditions",
        action="store_true",
        help="Use the repository's procedural completion conditions when the instruction omits them",
    )
    p_workflow_run.add_argument("--json", action="store_true", help="Emit JSON")

    p_workflow_routing = workflow_sub.add_parser(
        "routing",
        help="Record the main AI semantic routing decision for a Prompt Flow",
    )
    p_workflow_routing.add_argument("--log", required=True, help="Parent Prompt Flow run log")
    p_workflow_routing.add_argument("--selected-skill", default=None, help="Skill selected by the main AI")
    p_workflow_routing.add_argument("--candidate", action="append", default=[], help="Candidate Skill ID; repeatable")
    p_workflow_routing.add_argument(
        "--selection-mode",
        choices=["semantic", "explicit", "fallback", "needs_clarification"],
        default="semantic",
        help="Routing decision mode",
    )
    p_workflow_routing.add_argument("--reason", required=True, help="Evidence-bound routing reason")
    p_workflow_routing.add_argument("--target-work-item", default=None, help="Work item receiving the routing decision")
    p_workflow_routing.add_argument("--json", action="store_true", help="Emit JSON")

    p_workflow_delegate = workflow_sub.add_parser(
        "delegate",
        help="Start a child Skill Run for one parent workflow work item",
    )
    p_workflow_delegate.add_argument("--root", default=".", help="Project root (default: .)")
    p_workflow_delegate.add_argument("--parent-log", required=True, help="Parent Prompt Flow run log")
    p_workflow_delegate.add_argument("--meta", required=True, help="Relative path to the delegated Skill meta.md")
    p_workflow_delegate.add_argument("--task", default=None, help="Child Skill task text")
    p_workflow_delegate.add_argument("--task-file", default=None, help="Read child task text from a UTF-8 file")
    p_workflow_delegate.add_argument("--out", default=None, help="Write child Skill run log to this path")
    p_workflow_delegate.add_argument("--run-id", default=None, help="Caller-supplied child run UUID")
    p_workflow_delegate.add_argument("--work-item-id", required=True, help="Parent work item delegated to the child Skill")
    p_workflow_delegate.add_argument("--node-id", default=None, help="Prompt Flow node ID")
    p_workflow_delegate.add_argument("--json", action="store_true", help="Emit JSON")

    p_workflow_quality = workflow_sub.add_parser(
        "quality-review",
        help="Record main-AI quality Skill routing and start the selected child Skill",
    )
    p_workflow_quality.add_argument("--root", default=".", help="Project root (default: .)")
    p_workflow_quality.add_argument("--parent-log", required=True, help="Parent Prompt Flow run log")
    p_workflow_quality.add_argument("--meta", required=True, help="Selected quality review Skill meta.md")
    p_workflow_quality.add_argument("--selected-skill", required=True, help="Skill selected by the main AI")
    p_workflow_quality.add_argument("--candidate", action="append", required=True, help="Candidate Skill ID; repeatable")
    p_workflow_quality.add_argument("--reason", required=True, help="Evidence-bound selection reason")
    p_workflow_quality.add_argument("--task", default=None, help="Quality review task")
    p_workflow_quality.add_argument("--task-file", default=None, help="Read quality review task from a UTF-8 file")
    p_workflow_quality.add_argument("--out", default=None, help="Write child Skill run log to this path")
    p_workflow_quality.add_argument("--run-id", default=None, help="Caller-supplied child run UUID")
    p_workflow_quality.add_argument("--work-item-id", required=True, help="Parent work item under review")
    p_workflow_quality.add_argument("--node-id", default=None, help="Prompt Flow node ID")
    p_workflow_quality.add_argument("--json", action="store_true", help="Emit JSON")

    p_workflow_recovery = workflow_sub.add_parser(
        "recovery",
        help="Record a bounded recovery proposal or human-confirmed resume",
    )
    p_workflow_recovery.add_argument("--log", required=True, help="Prompt Flow or Skill Run log")
    p_workflow_recovery.add_argument("--recovery-id", required=True, help="Stable recovery proposal ID")
    p_workflow_recovery.add_argument("--status", required=True, choices=["proposed", "confirmed"], help="Proposal state")
    p_workflow_recovery.add_argument("--resume-location", required=True, help="Where execution should resume")
    p_workflow_recovery.add_argument("--reason", required=True, help="Why recovery is needed")
    p_workflow_recovery.add_argument("--next-action", required=True, help="Next executable action after confirmation")
    p_workflow_recovery.add_argument("--executable-action", default=None, help="Bounded action to execute after human confirmation")
    p_workflow_recovery.add_argument("--owner", default=None, help="Recovery owner")
    p_workflow_recovery.add_argument("--verification-method", default=None, help="How the resumed result will be verified")
    p_workflow_recovery.add_argument("--maximum-attempts", type=int, default=None, help="Maximum permitted recovery attempts")
    p_workflow_recovery.add_argument("--stop-condition", action="append", default=[], help="Recovery stop condition; repeatable")
    p_workflow_recovery.add_argument("--reviewer", default=None, help="Human reviewer confirming the resume")
    p_workflow_recovery.add_argument("--json", action="store_true", help="Emit JSON")

    p_workflow_reconcile = workflow_sub.add_parser(
        "reconcile",
        help="Reconcile a parent Prompt Flow with its delegated child Skill Runs",
    )
    p_workflow_reconcile.add_argument("--log", required=True, help="Parent Prompt Flow run log")
    p_workflow_reconcile.add_argument(
        "--apply-child-status",
        action="store_true",
        help="Reflect closed child status on the linked parent work item; does not execute work",
    )
    p_workflow_reconcile.add_argument("--json", action="store_true", help="Emit JSON")

    mcp = subparsers.add_parser(
        "mcp",
        help="Client-side MCP initialization helpers",
    )
    mcp_sub = mcp.add_subparsers(dest="mcp_cmd", required=True)
    p_mcp_flow_init = mcp_sub.add_parser(
        "flow-init",
        help="Initialize a Prompt Flow from a saved MCP startup context",
    )
    p_mcp_flow_init.add_argument("--startup-context", required=True, help="Saved get_startup_context JSON")
    prompt_group = p_mcp_flow_init.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="Prompt text; it is hashed, not stored in the audit")
    prompt_group.add_argument("--prompt-file", help="UTF-8 file containing the prompt")
    p_mcp_flow_init.add_argument("--cache-root", default=".xrefkit/mcp-cache", help="Client cache root")
    p_mcp_flow_init.add_argument("--repository-fingerprint", required=True, help="MCP repository fingerprint")
    p_mcp_flow_init.add_argument("--flow-id", default=None, help="Optional caller-supplied Flow ID")
    p_mcp_flow_init.add_argument("--root-run-id", default=None, help="Optional root run UUID")
    p_mcp_flow_init.add_argument("--json", action="store_true", help="Emit JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "xref":
        cfg = XrefConfig(
            root=args.root,
            include=args.include,
            exclude=args.exclude,
        )
        return cmd_xref(args, cfg)

    if args.command == "host" and args.host_cmd == "precheck":
        from xrefkit.host_precheck import cmd_host_precheck

        return cmd_host_precheck(args)

    if args.command == "ctx":
        from xrefkit.ctx import cmd_ctx

        cfg = XrefConfig(
            root=args.root,
            include=args.include,
            exclude=args.exclude,
        )
        return cmd_ctx(args, cfg)

    if args.command == "skill":
        if args.skill_cmd == "import":
            from xrefkit.import_skill import cmd_skill_import

            return cmd_skill_import(args)
        if args.skill_cmd == "list":
            from xrefkit.skillmeta import cmd_skill_list

            return cmd_skill_list(args)
        if args.skill_cmd == "index":
            from xrefkit.skillmeta import cmd_skill_index

            return cmd_skill_index(args)
        if args.skill_cmd == "merge-plan":
            from xrefkit.skillmeta import cmd_skill_merge_plan

            return cmd_skill_merge_plan(args)
        if args.skill_cmd == "run":
            from xrefkit.skillrun import cmd_skill_run

            return cmd_skill_run(args)
        if args.skill_cmd == "correlate":
            from xrefkit.skillrun import cmd_skill_correlate

            return cmd_skill_correlate(args)
        if args.skill_cmd == "routing":
            from xrefkit.skillrun import cmd_skill_routing

            return cmd_skill_routing(args)
        if args.skill_cmd == "knowledge":
            from xrefkit.skillrun import cmd_skill_knowledge

            return cmd_skill_knowledge(args)
        if args.skill_cmd == "feedback":
            from xrefkit.skillrun import cmd_skill_feedback

            return cmd_skill_feedback(args)
        if args.skill_cmd == "evaluate":
            from xrefkit.skillrun import cmd_skill_evaluate

            return cmd_skill_evaluate(args)
        if args.skill_cmd == "phase":
            from xrefkit.skillrun import cmd_skill_phase

            return cmd_skill_phase(args)
        if args.skill_cmd == "workitem":
            from xrefkit.skillrun import cmd_skill_workitem

            return cmd_skill_workitem(args)
        if args.skill_cmd == "artifact":
            from xrefkit.skillrun import cmd_skill_artifact

            return cmd_skill_artifact(args)
        if args.skill_cmd == "concern":
            from xrefkit.skillrun import cmd_skill_concern

            return cmd_skill_concern(args)
        if args.skill_cmd == "tokens":
            from xrefkit.skillrun import cmd_skill_tokens

            return cmd_skill_tokens(args)
        if args.skill_cmd == "close":
            from xrefkit.skillrun import cmd_skill_close

            return cmd_skill_close(args)
        if args.skill_cmd == "verify":
            from xrefkit.skillrun import cmd_skill_verify

            return cmd_skill_verify(args)

        from xrefkit.skillmeta import cmd_skill

        return cmd_skill(args)

    if args.command == "workflow":
        if args.workflow_cmd == "run":
            from xrefkit.skillrun import cmd_workflow_run

            return cmd_workflow_run(args)
        if args.workflow_cmd == "routing":
            from xrefkit.skillrun import cmd_workflow_routing

            return cmd_workflow_routing(args)
        if args.workflow_cmd == "delegate":
            from xrefkit.skillrun import cmd_workflow_delegate

            return cmd_workflow_delegate(args)
        if args.workflow_cmd == "quality-review":
            from xrefkit.skillrun import cmd_workflow_quality_review

            return cmd_workflow_quality_review(args)
        if args.workflow_cmd == "recovery":
            from xrefkit.skillrun import cmd_workflow_recovery

            return cmd_workflow_recovery(args)
        if args.workflow_cmd == "reconcile":
            from xrefkit.skillrun import cmd_workflow_reconcile

            return cmd_workflow_reconcile(args)

    if args.command == "mcp":
        if args.mcp_cmd == "flow-init":
            from pathlib import Path

            from xrefkit.mcp.client_flow import initialize_prompt_flow_from_file

            prompt = args.prompt
            if args.prompt_file:
                prompt = Path(args.prompt_file).read_text(encoding="utf-8")
            payload = initialize_prompt_flow_from_file(
                args.startup_context,
                prompt or "",
                cache_root=args.cache_root,
                repository_fingerprint=args.repository_fingerprint,
                flow_id=args.flow_id,
                root_run_id=args.root_run_id,
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

    if args.command == "pack":
        if args.pack_cmd == "list":
            from xrefkit.packmeta import cmd_pack_list

            return cmd_pack_list(args)

        from xrefkit.packmeta import cmd_pack_lint

        return cmd_pack_lint(args)

    if args.command == "dashboard":
        from xrefkit.dashboard import cmd_dashboard

        return cmd_dashboard(args)

    if args.command == "analysis":
        from xrefkit.boundary_analysis import cmd_analysis

        return cmd_analysis(args)

    if args.command == "gate":
        from xrefkit.gate import cmd_gate

        return cmd_gate(args)

    if args.command == "goal":
        from xrefkit.goalstate import cmd_goal

        return cmd_goal(args)

    if args.command == "trace":
        from xrefkit.decision_trace import cmd_trace

        return cmd_trace(args)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
