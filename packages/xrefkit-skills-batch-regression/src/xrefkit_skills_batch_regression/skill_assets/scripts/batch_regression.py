#!/usr/bin/env python3
"""Deterministic combination and old/new batch-result analysis.

This module deliberately has no database or process adapter. Adapters emit the
JSON record contract in references/adapter-contract.md; this tool consumes it.
"""
from __future__ import annotations
import argparse, csv, hashlib, itertools, json, random, sys
from datetime import datetime
from pathlib import Path
from code_tables import extract_source_tables, pairwise_table

STATUSES = {"success", "business_error", "system_error", "not_executed"}

def predicate(value, spec):
    if not spec: return False
    clauses = spec.get("all", spec.get("any", []))
    matched = [clause(value, c) for c in clauses]
    return all(matched) if "all" in spec else any(matched)

def clause(row, c):
    field, op, expected = c["field"], c["op"], c.get("value")
    present = field in row and row[field] is not None
    actual = row.get(field)
    if op == "eq": return actual == expected
    if op == "neq": return actual != expected
    if op == "in": return actual in expected if isinstance(expected, (list, tuple, set)) else False
    if op == "not_in": return actual not in expected if isinstance(expected, (list, tuple, set)) else False
    if op == "exists": return present
    if op == "missing": return not present
    return False

def generate_candidates(config):
    elements = config["combination"]["elements"]
    names = [e["name"] for e in elements]
    candidates = [dict(zip(names, values)) for values in itertools.product(*(e["values"] for e in elements))]
    all_count = len(candidates)
    kept, classifications = [], []
    for row in candidates:
        excluded = None
        for c in config["combination"].get("constraints", []):
            kind = c["kind"]
            matched = predicate(row, c.get("when"))
            missing_required = kind in ("required", "required_if") and matched and not row.get(c.get("field"))
            if matched and (kind in ("forbidden", "business_invalid", "upstream_absent", "uncertain") or missing_required):
                excluded = c
                break
        if excluded:
            kind = excluded["kind"]
            classification = {"forbidden": "business_invalid", "business_invalid": "business_invalid", "upstream_absent": "upstream_absent", "uncertain": "uncertain"}.get(kind, "business_invalid")
            classifications.append({"input": row, "classification": classification, "constraint": excluded})
        else:
            kept.append(row)
            classifications.append({"input": row, "classification": "candidate"})
    return {"all_candidate_count": all_count, "post_constraint_count": len(kept), "candidates": kept, "classifications": classifications}

def analyze_paths(paths):
    """Summarize static execution-path evidence without pretending to resolve dynamic dispatch."""
    result = {"path_count": len(paths), "dual_layer_paths": 0, "child_sp_paths": 0, "dynamic_unknowns": []}
    for path in paths:
        if path.get("csharp") and path.get("stored_procedures"): result["dual_layer_paths"] += 1
        if path.get("child_stored_procedures"): result["child_sp_paths"] += 1
        if path.get("dynamic_sql") or path.get("dynamic_sp_name"):
            result["dynamic_unknowns"].append({"path_id": path.get("id"), "reason": "dynamic SQL or stored-procedure target requires runtime evidence"})
    return result

def normalize(record, config):
    record = json.loads(json.dumps(record, ensure_ascii=False))
    for field in config.get("comparison", {}).get("ignore_fields", []): record.pop(field, None)
    for field, kind in config.get("comparison", {}).get("normalize_fields", {}).items():
        if field not in record: continue
        if kind == "datetime":
            try: record[field] = datetime.fromisoformat(str(record[field]).replace("Z", "+00:00")).isoformat()
            except ValueError: record[field] = "<invalid-datetime>"
        elif kind == "number":
            try: record[field] = float(record[field])
            except (TypeError, ValueError): record[field] = "<invalid-number>"
    return record

def compare(old_records, new_records, config):
    key = lambda r: tuple(r.get("input", {}).get(k) for k in config["comparison"]["key_fields"])
    old, new = {key(r): r for r in old_records}, {key(r): r for r in new_records}
    expected = config.get("planned_differences", [])
    rows = []
    for k in sorted(set(old) | set(new), key=str):
        o, n = old.get(k), new.get(k)
        if not o or not n: cls = "not_executed"
        elif n.get("status") == "system_error" or o.get("status") == "system_error": cls = "system_error"
        elif n.get("status") == "not_executed": cls = "not_executed"
        elif n.get("status") == "business_error" and o.get("status") != "business_error": cls = "business_invalid"
        elif n.get("status") not in STATUSES or o.get("status") not in STATUSES: cls = "uncertain"
        else:
            on, nn = normalize(o, config), normalize(n, config)
            fields = config["comparison"].get("fields", [])
            changed = [f for f in fields if on.get(f) != nn.get(f)]
            if not changed: cls = "baseline_match"
            else:
                hit = next((p for p in expected if predicate(n.get("input", {}), p.get("when")) and set(changed).issubset(set(p.get("fields", [])))), None)
                cls = "planned_difference" if hit else "unexplained_difference"
        rows.append({"input": (n or o).get("input", {}), "old": o, "new": n, "classification": cls,
                     "path_refs": sorted(set((o or {}).get("path_refs", []) + (n or {}).get("path_refs", []))),
                     "planned_relation": next((p.get("relation") for p in expected if predicate((n or o).get("input", {}), p.get("when"))), None)})
    return rows

def summarize(candidate_report, comparisons, config):
    counts = {k: 0 for k in ["baseline_match", "business_invalid", "system_error", "planned_difference", "unexplained_difference", "uncertain", "not_executed", "upstream_absent"]}
    for row in candidate_report["classifications"]:
        if row["classification"] == "business_invalid": counts["business_invalid"] += 1
    for row in comparisons: counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    old_records = [row["old"] for row in comparisons if row.get("old")]
    new_records = [row["new"] for row in comparisons if row.get("new")]
    paths = {}
    for row in comparisons:
        for path in row.get("path_refs", []) or ["unattributed"]: paths[path] = paths.get(path, 0) + 1
    return {**counts, "all_candidate_count": candidate_report["all_candidate_count"], "post_constraint_count": candidate_report["post_constraint_count"],
            "current_normal_count": sum(r.get("status") == "success" for r in old_records),
            "business_error_count": sum(r.get("status") == "business_error" for r in old_records),
            "new_system_error_count": sum(r.get("status") == "system_error" for r in new_records),
            "unexecuted_count": counts.get("not_executed", 0),
            "processed_count": len(comparisons), "path_counts": paths, "representative_regression_set_count": len(select_regression_set(comparisons, config)),
            "analysis": analyze_paths(config.get("paths", [])),
            "human_judgments_required": ["business validity", "baseline defects", "planned differences", "unexplained differences", "release disposition"]}

def select_regression_set(rows, config):
    limit, seed = config.get("regression_set", {}).get("max_size", 100), config.get("regression_set", {}).get("seed", 0)
    by_class = {}
    for row in rows: by_class.setdefault(row["classification"], []).append(row)
    selected = []
    for cls in sorted(by_class): selected.append(sorted(by_class[cls], key=lambda r: json.dumps(r["input"], sort_keys=True))[0])
    rest = [r for r in rows if r not in selected]; random.Random(seed).shuffle(rest)
    return (selected + rest)[:limit]

def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def main(argv=None):
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate"); g.add_argument("config"); g.add_argument("-o", "--output", required=True)
    c = sub.add_parser("compare"); c.add_argument("config"); c.add_argument("old"); c.add_argument("new"); c.add_argument("-o", "--output", required=True)
    r = sub.add_parser("report"); r.add_argument("config"); r.add_argument("old"); r.add_argument("new"); r.add_argument("-o", "--output", required=True)
    t = sub.add_parser("extract-tables"); t.add_argument("root"); t.add_argument("-o", "--output", required=True)
    args = p.parse_args(argv)
    if args.cmd == "extract-tables":
        out = extract_source_tables(args.root)
        out["orthogonal_table"] = pairwise_table(out["factors"])
    else:
        config = load(args.config); candidates = generate_candidates(config)
        if args.cmd == "generate": out = candidates
        else:
            comparisons = compare(load(args.old), load(args.new), config)
            if args.cmd == "compare": out = comparisons
            else: out = {"summary": summarize(candidates, comparisons, config), "comparisons": comparisons, "regression_set": select_regression_set(comparisons, config)}
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"); return 0
if __name__ == "__main__": sys.exit(main())
