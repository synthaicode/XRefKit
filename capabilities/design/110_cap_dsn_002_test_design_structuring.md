<!-- xid: 6C1A2D9F4502 -->
<a id="xid-6C1A2D9F4502"></a>

# Capability: CAP-DSN-002 Test Design Structuring

## Definition

- capability_id: `CAP-DSN-002`
- capability_name: `test_design_structuring`
- work_type: `execution`
- summary: expand approved test policy, requirements, and design artifacts into executable test items with requirement traceability

## Preconditions

- approved test policy exists
- approved design or design draft exists

## Trigger

- test workflow reaches the test-item step

## Inputs

- test policy
- approved requirements
- approved design or design draft
- planning basis source list

## Outputs

- test design
- test design basis policy reference
- test-item requirement traceability reference

## Required Domain Knowledge

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)
- applicable domain knowledge for test conditions

## Constraints

- realize the approved test policy without silently changing its scope
- each test design artifact must identify which test policy, requirement, and design artifact it realizes
- preserve unresolved test assumptions explicitly

## Assignment

- test phase
- [Design Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `test item drafting` is a business activity in test work.
- This capability is the reusable test-design structuring ability used by that activity.
