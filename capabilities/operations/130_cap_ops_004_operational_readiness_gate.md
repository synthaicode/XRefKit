<!-- xid: 83140C9538B3 -->
<a id="xid-83140C9538B3"></a>

# Capability: CAP-OPS-004 Operational Readiness Gate

## Definition

- capability_id: `CAP-OPS-004`
- capability_name: `operational_readiness_gate`
- work_type: `judgment`
- summary: evaluate whether release planning, monitoring, and response procedures are ready for CAB

## Preconditions

- outputs from `CAP-OPS-001`, `CAP-OPS-002`, and `CAP-OPS-003` exist

## Trigger

- CAB preparation starts

## Inputs

- release plan draft
- monitoring specification
- event-response procedure draft

## Outputs

- operational readiness result
- findings with evidence
- unresolved list

## Required Domain Knowledge

- acceptance criteria
- rollback criteria
- monitoring criteria

## Constraints

- evaluate only
- do not decide final release approval
- every judgment needs evidence

## Assignment

- CAB preparation
- [Operations Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)
## Task Lifecycle Mapping

- Startup:
  - use `Preconditions`, `Trigger`, and `Inputs` to confirm the capability can start
  - if required evidence is missing, record `unknown` before continuing
- Planning:
  - define targets, work rows, and handoff boundaries for this capability
- Execution:
  - produce the outputs defined in this capability within its stated constraints
- Monitoring and Control:
  - check progress and evidence quality through management-table and metrics rules
  - downgrade weakly supported conclusions to `unknown`
- Closure:
  - confirm the capability result is finalized as `done`, `unknown`, or `out_of_scope`
  - preserve unresolved and out-of-scope items for handoff or escalation

- execution metrics log
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)


