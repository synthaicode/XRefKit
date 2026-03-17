<!-- xid: 8B31F02A4007 -->
<a id="xid-8B31F02A4007"></a>

# Release Planning Workflow

This workflow defines how release-plan materials are prepared after manufacturing and testing.

## Purpose

Prepare release planning, monitoring, and response procedures before CAB review.

## Group Interaction

| Item | Value |
|------|------|
| Owner group | Operations Group |
| Input from | Manufacturing outputs, Design materials, Requirement materials, performance evidence |
| Output to | CAB evaluation workflow |
| Main handoff artifacts | release plan draft, monitoring specification, event-response procedure draft, operational readiness result |
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

## Sequence

1. Perform release plan draft creation by applying [CAP-OPS-001 Release Material Structuring](../capabilities/operations/100_cap_ops_001_release_plan_draft_creation.md#xid-9715BACE7EB8).
2. Perform monitoring design by applying [CAP-OPS-002 Operational Signal Specification](../capabilities/operations/110_cap_ops_002_monitoring_design.md#xid-316B0FB4493C).
3. Perform event-response procedure drafting by applying [CAP-OPS-003 Event Response Structuring](../capabilities/operations/120_cap_ops_003_event_response_procedure_draft.md#xid-6DA033B45D93).
4. Perform operational readiness gate by applying [CAP-OPS-004 Operational Readiness Evaluation](../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3).

## Related Skills

- [release_planning_flow](../skills/release_planning_flow/SKILL.md#xid-D216FD3C726C)
- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)

