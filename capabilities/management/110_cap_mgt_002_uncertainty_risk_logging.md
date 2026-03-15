<!-- xid: 9F14372D994A -->
<a id="xid-9F14372D994A"></a>

# Capability: CAP-MGT-002 Uncertainty and Risk Logging

## Definition

- capability_id: `CAP-MGT-002`
- capability_name: `uncertainty_and_risk_logging`
- work_type: `management`
- summary: record uncertainty, unresolved items, and execution metrics during work

## Preconditions

- active work execution exists

## Trigger

- `unknown`, `out_of_scope`, or unresolved findings occur
- a work step completes

## Inputs

- work result
- uncertainty or unresolved details
- metrics definition

## Outputs

- uncertainty list
- out-of-scope list
- metrics log

## Required Domain Knowledge

- `../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201`

## Constraints

- record only
- do not resolve or accept risk by itself
- preserve evidence gaps explicitly

## Assignment

- [All Groups](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- execution management role
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


