<!-- xid: 55CC9027ACAD -->
<a id="xid-55CC9027ACAD"></a>

# Capability: CAP-MFG-002 Unit-Level Verification

## Definition

- capability_id: `CAP-MFG-002`
- capability_name: `unit_level_verification`
- work_type: `execution`
- summary: execute unit tests for implemented code within design scope

## Preconditions

- implemented code from `CAP-MFG-001` exists
- test design or equivalent expectations exist

## Trigger

- `CAP-MFG-001` completes

## Inputs

- implemented code
- test design
- test design basis policy reference
- coding rules

## Outputs

- unit test results
- unresolved list
- uncertainty list
- unit test execution basis reference

## Required Domain Knowledge

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)
- coding rules

## Constraints

- test only within approved design scope
- do not redefine test criteria
- unit test execution must follow the provided test design unless an explicit deviation reason is recorded
- each executed unit test must identify which test design item and test-design basis reference it realizes
- record unresolved failures explicitly

## Assignment

- manufacturing phase
- [Manufacturing Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `unit test execution` is a business activity in manufacturing work.
- This capability is the reusable unit-level verification ability used by that activity.
