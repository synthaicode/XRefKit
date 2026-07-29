<!-- xid: 33D0A3A01B47 -->
<a id="xid-33D0A3A01B47"></a>

# Skill: cab_review_flow

## Purpose

Execute CAB-facing evaluation using `CAP-QA-003`, `CAP-OPS-004`, and `CAP-BIZ-001`.

## Required Capability Definitions (XID)


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
- Map each business activity to its supporting capability:
  - release plan suitability review -> `CAP-QA-003`
  - operational readiness gate -> `CAP-OPS-004`
  - value and constraint fit evaluation -> `CAP-BIZ-001`
- Prepare management rows for quality, operations, business, and unresolved risk items.

## Execution

- Evaluate release-plan suitability from the quality perspective.
- Evaluate operational readiness.
- Evaluate value and constraint fit.
- Return the three results with explicit evidence and unresolved items.

## Monitoring and Control

- Check that each CAB gate has a recorded result.
- Preserve explicit unresolved risks.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the three gate results to the human decision layer.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Evaluate only; do not decide final release approval.
- Every judgment must cite evidence.
- Preserve unresolved risks explicitly.

## Reporting Contract (共通報告)



- reporting_profile: phase_summary

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
