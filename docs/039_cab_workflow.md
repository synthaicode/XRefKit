<!-- xid: 8B31F02A4008 -->
<a id="xid-8B31F02A4008"></a>

# CAB Workflow

This workflow defines how quality, operational, and business evaluations are assembled before a human release decision.

## Purpose

Produce CAB evaluation outputs without collapsing the separation between evaluation and decision.

## Group Interaction

| Item | Value |
|------|------|
| Owner group | Quality Group, Operations Group, and Planning Group each within its own evaluation boundary |
| Input from | release-planning materials, manufacturing outputs, requirement and design evidence, value and constraint definitions |
| Output to | human decision layer and system quality feedback loop when rejection indicates an upstream structural issue |
| Main handoff artifacts | quality-gate result, operational readiness result, value-gate result, unresolved list, structural quality feedback record when needed |
| Escalation path | unresolved risks remain explicit for human decision; scope reassignment still goes through Coordinator routing; upstream structural causes go to the system quality feedback loop |

## Business Activities and Supporting Capabilities

- Release plan suitability review:
  - supported by [CAP-QA-003 Release Plan Suitability Review](../capabilities/quality/120_cap_qa_003_release_plan_suitability_review.md#xid-93E53EF38700)
- Operational readiness gate:
  - supported by [CAP-OPS-004 Operational Readiness Evaluation](../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3)
- Value and constraint fit evaluation:
  - supported by [CAP-BIZ-001 Value-Constraint Alignment Evaluation](../capabilities/business/100_cap_biz_001_value_constraint_fit_evaluation.md#xid-837CDB1183C9)

## Sequence

1. Perform release plan suitability review by applying [CAP-QA-003 Release Plan Suitability Review](../capabilities/quality/120_cap_qa_003_release_plan_suitability_review.md#xid-93E53EF38700).
2. Perform operational readiness gate by applying [CAP-OPS-004 Operational Readiness Evaluation](../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3).
3. Perform value and constraint fit evaluation by applying [CAP-BIZ-001 Value-Constraint Alignment Evaluation](../capabilities/business/100_cap_biz_001_value_constraint_fit_evaluation.md#xid-837CDB1183C9).
4. Hand the evaluation results to the human decision layer.
5. If rejection or conditional approval reveals an upstream structural quality issue, emit a system quality feedback record.

## Related Skills

- [cab_review_flow](../skills/cab_review_flow/SKILL.md#xid-33D0A3A01B47)

## Related

- [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012)

