<!-- xid: D216FD3C726C -->
<a id="xid-D216FD3C726C"></a>

# Skill: release_planning_flow

## Purpose

Execute `CAP-OPS-001 -> CAP-OPS-002 -> CAP-OPS-003 -> CAP-OPS-004 -> CAP-OPS-005` and prepare release materials and procedures for CAB.

## Required Capability Definitions (XID)

- [CAP-OPS-001 Release Material Structuring](../../capabilities/operations/100_cap_ops_001_release_plan_draft_creation.md#xid-9715BACE7EB8)
- [CAP-OPS-002 Operational Signal Specification](../../capabilities/operations/110_cap_ops_002_monitoring_design.md#xid-316B0FB4493C)
- [CAP-OPS-003 Event Response Structuring](../../capabilities/operations/120_cap_ops_003_event_response_procedure_draft.md#xid-6DA033B45D93)
- [CAP-OPS-004 Operational Readiness Evaluation](../../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3)
- [CAP-OPS-005 Release Verification](../../capabilities/operations/140_cap_ops_005_release_verification.md#xid-83140C9538B4)

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
