#!/usr/bin/env python3
"""Conservative, evidence-preserving extraction of decision and pairwise tables.

This is a syntax scanner, not a C# or T-SQL compiler. Unresolved expressions
remain explicit in ``uncertainties`` and must not be promoted to business rules.
"""
from __future__ import annotations
import itertools, re
from pathlib import Path

CONDITION_RE = re.compile(r"\b(if|when|case)\b(?P<expr>[^\r\n]*)", re.I)
COMPARISON_RE = re.compile(r"(?P<field>[\[\]A-Za-z_][\w.\[\]]*)\s*(?P<op>==|!=|>=|<=|>|<|=|\bIN\b|\bIS\b)\s*(?P<value>\([^\)]*\)|[^,;\s\)]+)", re.I)
STRING_RE = re.compile(r"'(?:''|[^'])*'|\"(?:\\.|[^\"])*\"")
IDENTIFIER_RE = re.compile(r"^[\[\]A-Za-z_][\w.\[\]]*$")
KEYWORDS = {"if", "when", "case", "then", "else", "and", "or", "not", "is", "null", "true", "false"}

def _clean(value):
    value = value.strip().strip("[]")
    return value

def _literal_values(value):
    value = value.strip()
    if value.startswith("(") and value.endswith(")"):
        parts = value[1:-1].split(",")
        return [_clean(p).strip("'\"") for p in parts if p.strip()]
    if STRING_RE.fullmatch(value): return [value[1:-1].replace("''", "'").replace('\\"', '"')]
    if re.fullmatch(r"-?\d+(?:\.\d+)?", value): return [value]
    if value.upper() in {"NULL", "TRUE", "FALSE"}: return [value.upper()]
    return []

def _language(path): return "csharp" if path.suffix.lower() == ".cs" else "sql"

def extract_source_tables(root):
    root = Path(root)
    rows, factors, uncertainties, files = [], {}, [], []
    paths = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".cs", ".sql"})
    for path in paths:
        rel = str(path.relative_to(root)).replace("\\", "/")
        files.append(rel)
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for match in CONDITION_RE.finditer(line):
                expr = match.group("expr").strip()
                expr = re.sub(r"^\(?\s*(?:when|case)\b", "", expr, flags=re.I).strip()
                expr = re.split(r"\bthen\b", expr, maxsplit=1, flags=re.I)[0].strip()
                expr = expr.rstrip("{").strip().rstrip(")").strip()
                comparisons = []
                for comp in COMPARISON_RE.finditer(expr):
                    field, op, raw = _clean(comp.group("field")), comp.group("op").upper(), comp.group("value")
                    if field.lower() in KEYWORDS: continue
                    values = _literal_values(raw)
                    if not values:
                        uncertainties.append({"source": f"{rel}:{line_no}", "expression": expr, "reason": "comparison value or expression is not statically literal"})
                        values = ["<unknown>"]
                    comparisons.append({"field": field, "operator": op, "values": values})
                    factors.setdefault(field, {"values": set(), "evidence": []})["values"].update(values)
                    factors[field]["evidence"].append(f"{rel}:{line_no}")
                if comparisons:
                    rows.append({"id": f"DT-{len(rows)+1:04d}", "source": f"{rel}:{line_no}", "language": _language(path), "construct": match.group(1).lower(), "condition": expr, "conditions": comparisons, "outcome": "<human-confirmation-required>"})
                elif expr and not IDENTIFIER_RE.fullmatch(expr):
                    uncertainties.append({"source": f"{rel}:{line_no}", "expression": expr, "reason": "condition found but no deterministic comparison extracted"})
    factor_list = [{"name": name, "values": sorted(data["values"], key=str), "evidence": sorted(set(data["evidence"]))} for name, data in sorted(factors.items())]
    return {"source_root": str(root), "files": files, "factors": factor_list, "decision_table": rows, "uncertainties": uncertainties}

def pairwise_table(factors):
    """Create a deterministic strength-2 covering table from extracted factors."""
    if not factors: return {"strength": 2, "rows": [], "uncovered_pairs": []}
    names, domains = [f["name"] for f in factors], [f["values"] or ["<unknown>"] for f in factors]
    if len(names) == 1: return {"strength": 2, "rows": [{names[0]: v} for v in domains[0]], "uncovered_pairs": []}
    required = {(i, j, a, b) for i in range(len(names)) for j in range(i+1, len(names)) for a in domains[i] for b in domains[j]}
    candidates = [dict(zip(names, values)) for values in itertools.product(*domains)]
    selected = []
    while required:
        best = max(candidates, key=lambda row: sum((i, j, row[names[i]], row[names[j]]) in required for i in range(len(names)) for j in range(i+1, len(names))))
        selected.append(best)
        required -= {(i, j, best[names[i]], best[names[j]]) for i in range(len(names)) for j in range(i+1, len(names))}
        candidates.remove(best)
    return {"strength": 2, "rows": selected, "uncovered_pairs": sorted([list(x) for x in required], key=str)}
