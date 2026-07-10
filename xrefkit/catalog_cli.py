"""CLI for list-first catalogs and candidate maintenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .structure_catalog import get_entry, list_findings, list_targets, load_catalog, maintain_catalog, reconcile_receipts


DEFAULT_CATALOG = "knowledge/source_analysis/source_structure_catalog.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit catalog")
    parser.add_argument("--root", default=".")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list")
    listing.add_argument("kind", choices=["targets", "findings"])
    listing.add_argument("--target")
    listing.add_argument("--json", action="store_true")
    get = sub.add_parser("get")
    get.add_argument("xid")
    get.add_argument("--json", action="store_true")
    maintain = sub.add_parser("maintain")
    maintain.add_argument("--inbox", default="work/inbox/source_structure_findings")
    maintain.add_argument("--apply-safe", action="store_true")
    maintain.add_argument("--json", action="store_true")
    reconcile = sub.add_parser("reconcile")
    reconcile.add_argument("--reports", default="work/reports")
    reconcile.add_argument("--inbox", default="work/inbox/source_structure_findings")
    reconcile.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == "list":
            catalog = load_catalog(root / args.catalog)
            if args.kind == "targets":
                result = list_targets(catalog)
            else:
                if not args.target:
                    raise ValueError("--target is required for finding list")
                result = list_findings(catalog, args.target)
        elif args.command == "get":
            result = get_entry(load_catalog(root / args.catalog), args.xid)
        elif args.command == "maintain":
            result = maintain_catalog(root, args.catalog, args.inbox, apply_safe=args.apply_safe)
        else:
            result = reconcile_receipts(root, args.reports, args.inbox)
    except (OSError, KeyError, ValueError) as exc:
        result = {"ok": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if not isinstance(result, dict) or result.get("ok", True) else 1
