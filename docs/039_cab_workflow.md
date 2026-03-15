<!-- xid: 8B31F02A4008 -->
<a id="xid-8B31F02A4008"></a>

# CAB Workflow

This workflow defines how quality, operational, and business evaluations are assembled before a human release decision.

## Purpose

Produce CAB evaluation outputs without collapsing the separation between evaluation and decision.

## Sequence

1. Run [CAP-QA-003 Release Plan Suitability Review](../capabilities/quality/120_cap_qa_003_release_plan_suitability_review.md#xid-93E53EF38700).
2. Run [CAP-OPS-004 Operational Readiness Gate](../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3).
3. Run [CAP-BIZ-001 Value and Constraint Fit Evaluation](../capabilities/business/100_cap_biz_001_value_constraint_fit_evaluation.md#xid-837CDB1183C9).
4. Hand the evaluation results to the human decision layer.

## Related Skills

- [cab_review_flow](../skills/cab_review_flow/SKILL.md#xid-33D0A3A01B47)

