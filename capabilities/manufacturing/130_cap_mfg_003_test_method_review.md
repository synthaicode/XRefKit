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
- [Manufacturing Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `manufacturing-side test-method review` is a business activity in test work.
- This capability exists so manufacturing knowledge can confirm feasible test methods without taking ownership of requirement intent.

## Task Lifecycle Mapping

- Startup:
  - use `Preconditions`, `Trigger`, and `Inputs` to confirm the capability can start
  - if required evidence is missing, record `unknown` before continuing
- Planning:
  - define review targets, work rows, and handoff boundaries for this capability
- Execution:
  - produce the outputs defined in this capability within its stated constraints
- Monitoring and Control:
  - check progress and evidence quality through management-table and metrics rules
  - downgrade weakly supported conclusions to `unknown`
- Closure:
  - confirm the capability result is finalized as `done`, `unknown`, or `out_of_scope`
  - preserve unresolved and out-of-scope items for handoff or escalation
