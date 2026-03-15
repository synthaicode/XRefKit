<!-- xid: 33D0A3A01B47 -->
<a id="xid-33D0A3A01B47"></a>

# Skill: cab_review_flow

## Purpose

Execute CAB-facing evaluation using `CAP-QA-003`, `CAP-OPS-004`, and `CAP-BIZ-001`.

## Required Capability Definitions (XID)

- [CAP-QA-003 Release Plan Suitability Review](../../capabilities/quality/120_cap_qa_003_release_plan_suitability_review.md#xid-93E53EF38700)
- [CAP-OPS-004 Operational Readiness Gate](../../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3)
- [CAP-BIZ-001 Value and Constraint Fit Evaluation](../../capabilities/business/100_cap_biz_001_value_constraint_fit_evaluation.md#xid-837CDB1183C9)

## Inputs

- release plan materials
- manufacturing outputs
- design and requirement evidence
- value, constraint, and priority definitions

## Outputs

- quality-gate result
- operational readiness result
- value-gate result
- unresolved list

## Startup

- Confirm CAB input materials exist.
- Confirm design, requirement, and value evidence exists.
- Record `unknown` if required evidence is missing.

## Planning

- Define the CAB evaluation scope.
- Prepare management rows for quality, operations, business, and unresolved risk items.

## Execution

- Evaluate release-plan suitability from the quality perspective.
- Evaluate operational readiness.
- Evaluate value and constraint fit.
- Return the three results with explicit evidence and unresolved items.

## Monitoring and Control

- Check that each CAB gate has a recorded result.
- Downgrade unsupported judgments to `unknown`.
- Preserve explicit unresolved risks.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the three gate results to the human decision layer.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Evaluate only; do not decide final release approval.
- Every judgment must cite evidence.
- Preserve unresolved risks explicitly.
