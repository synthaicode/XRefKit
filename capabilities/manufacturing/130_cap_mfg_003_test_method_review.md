<!-- xid: 55CC9027ACAE -->
<a id="xid-55CC9027ACAE"></a>

# Capability: CAP-MFG-003 Test Method Review

## Definition

- capability_id: `CAP-MFG-003`
- capability_name: `test_method_review`
- work_type: `execution`
- summary: review test items against the internal realization approach and confirm feasible test methods before execution

## Preconditions

- test design exists
- approved design or equivalent implementation approach evidence exists

## Trigger

- test workflow reaches the manufacturing-review step

## Inputs

- test design
- approved design or design draft
- target paths when available
- source modification design when available

## Outputs

- manufacturing test review result
- unresolved list

## Required Domain Knowledge

- coding rules
- implementation structure knowledge
- applicable test execution constraints

## Constraints

- review test-method suitability only
- do not redefine requirements or business scope
- preserve unsupported or uncertain methods explicitly

## Assignment

- test phase review support
- [Manufacturing Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `manufacturing-side test-method review` is a business activity in test work.
- This capability exists so manufacturing knowledge can confirm feasible test methods without taking ownership of requirement intent.
