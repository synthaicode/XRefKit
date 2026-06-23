"""Drift-detection scorer for csharp_review eval runs.

Usage:
    python score_findings.py --actual <findings.yaml> [--baseline <score.json>]

The actual-findings file is produced by an eval run of csharp_review and
must follow the schema described in eval_drift_detection.md:

    findings:
      - id: <run-local id>
        category: <category>
        file: <path relative to fixture repo root>
        line: <int>
        severity: critical | major | minor | needs_confirmation
        gist: <one line>
    handoff:
      - file: <path>
        gist: <one line>

Exit code 0 = no drift alarm, 1 = drift alarm raised.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).parent
LINE_WINDOW = 20
SEVERITY_RANK = {"needs_confirmation": 0, "minor": 1, "major": 2, "critical": 3}


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def norm_path(p: str) -> str:
    return p.replace("\\", "/").lstrip("./").lower()


def match(expected: dict, actual_findings: list[dict], used: set[int] | None = None) -> dict | None:
    # One actual finding may satisfy at most one expected finding (`used`
    # tracks consumed entries), so adjacent expected findings in the same
    # file/category cannot both be credited to a single detection.
    for idx, act in enumerate(actual_findings):
        if used is not None and idx in used:
            continue
        if norm_path(act["file"]) != norm_path(expected["file"]):
            continue
        if act["category"] != expected["category"]:
            continue
        if abs(int(act["line"]) - int(expected["expected_line"])) > LINE_WINDOW:
            continue
        if used is not None:
            used.add(idx)
        return act
    return None


def resolve_fixture_cases(manifest: dict) -> dict:
    fixture_map_path = HERE / "fixtures" / "fixture_manifest.yaml"
    fixture_cases = {}
    if fixture_map_path.exists():
        fixture_cases = load_yaml(fixture_map_path).get("cases", {})

    resolved = dict(manifest)
    resolved_findings = []
    for finding in manifest.get("findings", []):
        item = dict(finding)
        case_id = item.get("fixture_case")
        if case_id:
            case = fixture_cases.get(case_id)
            if case is None:
                raise KeyError(f"Unknown fixture_case: {case_id}")
            item.setdefault("file", case["file"])
            item.setdefault("expected_line", case["expected_line"])
        resolved_findings.append(item)
    resolved["findings"] = resolved_findings
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actual", required=True)
    parser.add_argument("--baseline", help="previous score.json to compare against")
    args = parser.parse_args()

    actual = load_yaml(Path(args.actual))
    actual_findings = actual.get("findings", [])
    actual_handoff = actual.get("handoff", [])

    visible = resolve_fixture_cases(load_yaml(HERE / "eval_manifest.yaml"))
    heldout = load_yaml(HERE / "eval_manifest_heldout.yaml")
    expected = visible.get("findings", []) + heldout.get("findings", [])
    calibrations = visible.get("calibration", [])

    hits, misses, severity_low = [], [], []
    used: set[int] = set()
    for exp in expected:
        act = match(exp, actual_findings, used)
        if act is None:
            misses.append(exp["id"])
            continue
        hits.append(exp["id"])
        if SEVERITY_RANK[act["severity"]] < SEVERITY_RANK[exp["min_severity"]]:
            severity_low.append(f"{exp['id']} (got {act['severity']}, expected >= {exp['min_severity']})")

    calibration_failures = []
    for cal in calibrations:
        if cal["category"] == "handoff":
            on_handoff = any(norm_path(h["file"]) == norm_path(cal["file"]) for h in actual_handoff)
            deep_dived = match({**cal, "category": "resource_efficiency"}, actual_findings)
            if deep_dived and not on_handoff:
                calibration_failures.append(f"{cal['id']}: deep-dived instead of handed off")
            continue
        act = match(cal, actual_findings)
        if act is not None:
            cap = cal.get("calibration_max_severity", "needs_confirmation")
            if SEVERITY_RANK[act["severity"]] > SEVERITY_RANK[cap]:
                calibration_failures.append(f"{cal['id']}: severity {act['severity']} exceeds calibration cap {cap}")

    matched_files = {norm_path(e["file"]) for e in expected} | {norm_path(c["file"]) for c in calibrations}
    triage = [
        f"{a['file']}:{a['line']} [{a['category']}] {a.get('gist', '')}"
        for a in actual_findings
        if not any(match(e, [a]) for e in expected + calibrations)
    ]

    recall = len(hits) / len(expected) if expected else 1.0
    missed_major = [
        e["id"] for e in expected
        if e["id"] in misses and SEVERITY_RANK[e["min_severity"]] >= SEVERITY_RANK["major"]
    ]

    # Drift alarm rules (see eval_drift_detection.md):
    alarms = []
    if missed_major:
        alarms.append(f"missed major finding(s): {missed_major}")
    if calibration_failures:
        alarms.append(f"calibration failure(s): {calibration_failures}")
    if args.baseline:
        base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        if len(misses) > len(base.get("misses", [])):
            alarms.append(f"recall regression vs baseline: misses {base.get('misses', [])} -> {misses}")

    score = {
        "recall": round(recall, 3),
        "hits": hits,
        "misses": misses,
        "severity_low": severity_low,
        "calibration_failures": calibration_failures,
        "new_findings_for_human_triage": triage,
        "drift_alarms": alarms,
    }
    print(json.dumps(score, indent=2, ensure_ascii=False))
    return 1 if alarms else 0


if __name__ == "__main__":
    sys.exit(main())
