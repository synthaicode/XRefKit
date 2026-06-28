<!-- xid: 6C1A2D9F4504 -->
<a id="xid-6C1A2D9F4504"></a>

# Capability: CAP-DSN-004 Test Plan Structuring

## Definition

- capability_id: `CAP-DSN-004`
- capability_name: `test_plan_structuring`
- work_type: `execution`
- summary: structure approved test policy and requirement context into an executable test plan

## Preconditions

- approved test policy exists
- approved requirements exist

## Trigger

- test workflow reaches the test-plan step

## Inputs

- test policy
- approved requirements
- approved design or design draft
- planning basis source list

## Outputs

- test plan
- test plan basis policy reference

## Required Domain Knowledge

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)
- applicable domain knowledge for test scope and risk selection

## Constraints

- realize the approved test policy without silently changing its scope
- preserve requirement coverage intent explicitly
- preserve unresolved test planning assumptions explicitly

## Assignment

- test phase
- [Design Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `test plan drafting` is a business activity in test work.
- This capability is the reusable test-plan structuring ability used by that activity.
