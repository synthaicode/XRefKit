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
- test viewpoints or equivalent expectations exist

## Trigger

- `CAP-MFG-001` completes

## Inputs

- implemented code
- test viewpoints
- coding rules

## Outputs

- unit test results
- unresolved list
- uncertainty list

## Required Domain Knowledge

- test design criteria
- coding rules

## Constraints

- test only within approved design scope
- do not redefine test criteria
- record unresolved failures explicitly

## Assignment

- manufacturing phase
- [Manufacturing Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `unit test execution` is a business activity in manufacturing work.
- This capability is the reusable unit-level verification ability used by that activity.
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


