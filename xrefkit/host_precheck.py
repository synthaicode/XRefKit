"""Deterministic, host-agnostic compatibility pre-checks for Skill routing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "xrefkit.host_compatibility_precheck/v1"
_REQUIRED = ("host", "extension", "transcript_reference", "baseline", "observed")


def _text(value: Any, field: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{field} is required")
    return result


def _bool(value: Any) -> bool:
    return value is True


def build_precheck_report(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate only caller-supplied, observable routing facts.

    The function deliberately does not inspect a transcript or attempt to infer
    host/model routing. A transcript reference is provenance, not proof.
    """
    for field in _REQUIRED:
        if field not in spec:
            raise ValueError(f"{field} is required")

    host = _text(spec["host"], "host")
    extension = _text(spec["extension"], "extension")
    transcript_reference = _text(spec["transcript_reference"], "transcript_reference")
    baseline = spec["baseline"]
    observed = spec["observed"]
    if not isinstance(baseline, Mapping) or not isinstance(observed, Mapping):
        raise ValueError("baseline and observed must be objects")
    baseline_skill = _text(baseline.get("skill"), "baseline.skill")
    baseline_result = _text(baseline.get("result"), "baseline.result")
    observed_skill = _text(observed.get("skill"), "observed.skill")
    observed_result = _text(observed.get("result"), "observed.result")

    evidence = spec.get("evidence", {})
    if not isinstance(evidence, Mapping):
        raise ValueError("evidence must be an object")
    bootstrap = _bool(evidence.get("bootstrap"))
    discovery = _bool(evidence.get("discovery"))
    route_selection = _bool(evidence.get("route_selection"))
    catalog = str(spec.get("catalog", "available")).strip().lower()
    intent = str(spec.get("intent", "clear")).strip().lower()
    generic_preselection = _bool(spec.get("generic_preselection"))
    if catalog not in {"available", "unavailable"}:
        raise ValueError("catalog must be available or unavailable")
    if intent not in {"clear", "ambiguous"}:
        raise ValueError("intent must be clear or ambiguous")

    reasons: list[str] = []
    status = "pass"
    next_action = "Continue with the recorded XRefKit-managed route."
    if catalog == "unavailable":
        status = "blocked"
        reasons.append("The managed Skill catalog was unavailable.")
        next_action = "Make the managed catalog available, then repeat the pre-check."
    elif generic_preselection:
        status = "blocked"
        reasons.append("The host had already selected a generic Skill before managed routing evidence was recorded.")
        next_action = "Use the explicit XRefKit entrypoint and record a new bootstrap, discovery, and route-selection trace."
    elif not (bootstrap and discovery and route_selection):
        status = "blocked"
        reasons.append("Bootstrap, discovery, and route-selection evidence are not all present.")
        next_action = "Run the managed bootstrap/discovery sequence and record route-selection evidence before claiming routing."
    elif intent == "ambiguous":
        status = "needs_human_confirmation"
        reasons.append("The intent matched more than one possible route.")
        next_action = "Ask the human to select the intended XRefKit entrypoint or Skill."
    elif (observed_skill, observed_result) != (baseline_skill, baseline_result):
        status = "needs_human_confirmation"
        reasons.append("The observed Skill/result differs from the declared baseline.")
        next_action = "Compare the evidence with the human owner and repeat after the baseline is confirmed."

    return {
        "schema": SCHEMA,
        "observed": {
            "host": host,
            "extension": extension,
            "transcript_reference": transcript_reference,
            "baseline": {"skill": baseline_skill, "result": baseline_result},
            "selected": {"skill": observed_skill, "result": observed_result},
            "evidence": {
                "bootstrap": bootstrap,
                "discovery": discovery,
                "route_selection": route_selection,
            },
            "catalog": catalog,
            "intent": intent,
            "generic_preselection": generic_preselection,
        },
        "unobservable": [
            "host or system-prompt priority",
            "private model reasoning",
            "whether XRefKit overrode a host-selected Skill",
        ],
        "assessment": {"status": status, "reasons": reasons, "next_action": next_action},
    }


def cmd_host_precheck(args: argparse.Namespace) -> int:
    try:
        spec = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(spec, Mapping):
            raise ValueError("input JSON must be an object")
        report = build_precheck_report(spec)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "invalid", "error": str(exc)}, ensure_ascii=False))
        return 1
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["assessment"]["status"] == "pass" else 1
