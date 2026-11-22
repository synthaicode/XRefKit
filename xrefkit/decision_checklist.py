"""Select and validate engineering design checks against resolved principles."""

import json
from pathlib import Path


DEFINITIONS = Path(__file__).with_name("resources") / "engineering-decision-checklist.json"
DECISION_TYPES = {
    "api_integration": "api",
    "state_management": "state",
    "concurrency": "concurrency",
    "architecture_change": "architecture",
    "security": "security",
}


def select(prepared, resolution):
    definitions = json.loads(DEFINITIONS.read_text(encoding="utf-8"))
    context = prepared["decision_context"]
    category = context["category"]
    groups = {"global"}
    if category in DECISION_TYPES:
        groups.add(DECISION_TYPES[category])
    if context["external_side_effects"] != "no":
        groups.add("api")
    if context["state_management"] != "no":
        groups.add("state")
    # A state decision always examines whether concurrent writers can exist.
    if context["concurrency"] != "no" or "state" in groups:
        groups.add("concurrency")

    references = prepared["context"]["references"]
    checks = {}
    for group in sorted(groups):
        for check_id, question, areas, *conditions in definitions["groups"][group]:
            related = (
                resolution["required"] if check_id == "GDC-04" else
                sorted(xid for xid, ref in references.items()
                       if set(areas).intersection(ref.get("discovery", {}).get("areas", [])))
            )
            applicable = not (conditions == ["no_concurrency"] and context["concurrency"] == "no"
                              and category != "concurrency")
            checks[check_id] = {
                "check_id": check_id, "category": group, "question": question,
                "applicability": {
                    "decision_types": [kind for kind, name in DECISION_TYPES.items() if name == group],
                    "conditions": conditions, "applies": applicable,
                },
                "related_xids": related, "required": True, "revision": definitions["revision"],
                "knowledge_gaps": areas if areas and not related else [],
            }
    return {"revision": definitions["revision"], "categories": sorted(groups), "checks": checks}


def pending(selection, results):
    return {check_id: results.get(check_id, {}).get("result", "MISSING")
            for check_id, check in selection["checks"].items() if check["required"]
            and results.get(check_id, {}).get("result") not in ("PASS", "NOT_APPLICABLE")}


def validate(prepared, resolution, proposal, verify_file, reference_set_sha256):
    selection = resolution["checklist"]
    envelope = proposal["checklist"]
    binding = {"decision_id": prepared["decision_id"], "reference_set_sha256": reference_set_sha256,
               "candidate": proposal["candidate"]}
    if (not isinstance(envelope, dict) or set(envelope) != binding.keys() | {"results"}
            or any(envelope[key] != value for key, value in binding.items())):
        raise ValueError("checklist must bind this decision, reference set and candidate artifact")
    results = envelope["results"]
    if not isinstance(results, dict) or results.keys() - selection["checks"].keys():
        raise ValueError("checklist results must refer to selected checks")
    references = prepared["context"]["references"]
    evaluators = set()
    for check_id, result in results.items():
        check = selection["checks"][check_id]
        if (not isinstance(result, dict) or set(result) != {
            "revision", "applicability", "result", "reason", "references", "evidence", "unresolved", "evaluator",
        } or result["revision"] != check["revision"]):
            raise ValueError(f"{check_id}: invalid checklist result or revision")
        status = result["result"]
        if status not in ("PASS", "FAIL", "NOT_APPLICABLE", "UNKNOWN"):
            raise ValueError(f"{check_id}: invalid checklist status")
        if any(not isinstance(result[key], str) or not result[key].strip() for key in ("reason", "evaluator")):
            raise ValueError(f"{check_id}: reason and evaluator are required")
        evaluators.add(result["evaluator"])
        na = status == "NOT_APPLICABLE"
        expected = "not_applicable" if na else "applies"
        if result["applicability"] != expected or na == check["applicability"]["applies"]:
            raise ValueError(f"{check_id}: applicability conflicts with required coverage")
        unresolved = result["unresolved"]
        if (not isinstance(unresolved, list) or any(not isinstance(x, str) or not x.strip() for x in unresolved)
                or (status in ("PASS", "NOT_APPLICABLE") and unresolved)
                or (status == "UNKNOWN" and not unresolved)):
            raise ValueError(f"{check_id}: unresolved items are inconsistent with checklist status")
        refs = result["references"]
        if not isinstance(refs, dict) or any(
            xid not in references or references[xid]["revision"] != revision for xid, revision in refs.items()
        ):
            raise ValueError(f"{check_id}: checklist XID references must match their resolved revisions")
        if check_id == "GDC-04" and status == "PASS" and set(resolution["required"]) - refs.keys():
            raise ValueError("GDC-04: required principle references are missing from checklist evidence")
        evidence = result["evidence"]
        if not isinstance(evidence, list) or (status in ("PASS", "FAIL") and not evidence):
            raise ValueError(f"{check_id}: checklist verification evidence is required")
        for proof in evidence:
            if not isinstance(proof, dict) or set(proof) != {"path", "sha256"}:
                raise ValueError(f"{check_id}: invalid checklist evidence")
            verify_file(proof["path"], proof["sha256"])
    remaining = pending(selection, results)
    if proposal["classification"] == "DETERMINED" and remaining:
        details = ", ".join(f"{check_id}={status}" for check_id, status in sorted(remaining.items()))
        raise ValueError(f"required checklist checks are unresolved: {details}")
    return evaluators
