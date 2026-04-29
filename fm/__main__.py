from __future__ import annotations

import argparse
import sys

from fm.xref import XrefConfig, cmd_xref


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fm", description="FileManager helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    xref = subparsers.add_parser("xref", help="Stable cross-file links by ID")
    xref_sub = xref.add_subparsers(dest="xref_cmd", required=True)

    def add_common_config(p: argparse.ArgumentParser) -> None:
        p.add_argument("--root", default=".", help="Project root (default: .)")
        p.add_argument(
            "--include",
            nargs="*",
            default=None,
            help="Top-level folders to include (default: docs agent knowledge)",
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

    skill = subparsers.add_parser("skill", help="Validate skill metadata before loading")
    skill_sub = skill.add_subparsers(dest="skill_cmd", required=True)

    p_skill_check = skill_sub.add_parser("check", help="Validate skill meta guard compliance")
    p_skill_check.add_argument("--root", default=".", help="Project root (default: .)")
    p_skill_check.add_argument("--meta", default=None, help="Relative path to a single meta.md to validate")
    p_skill_check.add_argument(
        "--scope",
        choices=["skills", "all"],
        default="skills",
        help="Validation scope when --meta is omitted (default: skills)",
    )
    p_skill_check.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_run = skill_sub.add_parser("run", help="Create a Skill runtime envelope and session log")
    p_skill_run.add_argument("--root", default=".", help="Project root (default: .)")
    p_skill_run.add_argument("--meta", required=True, help="Relative path to the Skill meta.md to run")
    p_skill_run.add_argument("--task", default=None, help="Task text for the Skill run")
    p_skill_run.add_argument("--task-file", default=None, help="Read task text from a UTF-8 file")
    p_skill_run.add_argument("--out", default=None, help="Write run log to this path")
    p_skill_run.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_phase = skill_sub.add_parser("phase", help="Update a Skill run log phase state")
    p_skill_phase.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_phase.add_argument(
        "--phase",
        required=True,
        choices=["startup", "planning", "execution", "check", "closure", "handoff"],
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
        help="Runtime role assigned by fm skill run; required for execution, check, and handoff phases",
    )
    p_skill_phase.add_argument("--json", action="store_true", help="Emit JSON")

    p_skill_workitem = skill_sub.add_parser("workitem", help="Add or update a concrete Skill work item")
    p_skill_workitem.add_argument("--log", required=True, help="Skill run log to update")
    p_skill_workitem.add_argument("--item", required=True, help="Stable work item id, such as WI-001")
    p_skill_workitem.add_argument("--text", default=None, help="Work item text; required when adding a new item")
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

    p_skill_close = skill_sub.add_parser("close", help="Apply the Skill run closure gate")
    p_skill_close.add_argument("--log", required=True, help="Skill run log to close")
    p_skill_close.add_argument("--note", default=None, help="Optional closure event note")
    p_skill_close.add_argument("--json", action="store_true", help="Emit JSON")

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

    if args.command == "ctx":
        from fm.ctx import cmd_ctx

        cfg = XrefConfig(
            root=args.root,
            include=args.include,
            exclude=args.exclude,
        )
        return cmd_ctx(args, cfg)

    if args.command == "skill":
        if args.skill_cmd == "run":
            from fm.skillrun import cmd_skill_run

            return cmd_skill_run(args)
        if args.skill_cmd == "phase":
            from fm.skillrun import cmd_skill_phase

            return cmd_skill_phase(args)
        if args.skill_cmd == "workitem":
            from fm.skillrun import cmd_skill_workitem

            return cmd_skill_workitem(args)
        if args.skill_cmd == "artifact":
            from fm.skillrun import cmd_skill_artifact

            return cmd_skill_artifact(args)
        if args.skill_cmd == "close":
            from fm.skillrun import cmd_skill_close

            return cmd_skill_close(args)

        from fm.skillmeta import cmd_skill

        return cmd_skill(args)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
