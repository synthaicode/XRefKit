"""Unified error-policy audit: merge the custom locator and the analyzer-backed
normalizer into one 131 candidate stream (the precursor to an `fm audit` front).

Combines two candidate sources, both already in the 131 contract:

- ``tools/error_policy_locator.py``  — custom ``cs.err.empty_catch`` over source files
- ``tools/sarif_to_locator.py``      — analyzer-backed locators from a SARIF run

Candidates are deduplicated by ``(file, line, locator_id)`` so a catch flagged by
both the custom locator and an analyzer (e.g. Roslynator RCS1075) collapses into
one candidate carrying multiple corroborating ``sources``. Output stays
candidate-only (``confidence: candidate``, ``judgment_status: unset``); the audit
never emits a verdict and never auto-fails.

Scope from both inputs is preserved, including the normalizer's
``collection_errors`` (a missing analyzer run is a collection error, never
silently "no hits").
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:  # allow `python tools/error_policy_audit.py`
    sys.path.insert(0, str(REPO_ROOT))

from tools.error_policy_locator import scan_paths as scan_custom
from tools.sarif_to_locator import normalize as normalize_sarif


def _custom_source(hit) -> dict:
    return {
        "detector": hit.detection_method,
        "rule": None,
        "notes": hit.notes,
        "snippet": hit.snippet,
    }


def _analyzer_source(hit) -> dict:
    return {
        "detector": hit.detection_method,
        "rule": hit.external_rule_id,
        "notes": hit.notes,
        "snippet": None,
    }


def aggregate(custom_hits, analyzer_hits) -> list[dict]:
    """Merge both hit lists into unified candidates keyed by (file, line, locator_id)."""
    merged: dict[tuple[str, int, str], dict] = {}

    def add(hit, source: dict) -> None:
        key = (hit.file, hit.line, hit.locator_id)
        rec = merged.get(key)
        if rec is None:
            merged[key] = {
                "locator_id": hit.locator_id,
                "source_pattern_id": hit.source_pattern_id,
                "tier": hit.tier,
                "file": hit.file,
                "line": hit.line,
                "column": hit.column,
                "confidence": "candidate",
                "judgment_status": "unset",
                "sources": [source],
            }
        else:
            rec["column"] = min(rec["column"], hit.column)
            rec["sources"].append(source)

    for hit in custom_hits:
        add(hit, _custom_source(hit))
    for hit in analyzer_hits:
        add(hit, _analyzer_source(hit))

    return [
        merged[k]
        for k in sorted(merged, key=lambda k: (k[0], k[1], k[2]))
    ]


def run(source_paths, sarif_paths, *, root=None, include_tests=False):
    root_path = Path(root).resolve() if root else None

    custom_hits, custom_scope = [], None
    if source_paths:
        # resolve so discovered paths share the form of root_path (avoids 8.3 /
        # symlink mismatches that break relative_to and split the merge key)
        custom_hits, custom_scope = scan_custom(
            [Path(p).resolve() for p in source_paths],
            include_tests=include_tests,
            root=root_path or Path.cwd(),
        )

    analyzer_hits, analyzer_scope = [], None
    if sarif_paths:
        analyzer_hits, analyzer_scope = normalize_sarif(
            [Path(p) for p in sarif_paths], root=root_path
        )

    candidates = aggregate(custom_hits, analyzer_hits)
    scope = {
        "custom_scope": asdict(custom_scope) if custom_scope else None,
        "analyzer_scope": asdict(analyzer_scope) if analyzer_scope else None,
        "collection_errors": list(analyzer_scope.collection_errors) if analyzer_scope else [],
        "candidate_count": len(candidates),
    }
    return candidates, scope


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unified error-policy audit (custom locator + analyzer SARIF); candidates only"
    )
    parser.add_argument("--source", action="append", default=[], help="source file/dir for the custom locator")
    parser.add_argument("--sarif", action="append", default=[], help="analyzer SARIF for the normalizer")
    parser.add_argument("--root", default=None, help="root for relative paths")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--strict", action="store_true", help="exit non-zero on analyzer collection errors"
    )
    args = parser.parse_args(argv)

    if not args.source and not args.sarif:
        parser.error("provide at least one --source and/or --sarif")

    candidates, scope = run(args.source, args.sarif, root=args.root, include_tests=args.include_tests)

    if args.json:
        print(json.dumps({"scope": scope, "candidates": candidates}, indent=2))
    else:
        print(f"collection errors: {len(scope['collection_errors'])}")
        for err in scope["collection_errors"]:
            print(f"  ! {err}")
        print(f"candidates (NOT verdicts): {scope['candidate_count']}")
        for c in candidates:
            rules = ",".join(s["rule"] for s in c["sources"] if s["rule"]) or "-"
            detectors = ",".join(sorted({s["detector"] for s in c["sources"]}))
            print(f"  [{c['locator_id']}] {c['file']}:{c['line']}  x{len(c['sources'])} ({detectors}) rules={rules}")

    if args.strict and scope["collection_errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
