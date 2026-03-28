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
- [Design Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `test plan drafting` is a business activity in test work.
- This capability is the reusable test-plan structuring ability used by that activity.

## Task Lifecycle Mapping

- Startup:
  - use `Preconditions`, `Trigger`, and `Inputs` to confirm the capability can start
  - if required evidence is missing, record `unknown` before continuing
- Planning:
  - define test-plan targets, work rows, and handoff boundaries for this capability
- Execution:
  - produce the outputs defined in this capability within its stated constraints
- Monitoring and Control:
  - check progress and evidence quality through management-table and metrics rules
  - downgrade weakly supported conclusions to `unknown`
- Closure:
  - confirm the capability result is finalized as `done`, `unknown`, or `out_of_scope`
  - preserve unresolved and out-of-scope items for handoff or escalation
