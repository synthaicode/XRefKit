"""On-demand report over the deterministic declaration/signature inventory.

Mechanism D (signature/declaration facts) of the structure-analysis determinism
tiers (knowledge/source_analysis/121). Consumes the inventory emitted by
tools/structure_graph (``--decl <decl.json>``, schema
xrefkit.declaration_facts/v1) and presents facts that back analysis viewpoints
#16 (concurrency), #12 (data-boundary type facts), and #10 (build configuration):

- async    — async / Task-returning methods, flagging those with no
             CancellationToken parameter (propagation-gap candidates) (#16)
- static   — static mutable shared state: non-const non-readonly static fields
             and static settable properties (#16)
- dbset    — EF Core DbSet<TEntity> persistence boundaries (#12)
- concurrency — lock statements and Interlocked / Monitor sites (#16)
- conditional — #if / #elif symbols per file, plus the active preprocessor
             symbols and declared target frameworks per project (#10)

Candidate, not verdict (binding per 131 / 121): a missing CancellationToken is
not a defect (many async methods legitimately take none), static mutable state is
not automatically a race, and #if symbols are the variants that exist, not which
one a given change must target. These are facts for the judgment layer.

Usage:
    python tools/declaration_facts_report.py <decl.json>
    python tools/declaration_facts_report.py <decl.json> --category async --missing-ct
    python tools/declaration_facts_report.py <decl.json> --category dbset
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _loc(v: dict) -> str:
    return f'{v.get("file")}:{v.get("line")}' if v.get("file") else ""


def _report_async(data: dict, top: int, missing_ct: bool) -> None:
    rows = data.get("asyncMethods", [])
    if missing_ct:
        rows = [r for r in rows if not r.get("hasCancellationToken")]
    print(f"## async — async / Task-returning methods  ({len(rows)})"
          + ("  [no CancellationToken]" if missing_ct else ""))
    print("   (a missing CancellationToken is a propagation-gap candidate, not a defect)")
    for r in rows[:top]:
        ct = "ct" if r.get("hasCancellationToken") else "NO-ct"
        kw = "async" if r.get("isAsync") else "task "
        print(f"  [{kw} {ct:5s}] {r['display']} : {r['returnType']}   {_loc(r)}")


def _report_static(data: dict, top: int) -> None:
    rows = data.get("staticState", [])
    print(f"## static — mutable shared state  ({len(rows)})")
    print("   (non-const non-readonly static field / static settable property)")
    for r in rows[:top]:
        print(f"  {r['kind']:8s} {r['display']} : {r['type']}   {_loc(r)}")


def _report_dbset(data: dict, top: int) -> None:
    rows = data.get("dbSets", [])
    print(f"## dbset — EF Core DbSet<T> persistence boundaries  ({len(rows)})")
    for r in rows[:top]:
        print(f"  {r['display']}  -> {r['entityType']}   {_loc(r)}")


def _report_concurrency(data: dict, top: int) -> None:
    rows = data.get("concurrencySites", [])
    print(f"## concurrency — lock / Interlocked / Monitor sites  ({len(rows)})")
    from collections import Counter
    by_kind = Counter(r["kind"] for r in rows)
    print("  kinds: " + ", ".join(f"{k}={n}" for k, n in by_kind.most_common()))
    for r in rows[:top]:
        member = r.get("enclosingDisplay") or "(top level)"
        print(f"  {r['kind']:11s} {r['detail']:14s} in {member}   {_loc(r)}")


def _report_conditional(data: dict, top: int) -> None:
    by_file = data.get("conditionalsByFile", {})
    proj_syms = data.get("projectSymbols", {})
    proj_tfms = data.get("projectTfms", {})
    print("## conditional — declared target frameworks by project")
    for proj, tfms in proj_tfms.items():
        multi = "  (multi-TFM)" if len(tfms) > 1 else ""
        print(f"  {proj}: {', '.join(tfms) or '(none parsed)'}{multi}")
    print()
    print(f"## conditional — #if symbols by file  ({len(by_file)})")
    print("   (build-configuration variants a single compilation pass cannot all see)")
    for f, syms in list(by_file.items())[:top]:
        print(f"  {f}: {', '.join(syms)}")
    print()
    print("## conditional — active preprocessor symbols by project")
    for proj, syms in proj_syms.items():
        print(f"  {proj}: {', '.join(syms)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--category", choices=["async", "static", "dbset", "concurrency", "conditional"],
                    help="show only one category")
    ap.add_argument("--missing-ct", action="store_true",
                    help="(async) show only methods without a CancellationToken")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    data = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    if data.get("schema") != "xrefkit.declaration_facts/v1":
        print(f"warning: unexpected schema {data.get('schema')!r}", file=sys.stderr)

    stats = data.get("stats", {})
    print(f"# Declaration facts report: {args.inventory}")
    print(f"generated: {data.get('generatedAt')}")
    print(f"projects: {', '.join(p['name'] for p in data.get('projects', []))}")
    print(f"async: {stats.get('asyncCount')} "
          f"(no-ct {stats.get('asyncMissingCancellationToken')})   "
          f"static state: {stats.get('staticStateCount')}   "
          f"dbset: {stats.get('dbSetCount')}   "
          f"concurrency: {stats.get('concurrencySiteCount')}   "
          f"conditional files: {stats.get('conditionalFileCount')}")
    print()
    print("candidate, not verdict: missing CT is not a defect, static state is not "
          "automatically a race, #if symbols are variants not the target.")
    print()

    cats = [args.category] if args.category else \
        ["async", "static", "dbset", "concurrency", "conditional"]
    for cat in cats:
        if cat == "async":
            _report_async(data, args.top, args.missing_ct)
        elif cat == "static":
            _report_static(data, args.top)
        elif cat == "dbset":
            _report_dbset(data, args.top)
        elif cat == "concurrency":
            _report_concurrency(data, args.top)
        elif cat == "conditional":
            _report_conditional(data, args.top)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
