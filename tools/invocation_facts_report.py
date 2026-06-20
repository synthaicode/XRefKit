"""On-demand report over the deterministic framework-invocation inventory.

Mechanism C (invocation-pattern locators) of the structure-analysis determinism
tiers (knowledge/source_analysis/121). Consumes the inventory emitted by
tools/structure_graph (``--invocations <inv.json>``, schema
xrefkit.invocation_facts/v1) and presents three categories that back analysis
viewpoints #14 (logging), #9 (configuration boundary), and #6 (pipeline order):

- logging   — ILogger.Log* sites with level (viewpoint 14)
- config    — IConfiguration GetSection/GetValue/GetConnectionString/Bind and
              Configure<T> sites with key / bound type (viewpoint 9)
- pipeline  — IApplicationBuilder Use* middleware, order reconstructed per
              enclosing member from file:line (viewpoint 6)
- discovery — reflection / scanning sites (GetTypes, Scan, Activator, GetType)
              that decide wiring at runtime (viewpoint 7)
- transaction — Begin[Transaction|Async] sites on EF Core / System.Data
              (viewpoint 12)

Candidate, not verdict (binding per 131 / 121): these are extracted facts, not
findings. Logging does not assess PII risk, config does not resolve dynamically
built keys, and pipeline order is the *written* order, not its runtime meaning.

Usage:
    python tools/invocation_facts_report.py <inv.json>
    python tools/invocation_facts_report.py <inv.json> --category pipeline
    python tools/invocation_facts_report.py <inv.json> --category config
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _loc(v: dict) -> str:
    return f'{v.get("file")}:{v.get("line")}' if v.get("file") else ""


def _report_logging(rows: list[dict]) -> None:
    print(f"## logging — ILogger sites  ({len(rows)})")
    by_level = Counter(v.get("level") or "?" for v in rows)
    print("  levels: " + ", ".join(f"{k}={n}" for k, n in by_level.most_common()))
    by_method: dict[str, list[dict]] = defaultdict(list)
    for v in rows:
        by_method[v.get("enclosingDisplay") or "(top level)"].append(v)
    for member, vs in sorted(by_method.items()):
        levels = ", ".join(sorted({v.get("level") or "?" for v in vs}))
        print(f"  {len(vs):3d} call(s)  {member}   [{levels}]")


def _report_config(rows: list[dict]) -> None:
    print(f"## config — binding sites  ({len(rows)})")
    for v in rows:
        key = f'"{v["key"]}"' if v.get("key") else "(no literal key)"
        tt = f' -> {v["targetType"]}' if v.get("targetType") else ""
        print(f'  {v["method"]:18s} {key}{tt}   {_loc(v)}')


def _report_pipeline(rows: list[dict]) -> None:
    print(f"## pipeline — IApplicationBuilder Use* order  ({len(rows)})")
    # Reconstruct order per enclosing member by source position (file, line).
    by_member: dict[str, list[dict]] = defaultdict(list)
    for v in rows:
        by_member[v.get("enclosingDisplay") or "(top level)"].append(v)
    for member, vs in sorted(by_member.items()):
        vs.sort(key=lambda v: (v.get("file") or "", v.get("line") or 0))
        print(f"  {member}")
        for i, v in enumerate(vs):
            print(f"      {i:2d}. {v['method']}   {_loc(v)}")


def _report_discovery(rows: list[dict]) -> None:
    print(f"## discovery — reflection / scanning sites  ({len(rows)})")
    print("   (runtime wiring invisible to the call graph; resolution target is spec-out)")
    for v in rows:
        recv = v.get("receiverType") or "?"
        key = f' "{v["key"]}"' if v.get("key") else ""
        member = v.get("enclosingDisplay") or "(top level)"
        print(f'  {v["method"]}{key}  on {recv}   in {member}   {_loc(v)}')


def _report_transaction(rows: list[dict]) -> None:
    print(f"## transaction — Begin* sites  ({len(rows)})")
    for v in rows:
        recv = v.get("receiverType") or "?"
        member = v.get("enclosingDisplay") or "(top level)"
        print(f'  {v["method"]}  on {recv}   in {member}   {_loc(v)}')


REPORTERS = {
    "logging": _report_logging,
    "config": _report_config,
    "pipeline": _report_pipeline,
    "discovery": _report_discovery,
    "transaction": _report_transaction,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--category", choices=sorted(REPORTERS), help="show only one category")
    args = ap.parse_args()

    data = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    if data.get("schema") != "xrefkit.invocation_facts/v1":
        print(f"warning: unexpected schema {data.get('schema')!r}", file=sys.stderr)
    invs = data.get("invocations", [])

    stats = data.get("stats", {})
    print(f"# Invocation facts report: {args.inventory}")
    print(f"generated: {data.get('generatedAt')}")
    print(f"projects: {', '.join(p['name'] for p in data.get('projects', []))}")
    by_cat = stats.get("byCategory", {})
    print(f"invocations: {stats.get('invocationCount')}   "
          + "  ".join(f"{k}={v}" for k, v in sorted(by_cat.items())))
    print()
    print("candidate, not verdict: facts only — no PII assessment, no dynamic-key "
          "resolution, pipeline order is written order not runtime meaning.")
    print()

    categories = [args.category] if args.category else list(REPORTERS)
    for cat in categories:
        rows = [v for v in invs if v["category"] == cat]
        REPORTERS[cat](rows)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
