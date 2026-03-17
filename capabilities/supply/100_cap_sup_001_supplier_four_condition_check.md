<!-- xid: 2DC9A90A6508 -->
<a id="xid-2DC9A90A6508"></a>

# Capability: CAP-SUP-001 External Service Condition Comparison

## Definition

- capability_id: `CAP-SUP-001`
- capability_name: `external_service_condition_comparison`
- work_type: `execution`
- summary: compare candidate external services against adoption, SLA, capacity, and cost conditions

## Preconditions

- supplier definitions exist
- the request includes new or existing external-service usage

## Trigger

- estimation phase starts for supplier or budget analysis

## Inputs

- request
- supplier definitions

## Outputs

- four-condition comparison result
- issue list
- uncertainty list

## Required Domain Knowledge

- supplier adoption conditions
- supplier SLA conditions
- supplier capacity conditions
- supplier cost conditions

## Constraints

- compare and list only
- do not decide adoption approval
- record unknown evidence gaps explicitly

## Assignment

- estimation phase
- [Planning Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `supplier four-condition check` is a business activity in estimation work.
- This capability is the reusable comparison ability used by that activity.
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


