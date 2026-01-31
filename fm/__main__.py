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
            help="Top-level folders to include (default: docs agent)",
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

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
