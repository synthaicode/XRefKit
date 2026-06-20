"""On-demand report over the deterministic DI registration inventory.

Mechanism C (invocation-pattern locators) of the structure-analysis determinism
tiers (see knowledge/source_analysis/121, viewpoint 5 "DI registration and
lifetimes"). Consumes the inventory emitted by tools/structure_graph
(``--di <di.json>``, schema xrefkit.di_registrations/v1): registration sites with
service type, implementation type, lifetime, and the implementation's
constructor dependency types.

It lists registrations and computes **captive-dependency candidates** — a
longer-lived service holding a shorter-lived one — by joining each
implementation's constructor dependency types back to their registered lifetime.

Candidate, not verdict (binding per 131 / 121): the join is static and resolves a
dependency only when its declared type is itself registered here; factory
registrations hide their implementation, and a custom or wrapped container can
change lifetime semantics. A flagged pair is a candidate to inspect, never a
confirmed defect.

With --graph it additionally flags **container-bypass candidates**: code that
constructs a DI-registered type with `new` outside the composition root, found by
joining the graph's constructor `calls` edges to the registered type set. This
completes viewpoint #5 ("components constructed with new inside layers that
otherwise resolve through the container").

Usage:
    python tools/di_registration_report.py <di.json>
    python tools/di_registration_report.py <di.json> --captive-only
    python tools/di_registration_report.py <di.json> --lifetime singleton
    python tools/di_registration_report.py <di.json> --graph <graph.json>   # + bypass
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

# Longer number = longer lived. A captive dependency is a service whose lifetime
# rank exceeds that of a dependency it injects.
RANK = {"singleton": 3, "scoped": 2, "transient": 1}


def _report_bypass(graph_path: str, regs: list[dict]) -> None:
    """Constructions of a registered type via `new` outside the composition root."""
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]}

    registered = {t for r in regs for t in (r.get("serviceType"), r.get("implementationType")) if t}
    # Composition-root files: anything that holds a registration is wiring code,
    # plus the conventional Program.cs / Startup.cs. `new` there is expected.
    root_files = {r["file"] for r in regs if r.get("file")}
    root_basenames = {"Program.cs", "Startup.cs"}

    # member id -> declaring type id (reverse of `declares`).
    declarer = {e["to"]: e["from"] for e in graph["edges"] if e["type"] == "declares"}

    def type_display(member_id: str) -> str | None:
        t = nodes.get(declarer.get(member_id, ""))
        return t["display"] if t else None

    # Registered constructor node ids: ctor members of a registered type.
    registered_ctor = {
        nid for nid in nodes
        if ".#ctor" in nid and type_display(nid) in registered
    }

    seen: set[tuple[str, str]] = set()
    rows: list[tuple[str, str, str]] = []
    for e in graph["edges"]:
        if e["type"] != "calls" or e["to"] not in registered_ctor:
            continue
        caller = nodes.get(e["from"])
        if not caller:
            continue
        f = caller.get("file") or ""
        if f in root_files or f.rsplit("/", 1)[-1] in root_basenames:
            continue
        constructed = type_display(e["to"]) or e["to"]
        kdup = (caller["display"], constructed)
        if kdup in seen:
            continue
        seen.add(kdup)
        rows.append((caller["display"], constructed, f))

    print()
    print(f"## Container-bypass candidates  ({len(rows)})")
    print("   (registered type constructed with `new` outside composition root)")
    if not rows:
        print("  none found")
    for caller, constructed, f in sorted(rows):
        print(f"  {caller}")
        print(f"      news {constructed}   {f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--lifetime", choices=sorted(RANK), help="filter the listing to one lifetime")
    ap.add_argument("--captive-only", action="store_true", help="print only captive-dependency candidates")
    ap.add_argument("--graph", help="structure graph json; enables container-bypass candidates")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    data = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    if data.get("schema") != "xrefkit.di_registrations/v1":
        print(f"warning: unexpected schema {data.get('schema')!r}", file=sys.stderr)
    regs = data.get("registrations", [])

    # service type -> set of registered lifetimes (a type can be registered more
    # than once; any registration that is shorter-lived than a holder is a risk).
    svc_lifetimes: dict[str, set[str]] = defaultdict(set)
    for r in regs:
        if r.get("serviceType"):
            svc_lifetimes[r["serviceType"]].add(r["lifetime"])

    stats = data.get("stats", {})
    print(f"# DI registration report: {args.inventory}")
    print(f"generated: {data.get('generatedAt')}")
    print(f"projects: {', '.join(p['name'] for p in data.get('projects', []))}")
    by_life = stats.get("byLifetime", {})
    print(f"registrations: {stats.get('registrationCount')}   "
          + "  ".join(f"{k}={v}" for k, v in sorted(by_life.items())))
    print()
    print("candidate, not verdict: lifetime join is static; factory regs hide the "
          "impl and custom containers can differ.")
    print()

    # Captive-dependency candidates.
    captive: list[tuple[str, str, str, str, str, int]] = []  # holder, holderLife, dep, depLife, file, line
    for r in regs:
        hlife = r["lifetime"]
        hrank = RANK.get(hlife, 0)
        holder = r.get("implementationType") or r.get("serviceType") or "(factory)"
        for dep in r.get("ctorDeps", []):
            for dlife in svc_lifetimes.get(dep, ()):
                if hrank > RANK.get(dlife, 0):
                    captive.append((holder, hlife, dep, dlife, r.get("file") or "", r.get("line") or 0))

    print(f"## Captive-dependency candidates  ({len(captive)})")
    print("   (holder outlives an injected dependency — e.g. singleton holding scoped)")
    if not captive:
        print("  none found in the registered set")
    for holder, hlife, dep, dlife, file, line in sorted(captive):
        sev = "HARD" if (hlife == "singleton" and dlife == "scoped") else "note"
        loc = f"{file}:{line}" if file else ""
        print(f"  [{sev}] {hlife} {holder}")
        print(f"         holds {dlife} {dep}   {loc}")

    if args.captive_only:
        return 0

    if args.graph:
        _report_bypass(args.graph, regs)

    print()
    listed = [r for r in regs if not args.lifetime or r["lifetime"] == args.lifetime]
    print(f"## Registrations  ({len(listed)})  top {args.top}")
    for r in listed[: args.top]:
        impl = r.get("implementationType") or ("factory" if r.get("Factory") or r.get("factory") else "?")
        svc = r.get("serviceType") or "?"
        loc = f'{r.get("file")}:{r.get("line")}' if r.get("file") else ""
        arrow = f"{svc} -> {impl}" if svc != impl else svc
        print(f"  {r['lifetime']:9s} {r['method']:18s} {arrow}   {loc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
