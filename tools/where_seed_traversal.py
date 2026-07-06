# xid: 39959ED2E7EC

"""Where impacted-boundary traversal over the structure graph (the XDDP Where step).

Given a seed derived from the change objective, traverse the relation graph to
produce an *impacted boundary candidate* set — the deterministic backstop for the
Where output of dotnet_change_analysis. The cut is computed per change, never
stored (see knowledge/source_analysis/160_structure_graph_tm_backstop.md).

Candidate, not verdict: the traversal proposes; inclusion/exclusion is curated by
a human/LLM against the change objective. Reflection, delegate invocation, and
dynamic resolution beyond resolved interface dispatch are out of range. High
fan-in shared nodes are damped (marked `transit`, not expanded) per principle 5 so
the boundary does not flood with logger/base-type/utility noise.

Directions:
  backward (default) — who depends on the seed: callers, users, and (for a type)
                       members — the classic "impact of changing the seed".
  forward            — what the seed depends on / touches.

Usage:
    python tools/where_seed_traversal.py <graph.json> --seed EntityModel
    python tools/where_seed_traversal.py <graph.json> --seed "KsqlContext.InitializeCore" --direction both --depth 3
    python tools/where_seed_traversal.py <graph.json> --seed IRepo --transit-threshold 30
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Edges that carry change-impact dependency. `writes`/`uses-name` are excluded:
# they are ownership/coupling signals, not ripple paths.
IMPACT_EDGES = {"calls", "uses", "dispatches-to"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("graph")
    ap.add_argument("--seed", required=True, help="DocID or display substring of the change seed")
    ap.add_argument("--direction", choices=["backward", "forward", "both"], default="backward")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--transit-threshold", type=int, default=25,
                    help="nodes with call fan-in above this are damped (transit, not expanded)")
    ap.add_argument("--top", type=int, default=60)
    args = ap.parse_args()

    graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]}
    edges = graph["edges"]

    succ: dict[str, set[str]] = defaultdict(set)   # from -> to (forward)
    pred: dict[str, set[str]] = defaultdict(set)   # to -> from (backward)
    declares: dict[str, set[str]] = defaultdict(set)  # type -> members
    declarer: dict[str, str] = {}                  # member -> declaring type
    call_fanin: dict[str, int] = defaultdict(int)
    for e in edges:
        if e["type"] in IMPACT_EDGES:
            succ[e["from"]].add(e["to"])
            pred[e["to"]].add(e["from"])
        if e["type"] == "declares":
            declares[e["from"]].add(e["to"])
            declarer[e["to"]] = e["from"]
        if e["type"] == "calls":
            call_fanin[e["to"]] += 1

    def owner_of(nid: str) -> tuple[str, str]:
        """(project, declaring-type display) for grouping; clean for any node kind."""
        n = nodes.get(nid)
        if n is None:
            return ("(accessor/external)", nid[2:].rsplit(".", 1)[0] if nid.startswith("M:") else nid)
        if n["kind"] in {"type", "interface", "struct", "enum"}:
            return (n["project"], n["display"])
        t = nodes.get(declarer.get(nid, ""))
        return (n["project"], t["display"] if t else n["display"])

    # Resolve the seed: exact DocID, else case-insensitive display substring.
    q = args.seed.lower()
    seeds = {args.seed} if args.seed in nodes else {
        nid for nid, n in nodes.items() if q in n["display"].lower()
    }
    if not seeds:
        print(f"no node matches seed {args.seed!r}", file=sys.stderr)
        return 2
    # Expanding a type seed to its declared members makes a type-level change
    # traverse from each member that callers actually depend on.
    for sid in list(seeds):
        if nodes.get(sid, {}).get("kind") in {"type", "interface", "struct", "enum"}:
            seeds |= declares.get(sid, set())

    def label(nid: str) -> str:
        n = nodes.get(nid)
        return f'{n["display"]}  [{n["project"]}]' if n else nid

    def traverse(adj: dict[str, set[str]]) -> tuple[dict[str, int], set[str]]:
        dist: dict[str, int] = {}
        transit: set[str] = set()
        queue: deque[tuple[str, int]] = deque((s, 0) for s in seeds)
        seen = set(seeds)
        while queue:
            cur, d = queue.popleft()
            if d >= args.depth:
                continue
            for nxt in adj.get(cur, ()):
                if nxt in seeds:
                    continue
                if nxt not in dist or d + 1 < dist[nxt]:
                    dist[nxt] = d + 1
                # Damp expansion through high fan-in shared nodes (principle 5).
                if call_fanin.get(nxt, 0) > args.transit_threshold:
                    transit.add(nxt)
                    continue
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, d + 1))
        return dist, transit

    print(f"# Where impacted-boundary traversal: {args.graph}")
    print(f"seed: {args.seed!r}  ->  {len(seeds)} seed node(s)")
    print(f"direction: {args.direction}   depth: {args.depth}   transit-threshold(fan-in): {args.transit_threshold}")
    print()
    print("candidate, not verdict: traversal proposes the boundary; inclusion is curated "
          "against the change objective. Reflection/delegate/dynamic resolution out of range.")
    print()

    runs = []
    if args.direction in ("backward", "both"):
        runs.append(("BACKWARD — who depends on the seed (impact of changing it)", pred))
    if args.direction in ("forward", "both"):
        runs.append(("FORWARD — what the seed depends on / touches", succ))

    for title, adj in runs:
        dist, transit = traverse(adj)
        print(f"## {title}   ({len(dist)} candidates)")
        by_proj_type: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
        for nid, d in dist.items():
            disp = nodes.get(nid, {}).get("display", nid)
            by_proj_type[owner_of(nid)].append((d, disp))
        shown = 0
        for (proj, owner), items in sorted(by_proj_type.items()):
            if shown >= args.top:
                break
            print(f"  [{proj}] {owner}")
            for d, disp in sorted(items):
                print(f"      d{d}  {disp}")
                shown += 1
                if shown >= args.top:
                    break
        if transit:
            print(f"  -- {len(transit)} transit node(s) damped (high fan-in, not expanded):")
            for nid in sorted(transit, key=lambda x: -call_fanin.get(x, 0))[:10]:
                print(f"       fan-in={call_fanin.get(nid,0):3d}  {label(nid)}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
