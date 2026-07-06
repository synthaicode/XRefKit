# xid: 13E32D7ED058

"""Coupling report over a structure graph (no seed).

Consumes the graph emitted by tools/structure_graph (schema
xrefkit.structure_graph/v1) and reports the seedless views the XDDP Where
backstop can produce before any change requirement: graph composition and the
Coupling Check (fan-in / fan-out / degree centrality).

See knowledge/source_analysis/160_structure_graph_tm_backstop.md.

Usage:
    python tools/structure_graph_report.py <graph.json> [--top N]
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("graph")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    data = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in data["nodes"]}
    edges = data["edges"]

    # Composition
    node_kinds = Counter(n["kind"] for n in nodes.values())
    edge_types = Counter(e["type"] for e in edges)

    # Internal call graph: fan-in (distinct callers) / fan-out (distinct callees)
    callers: dict[str, set[str]] = defaultdict(set)  # node -> who calls it
    callees: dict[str, set[str]] = defaultdict(set)  # node -> who it calls
    for e in edges:
        if e["type"] != "calls":
            continue
        callees[e["from"]].add(e["to"])
        callers[e["to"]].add(e["from"])

    ext = data.get("externalCallCount", {})

    # Name-based coupling: shared identifier-like literals (topic/schema/config).
    name_users: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        if e["type"] == "uses-name":
            name_users[e["to"]].add(e["from"])

    # Dependency direction: type-reference (`uses`) and project-reference edges.
    uses_in: dict[str, set[str]] = defaultdict(set)   # type -> types that use it
    uses_out: dict[str, set[str]] = defaultdict(set)  # type -> types it uses
    project_deps: list[tuple[str, str]] = []
    # State ownership: which members write each field (reverse of `writes`).
    field_writers: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        if e["type"] == "uses":
            uses_out[e["from"]].add(e["to"])
            uses_in[e["to"]].add(e["from"])
        elif e["type"] == "uses-project":
            project_deps.append((e["from"], e["to"]))
        elif e["type"] == "writes":
            field_writers[e["to"]].add(e["from"])

    def label(nid: str) -> str:
        n = nodes.get(nid)
        if not n:
            return nid
        return f'{n["display"]}  [{n["project"]}]'

    all_call_nodes = set(callers) | set(callees)
    rows = []
    for nid in all_call_nodes:
        fin = len(callers[nid])
        fout = len(callees[nid])
        rows.append((nid, fin, fout, fin + fout))

    print(f"# Structure graph report: {args.graph}")
    print(f"generated: {data.get('generatedAt')}")
    print(f"projects: {', '.join(p['name'] for p in data['projects'])}")
    print()
    print(f"nodes: {data['stats']['nodeCount']}   edges: {data['stats']['edgeCount']}")
    print("node kinds: " + ", ".join(f"{k}={v}" for k, v in node_kinds.most_common()))
    print("edge types: " + ", ".join(f"{k}={v}" for k, v in edge_types.most_common()))
    print()

    n = args.top

    print(f"## High fan-in (most depended-upon — change ripples widely)  top {n}")
    for nid, fin, fout, _ in sorted(rows, key=lambda r: (-r[1], r[0]))[:n]:
        print(f"  fan-in={fin:3d} fan-out={fout:3d}  {label(nid)}")
    print()

    print(f"## High fan-out (most dependent — touches many things)  top {n}")
    for nid, fin, fout, _ in sorted(rows, key=lambda r: (-r[2], r[0]))[:n]:
        print(f"  fan-out={fout:3d} fan-in={fin:3d}  {label(nid)}")
    print()

    print(f"## High degree centrality (fan-in + fan-out)  top {n}")
    print("   (candidates to mark `transit` / prune during traversal — principle 5)")
    for nid, fin, fout, deg in sorted(rows, key=lambda r: (-r[3], r[0]))[:n]:
        print(f"  degree={deg:3d} (in={fin}, out={fout})  {label(nid)}")
    print()

    if name_users:
        print(f"## Name-based coupling — shared literals (topic/schema/config)  top {n}")
        print("   (call-invisible convergence: distinct members sharing one name)")
        for nid, users in sorted(name_users.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:n]:
            print(f"  members={len(users):3d}  \"{nodes[nid]['name']}\"")
        print()

    if ext:
        print(f"## Most external calls (boundary to framework / NuGet)  top {n}")
        for nid, c in sorted(ext.items(), key=lambda kv: -kv[1])[:n]:
            print(f"  external-calls={c:3d}  {label(nid)}")
        print()

    if project_deps:
        print("## Project dependencies (assembly-boundary direction)")
        for frm, to in sorted(project_deps):
            fn = nodes.get(frm, {}).get("name", frm)
            tn = nodes.get(to, {}).get("name", to)
            print(f"  {fn} -> {tn}")
        print()

    if uses_out or uses_in:
        dep_nodes = set(uses_in) | set(uses_out)
        print(f"## Type dependency `uses` — high fan-in (most depended-upon types)  top {n}")
        for nid in sorted(dep_nodes, key=lambda x: (-len(uses_in[x]), x))[:n]:
            print(f"  uses-in={len(uses_in[nid]):3d} uses-out={len(uses_out[nid]):3d}  {label(nid)}")
        print()
        print(f"## Type dependency `uses` — high fan-out (most dependent types)  top {n}")
        for nid in sorted(dep_nodes, key=lambda x: (-len(uses_out[x]), x))[:n]:
            print(f"  uses-out={len(uses_out[nid]):3d} uses-in={len(uses_in[nid]):3d}  {label(nid)}")
        print()

    if field_writers:
        print(f"## State ownership — fields with the most distinct writers  top {n}")
        print("   (many writers across types = diffuse mutable-state ownership)")
        for nid, writers in sorted(field_writers.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:n]:
            print(f"  writers={len(writers):3d}  {label(nid)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
