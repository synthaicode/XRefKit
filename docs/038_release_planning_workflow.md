<!-- xid: 8B31F02A4007 -->
<a id="xid-8B31F02A4007"></a>

# Release Planning Workflow

This workflow defines how release materials, release procedures, and release confirmation procedures are prepared after manufacturing and testing.

## Purpose

Prepare the release materials and operating procedures needed for release execution, environment preparation, monitoring, rollback, and response before CAB review.

## Group Interaction

| Item | Value |
|------|------|
| Owner group | Operations Group |
| Input from | Manufacturing outputs, integration regression verification outputs, release policy, planning basis source list, Design materials, Requirement materials, performance evidence |
| Output to | CAB evaluation workflow |
| Main handoff artifacts | test-environment release plan, production-environment release plan, release basis reference, environment release basis reference, release procedure draft, release confirmation procedure draft, rollback procedure draft, monitoring specification, event-response procedure draft, operational readiness result, release verification result, release verification basis reference |
| Escalation path | operational gaps remain explicit as `unknown`; out-of-scope operational items go to Coordinator routing |

## Business Activities and Supporting Capabilities

- Release plan draft creation:
  - supported by [CAP-OPS-001 Release Material Structuring](../capabilities/operations/100_cap_ops_001_release_plan_draft_creation.md#xid-9715BACE7EB8)
- Monitoring design:
  - supported by [CAP-OPS-002 Operational Signal Specification](../capabilities/operations/110_cap_ops_002_monitoring_design.md#xid-316B0FB4493C)
- Event-response procedure drafting:
  - supported by [CAP-OPS-003 Event Response Structuring](../capabilities/operations/120_cap_ops_003_event_response_procedure_draft.md#xid-6DA033B45D93)
- Operational readiness gate:
  - supported by [CAP-OPS-004 Operational Readiness Evaluation](../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3)
- Release verification:
  - supported by [CAP-OPS-005 Release Verification](../capabilities/operations/140_cap_ops_005_release_verification.md#xid-83140C9538B4)

## Sequence

1. Perform release plan draft creation by applying [CAP-OPS-001 Release Material Structuring](../capabilities/operations/100_cap_ops_001_release_plan_draft_creation.md#xid-9715BACE7EB8).
2. Split release planning into test-environment release and production-environment release.
3. Prepare release, release-confirmation, and rollback procedures as part of the release materials.
4. Record which release policy entry and planning basis source each environment-specific release plan realizes.
5. Perform monitoring design by applying [CAP-OPS-002 Operational Signal Specification](../capabilities/operations/110_cap_ops_002_monitoring_design.md#xid-316B0FB4493C).
6. Perform event-response procedure drafting by applying [CAP-OPS-003 Event Response Structuring](../capabilities/operations/120_cap_ops_003_event_response_procedure_draft.md#xid-6DA033B45D93).
7. Perform operational readiness gate by applying [CAP-OPS-004 Operational Readiness Evaluation](../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3).
8. Perform release verification by applying [CAP-OPS-005 Release Verification](../capabilities/operations/140_cap_ops_005_release_verification.md#xid-83140C9538B4).

## Control Rules

- Release planning prepares release materials and procedures; it does not decide release approval.
- Release materials must include environment-specific release plans together with execution, confirmation, rollback, monitoring, and response procedures.
- Release confirmation procedures must include placement confirmation and behavior confirmation.

## Related Skills

- [release_planning_flow](../skills/release_planning_flow/SKILL.md#xid-D216FD3C726C)
- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)

## Required Knowledge

- [IPA release activity catalog](../knowledge/operations/100_ipa_release_activity_catalog.md#xid-7B3E5D1A6101)

