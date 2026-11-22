"""Coordinate a verified Brownfield design finding."""

OUTCOMES = {"IMPLEMENTATION_FIX", "DESIGN_REVIEW_REQUIRED", "INVESTIGATION_REQUIRED"}
IDENTITY = ("work_item_id", "work_revision", "finding_id")


def receive_finding(finding, *, work_item_id, work_revision, existing_findings=()):
    """Prepare a PM action from the current work and existing persisted findings.

    The caller resolves and verifies the source Handoff and current records.
    Persist under the existing guarded update route, re-reading on conflict.
    """
    if finding.get("schema") != "brownfield.design_finding/v1":
        raise ValueError("unsupported Brownfield finding")
    required = (*IDENTITY, "source_run_id", "observation", "cause", "rationale", "next_phase")
    if any(not isinstance(finding.get(key), str) or not finding[key].strip() for key in required):
        raise ValueError("incomplete finding identity or rationale")
    if (finding["work_item_id"], finding["work_revision"]) != (work_item_id, work_revision):
        raise ValueError("finding does not match the current Work Item revision")
    for key in ("evidence_refs", "principle_refs", "policy_gaps", "related_issues",
                "approval_roles", "unknowns"):
        if not isinstance(finding.get(key), list):
            raise ValueError(f"invalid finding field: {key}")
    outcome = finding.get("outcome")
    if outcome not in OUTCOMES or finding.get("confidence") not in ("low", "medium", "high"):
        raise ValueError("invalid Brownfield disposition")
    if outcome == "INVESTIGATION_REQUIRED":
        if not finding["unknowns"]:
            raise ValueError("investigation requires explicit gaps")
    elif not finding["evidence_refs"] or finding["confidence"] == "low":
        raise ValueError("insufficient evidence for the submitted disposition")

    identity = tuple(finding[key] for key in IDENTITY)
    for existing in existing_findings:
        if tuple(existing[key] for key in IDENTITY) == identity:
            if existing != finding:
                raise ValueError("the current finding identity has conflicting contents")
            return {"action": "reuse", "finding_identity": identity}

    return {
        "action": {
            "IMPLEMENTATION_FIX": "coordinate_existing_execution",
            "DESIGN_REVIEW_REQUIRED": "hold_execution_and_request_reevaluation",
            "INVESTIGATION_REQUIRED": "coordinate_evidence_collection",
        }[outcome],
        "finding_identity": identity,
        "finding": finding,
        "related_issues_to_check": finding["related_issues"],
        "resolve_approval_owner": outcome == "DESIGN_REVIEW_REQUIRED" and not finding["approval_roles"],
    }


def resume_blockers(
    *, verified_current_design, verified_required_approval, impact_reviewed,
    acceptance_current, hold_resolved, work_start_authorized,
):
    """Identify unmet prerequisites; the caller resolves applicable authority."""
    checks = {
        "current_design": verified_current_design,
        "required_approval": verified_required_approval,
        "impact_review": impact_reviewed,
        "current_acceptance": acceptance_current,
        "hold_resolution": hold_resolved,
        "work_start_authority": work_start_authorized,
    }
    return tuple(check for check, result in checks.items() if result is not True)
