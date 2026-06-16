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
