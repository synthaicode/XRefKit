"""Record the evidence-backed judgment made during specification reconciliation."""

OUTCOMES = {
    "IMPLEMENTATION_DEFECT": "IMPLEMENTATION_FIX",
    "DESIGN_POLICY_MISSING": "DESIGN_REVIEW_REQUIRED",
    "DESIGN_POLICY_CONFLICT": "DESIGN_REVIEW_REQUIRED",
    "DESIGN_POLICY_INVALID": "DESIGN_REVIEW_REQUIRED",
    "INSUFFICIENT_EVIDENCE": "INVESTIGATION_REQUIRED",
    "REQUIREMENT_CHANGE": "DESIGN_REVIEW_REQUIRED",
}


def retry_disposition(
    *, failure, preconditions, transient, recovery_basis, effect,
    safe_replay, within_limits, can_continue_safely,
):
    """Evaluate explicit operation evidence; never dispatch a retry."""
    if failure == "authentication" or preconditions is False:
        return "stop"
    if failure == "contract_violation":
        return "evaluate_contract"
    if transient is False or within_limits is False or can_continue_safely is False:
        return "stop"
    if (preconditions is not True or transient is not True
            or not isinstance(recovery_basis, str) or not recovery_basis.strip()
            or within_limits is not True or can_continue_safely is not True):
        return "investigate"
    if effect not in ("not_executed", "no_side_effect") and safe_replay is not True:
        return "reconcile"
    return "bounded_retry"


def make_finding(
    *, work_item_id, work_revision, finding_id, source_run_id, observation,
    cause, evidence_refs, rationale, confidence, principle_refs=(),
    policy_gaps=(), related_issues=(), approval_roles=(), unknowns=(), engineering_decision_id=None,
):
    """Package the reviewer's explicit judgment without assigning authority."""
    texts = (work_item_id, work_revision, finding_id, source_run_id, observation, rationale)
    if any(not isinstance(value, str) or not value.strip() for value in texts):
        raise ValueError("finding identity, observation, and rationale are required")
    if engineering_decision_id is not None and (
        not isinstance(engineering_decision_id, str) or not engineering_decision_id.strip()
    ):
        raise ValueError("engineering decision ID must be nonempty text")
    if cause not in OUTCOMES or confidence not in ("low", "medium", "high"):
        raise ValueError("unknown cause or confidence")
    if cause != "INSUFFICIENT_EVIDENCE" and (not evidence_refs or confidence == "low"):
        raise ValueError("conclusive findings require evidence and sufficient confidence")
    if cause == "INSUFFICIENT_EVIDENCE" and not unknowns:
        raise ValueError("investigation requires explicit gaps")
    if cause == "IMPLEMENTATION_DEFECT" and not principle_refs:
        raise ValueError("implementation defect requires a traceable approved design basis")
    if cause.startswith("DESIGN_POLICY_") and not policy_gaps:
        raise ValueError("design-policy finding requires explicit policy gaps")
    for ref in principle_refs:
        if (not isinstance(ref, dict)
                or any(not isinstance(ref.get(key), str) or not ref[key].strip()
                       for key in ("ref", "revision", "applicability"))
                or "xid" not in ref
                or (ref["xid"] is not None
                    and (not isinstance(ref["xid"], str) or not ref["xid"].strip()))):
            raise ValueError("principle references require a revision and applicability basis")
    outcome = OUTCOMES[cause]
    return {
        "schema": "brownfield.design_finding/v1",
        "work_item_id": work_item_id, "work_revision": work_revision,
        "finding_id": finding_id, "source_run_id": source_run_id,
        "observation": observation, "cause": cause, "outcome": outcome,
        "rationale": rationale, "confidence": confidence,
        **({"engineering_decision_id": engineering_decision_id} if engineering_decision_id is not None else {}),
        "evidence_refs": list(evidence_refs), "principle_refs": list(principle_refs),
        "policy_gaps": list(policy_gaps), "related_issues": list(related_issues),
        "approval_roles": list(approval_roles), "unknowns": list(unknowns),
        "next_phase": "requirements" if cause == "REQUIREMENT_CHANGE" else {
            "IMPLEMENTATION_FIX": "manufacturing",
            "DESIGN_REVIEW_REQUIRED": "design",
            "INVESTIGATION_REQUIRED": "investigation",
        }[outcome],
    }
