"""On-demand report over a deterministic custom-attribute inventory.

Consumes the attribute inventory emitted by tools/structure_graph
(``--attributes <attrs.json>``, schema xrefkit.attribute_inventory/v1) and lists
custom-attribute applications and their constant-folded values. Attributes are
the static footprint of otherwise-dynamic channels (DI, routing, serialization,
mapping); this report surfaces those facts deterministically instead of leaving
them to LLM spec-out.

See knowledge/source_analysis/160_structure_graph_tm_backstop.md.

Usage:
    python tools/attribute_inventory_report.py <attrs.json>                 # summary by attribute type
    python tools/attribute_inventory_report.py <attrs.json> --attribute Topic   # list applications of [Topic]
    python tools/attribute_inventory_report.py <attrs.json> --target Order      # filter by target display substring
    python tools/attribute_inventory_report.py <attrs.json> --include-generated # keep obj/ AssemblyInfo attributes
    python tools/attribute_inventory_report.py <attrs.json> --top 20
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _norm(name: str) -> str:
    """Normalize an attribute name for matching: case-fold, drop Attribute suffix."""
    n = name.lower()
    if n.endswith("attribute"):
        n = n[: -len("attribute")]
    return n


def _render_value(v: object) -> str:
    if v is None:
        return "null"
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return "[" + ", ".join(_render_value(x) for x in v) + "]"
    return str(v)


def _is_generated(app: dict) -> bool:
    """Framework-injected assembly attributes live in generated obj/ AssemblyInfo."""
    f = app.get("file")
    if not f:
        return False
    return f.startswith("obj/") or "/obj/" in f


def _render_args(app: dict) -> str:
    parts = [_render_value(a) for a in app.get("ctorArgs", [])]
    parts += [f"{k}={_render_value(v)}" for k, v in app.get("namedArgs", {}).items()]
    return "(" + ", ".join(parts) + ")" if parts else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--attribute", help="filter to one attribute type (suffix/case insensitive)")
    ap.add_argument("--target", help="filter to targets whose display contains this substring")
    ap.add_argument("--include-generated", action="store_true",
                    help="keep framework-injected assembly attributes from generated obj/ AssemblyInfo")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    data = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    if data.get("schema") != "xrefkit.attribute_inventory/v1":
        print(f"warning: unexpected schema {data.get('schema')!r}", file=sys.stderr)
    apps = data.get("attributes", [])

    generated_hidden = 0
    if not args.include_generated:
        kept = [a for a in apps if not _is_generated(a)]
        generated_hidden = len(apps) - len(kept)
        apps = kept

    if args.attribute:
        q = _norm(args.attribute)
        apps = [a for a in apps if _norm(a["attributeName"]) == q]
    if args.target:
        t = args.target.lower()
        apps = [a for a in apps if t in a["targetDisplay"].lower()]

    stats = data.get("stats", {})
    print(f"# Attribute inventory report: {args.inventory}")
    print(f"generated: {data.get('generatedAt')}")
    print(f"projects: {', '.join(p['name'] for p in data.get('projects', []))}")
    print(
        f"applications: {stats.get('applicationCount')}   "
        f"distinct attribute types: {stats.get('distinctAttributeTypes')}   "
        f"annotated targets: {stats.get('annotatedTargets')}"
    )
    if generated_hidden:
        print(f"hidden (generated obj/ AssemblyInfo): {generated_hidden}   (--include-generated to show)")
    if args.attribute or args.target:
        print(f"filtered applications: {len(apps)}")
    print()

    # Detail listing when a filter narrows the set; otherwise a summary by type.
    if args.attribute or args.target:
        for a in apps:
            loc = f"{a['file']}:{a['line']}" if a.get("file") else "(no source loc)"
            print(f"  [{a['attributeName']}]{_render_args(a)}")
            print(f"      -> {a['targetKind']} {a['targetDisplay']}  [{a['project']}]  {loc}")
        return 0

    by_type: dict[str, set[str]] = defaultdict(set)
    counts: dict[str, int] = defaultdict(int)
    for a in apps:
        by_type[a["attributeName"]].add(a["target"])
        counts[a["attributeName"]] += 1

    print(f"## Attribute types by application count  top {args.top}")
    print("   (pass --attribute <name> to list applications and values)")
    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[: args.top]
    for name, c in rows:
        print(f"  apps={c:3d}  targets={len(by_type[name]):3d}  [{name}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
