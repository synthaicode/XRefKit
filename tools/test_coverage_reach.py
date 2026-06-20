"""Deterministic test-coverage reachability over the structure graph.

Mechanism F of the structure-analysis determinism tiers (see
knowledge/source_analysis/120 viewpoint 19, "Test boundary"). Consumes the
relation graph (tools/structure_graph, schema xrefkit.structure_graph/v1) and
the attribute inventory (--attributes, schema xrefkit.attribute_inventory/v1)
and computes, by forward `calls` traversal from test methods, which production
symbols are statically reachable from at least one test. Production methods that
no test reaches are emitted as **coverage-gap candidates**.

Interface/virtual dispatch is followed: the graph's `dispatches-to` edges
(abstraction member -> concrete implementation) are traversed alongside `calls`,
so a method reached only through an interface or base-class call is counted.

Candidate, not verdict (same binding as the error-policy locator tiers, 131): the
static graph still cannot see reflection- or delegate-based invocation, so an
"uncovered" entry is a candidate to inspect, never proof of missing coverage; and
reachability is not behavioral coverage (a reached method may be exercised
without its behavior asserted). The scope actually scanned is declared in the
output.

Usage:
    python tools/test_coverage_reach.py <graph.json> --attributes <attrs.json>
    python tools/test_coverage_reach.py <graph.json> --attributes <attrs.json> --top 40
    python tools/test_coverage_reach.py <graph.json> --attributes <attrs.json> --show-covered
    python tools/test_coverage_reach.py <graph.json> --attributes <attrs.json> --test-attribute SpecFact
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

# Test-method markers across the common .NET frameworks (xUnit, NUnit, MSTest).
# Matched suffix- and case-insensitively, so "FactAttribute" matches "Fact".
DEFAULT_TEST_ATTRS = {
    "fact", "theory",                         # xUnit
    "test", "testcase", "testcasesource",     # NUnit
    "testmethod", "datatestmethod",           # MSTest
}


def _norm(name: str) -> str:
    n = name.lower()
    if n.endswith("attribute"):
        n = n[: -len("attribute")]
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("graph")
    ap.add_argument("--attributes", required=True, help="attribute inventory json (to find test methods)")
    ap.add_argument("--test-attribute", action="append", default=[],
                    help="additional test-method attribute name (repeatable)")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--show-covered", action="store_true",
                    help="list reached production methods instead of the gap")
    args = ap.parse_args()

    graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    inv = json.loads(Path(args.attributes).read_text(encoding="utf-8"))

    nodes = {n["id"]: n for n in graph["nodes"]}
    # Forward adjacency: a method reaches its callees (calls) and, when it calls an
    # interface/abstract member, the concrete implementations of it (dispatches-to).
    calls: dict[str, set[str]] = defaultdict(set)
    dispatch_edges = 0
    for e in graph["edges"]:
        if e["type"] == "calls":
            calls[e["from"]].add(e["to"])
        elif e["type"] == "dispatches-to":
            calls[e["from"]].add(e["to"])
            dispatch_edges += 1

    test_attr_names = set(DEFAULT_TEST_ATTRS) | {_norm(a) for a in args.test_attribute}
    test_methods = {
        a["target"]
        for a in inv.get("attributes", [])
        if a["targetKind"] == "method" and _norm(a["attributeName"]) in test_attr_names
    }
    # A project that declares a test method is a test project; everything else is
    # production. Coverage is only meaningful for production methods.
    test_projects = {nodes[m]["project"] for m in test_methods if m in nodes}

    def is_production_method(n: dict) -> bool:
        return n["kind"] == "method" and n["project"] not in test_projects

    production_methods = {nid for nid, n in nodes.items() if is_production_method(n)}

    # Forward BFS from every test method over the call graph.
    reached: set[str] = set()
    queue: deque[str] = deque(test_methods)
    while queue:
        cur = queue.popleft()
        for nxt in calls.get(cur, ()):
            if nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)

    covered = production_methods & reached
    uncovered = production_methods - reached

    def label(nid: str) -> str:
        n = nodes.get(nid)
        return f'{n["display"]}  [{n["project"]}]' if n else nid

    total = len(production_methods)
    pct = (len(covered) / total * 100.0) if total else 0.0

    # Scope declaration (binding: "what was scanned" is part of the result).
    print(f"# Test-coverage reachability: {args.graph}")
    print(f"graph generated: {graph.get('generatedAt')}")
    print(f"projects: {', '.join(p['name'] for p in graph['projects'])}")
    print(f"test projects: {', '.join(sorted(test_projects)) or '(none found)'}")
    print(f"test attributes matched: {', '.join(sorted(test_attr_names))}")
    print(f"test methods (seeds): {len(test_methods)}")
    print(f"dispatch edges followed: {dispatch_edges}")
    print()
    print("candidate, not verdict: `calls` + `dispatches-to` traversal; reflection / "
          "delegate invocation still unseen, and reach is not assertion.")
    print()

    if not test_methods:
        print("no test methods found — supply the right --test-attribute, or the "
              "attribute inventory does not cover the test project.")
        return 0

    print(f"production methods: {total}   reachable: {len(covered)}   "
          f"gap candidates: {len(uncovered)}   reach={pct:.1f}%")
    print()

    if args.show_covered:
        print(f"## Reachable production methods  top {args.top}")
        rows = sorted(covered, key=lambda nid: label(nid))[: args.top]
        for nid in rows:
            print(f"  reached  {label(nid)}")
        return 0

    print(f"## Coverage-gap candidates — no test statically reaches these  top {args.top}")
    print("   (inspect; an interface-dispatched impl can appear here falsely)")
    by_proj_type: dict[tuple[str, str], list[str]] = defaultdict(list)
    for nid in uncovered:
        n = nodes[nid]
        # Group by declaring type for readability (DocID member -> owning type).
        owner = n["display"].rsplit(".", 1)[0] if "." in n["display"] else n["project"]
        by_proj_type[(n["project"], owner)].append(n["display"])
    shown = 0
    for (proj, owner), members in sorted(by_proj_type.items()):
        if shown >= args.top:
            break
        print(f"  [{proj}] {owner}")
        for m in sorted(members):
            print(f"      - {m}")
            shown += 1
            if shown >= args.top:
                break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
