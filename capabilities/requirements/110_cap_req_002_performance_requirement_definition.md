<!-- xid: D67FAD650F8C -->
<a id="xid-D67FAD650F8C"></a>

# Capability: CAP-REQ-002 Performance Requirement Definition

## Definition

- capability_id: `CAP-REQ-002`
- capability_name: `performance_requirement_definition`
- work_type: `execution`
- summary: define performance requirements and load-test draft conditions

## Preconditions

- request exists
- supplier capacity conditions or existing performance data exist

## Trigger

- requirements phase includes performance concerns

## Inputs

- request
- existing performance information
- supplier capacity conditions

## Outputs

- performance requirement definition
- load-test draft plan

## Required Domain Knowledge

- supplier capacity conditions
- performance criteria

## Constraints

- define draft conditions only
- do not approve final technical validity
- preserve assumption gaps explicitly

## Assignment

- requirements phase
- [Planning Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- [Design Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)
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


