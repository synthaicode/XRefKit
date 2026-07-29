<!-- xid: D216FD3C726C -->
<a id="xid-D216FD3C726C"></a>

# Skill: release_planning_flow

## Purpose

Execute `CAP-OPS-001 -> CAP-OPS-002 -> CAP-OPS-003 -> CAP-OPS-004 -> CAP-OPS-005` and prepare release materials and procedures for CAB.

## Required Capability Definitions (XID)


## Inputs

- manufacturing outputs
- integration regression verification result
- release policy
- planning basis source list
- design materials
- requirement materials
- optional performance data

## Outputs

- test-environment release plan
- production-environment release plan
- release basis reference
- environment release basis reference
- release procedure draft
- release confirmation procedure draft
- rollback procedure draft
- monitoring specification
- event-response procedure draft
- operational readiness result
- release verification result
- release verification basis reference
- unresolved list

## Required Knowledge (XID)

- [IPA release activity catalog](../../knowledge/operations/100_ipa_release_activity_catalog.md#xid-7B3E5D1A6101)

## Startup

- Confirm manufacturing outputs exist.
- Confirm design and requirement materials exist.
- Confirm performance evidence exists when needed.
- Record `unknown` if required evidence is missing.

## Planning

- Define the release-planning scope.
- Map each business activity to its supporting capability:
  - release plan draft creation -> `CAP-OPS-001`
  - monitoring design -> `CAP-OPS-002`
  - event-response procedure drafting -> `CAP-OPS-003`
  - operational readiness gate -> `CAP-OPS-004`
  - release verification -> `CAP-OPS-005`
- Define the step order: `CAP-OPS-001 -> CAP-OPS-002 -> CAP-OPS-003 -> CAP-OPS-004 -> CAP-OPS-005`.
- Prepare management rows for planning, monitoring, response procedures, readiness findings, and release verification findings.

## Execution

- Draft the release plan.
- Split the release plan into test-environment and production-environment versions.
- Prepare release, release-confirmation, and rollback procedures as part of the release materials.
- Define placement confirmation steps and behavior confirmation steps inside the release-confirmation procedure.
- Record which release policy entry and planning basis source each environment-specific release plan realizes.
- Check IPA-derived release activity areas and keep missing areas explicit.
- Define monitoring and thresholds.
- Draft event-response procedures.
- Evaluate operational readiness with evidence.
- Evaluate release verification with evidence.
- Check that both placement confirmation evidence and behavior confirmation evidence are present.
- Record which release plan item, release confirmation procedure item, and release basis reference each release verification result confirms.

## Monitoring and Control

- Check that each required release-planning and release-verification artifact has a recorded state.
- Downgrade unsupported readiness conclusions to `unknown`.
- Preserve explicit operational evidence gaps.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off release materials, release basis references, and release verification basis reference to CAB.
- Escalate out-of-scope operational items when reassignment is required.

## Rules

- Do not approve final release timing.
- Do not approve final go/no-go.
- Every judgment in the readiness gate must cite evidence.

## Reporting Contract (共通報告)



- reporting_profile: phase_summary

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
