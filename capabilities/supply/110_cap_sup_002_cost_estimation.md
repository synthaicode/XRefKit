<!-- xid: 754A17D69C7C -->
<a id="xid-754A17D69C7C"></a>

# Capability: CAP-SUP-002 Cost Pattern Projection

## Definition

- capability_id: `CAP-SUP-002`
- capability_name: `cost_pattern_projection`
- work_type: `execution`
- summary: estimate service cost patterns and identify budget-overrun risk

## Preconditions

- output from `CAP-SUP-001` exists
- budget definition exists

## Trigger

- supplier condition check completes

## Inputs

- request size assumptions
- supplier cost conditions
- budget definition

## Outputs

- cost estimate patterns
- budget-overrun risk list
- uncertainty list

## Required Domain Knowledge

- budget definitions
- supplier cost conditions

## Constraints

- estimate and compare patterns only
- do not decide final budget ceiling
- preserve assumption gaps explicitly

## Assignment

- estimation phase
- [Planning Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `cost estimation` is a business activity in estimation work.
- This capability is the reusable cost-projection ability used by that activity.
