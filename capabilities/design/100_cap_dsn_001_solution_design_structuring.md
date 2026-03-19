<!-- xid: 6C1A2D9F4501 -->
<a id="xid-6C1A2D9F4501"></a>

# Capability: CAP-DSN-001 Solution Design Structuring

## Definition

- capability_id: `CAP-DSN-001`
- capability_name: `solution_design_structuring`
- work_type: `execution`
- summary: structure planning outputs into implementation-ready design artifacts

## Preconditions

- approved work plan exists
- approved source modification policy exists

## Trigger

- design phase starts

## Inputs

- approved requirements
- work plan
- source modification policy
- data change policy
- test policy
- planning basis source list

## Outputs

- approved design
- target paths
- source modification design
- data change design
- test design
- design basis policy reference

## Required Domain Knowledge

- architecture rules
- coding rules
- interface and data constraints

## Constraints

- realize planning policies without redefining business scope
- each design artifact must identify which planning policy and planning basis source entry it realizes
- preserve unresolved design assumptions explicitly
- do not start manufacturing decisions inside this capability

## Assignment

- design phase
- [Design Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `solution design drafting` is a business activity in design work.
- This capability is the reusable design-structuring ability used by that activity.

## Task Lifecycle Mapping

- Startup:
  - use `Preconditions`, `Trigger`, and `Inputs` to confirm the capability can start
  - if required evidence is missing, record `unknown` before continuing
- Planning:
  - define design targets, work rows, and handoff boundaries for this capability
- Execution:
  - produce the outputs defined in this capability within its stated constraints
- Monitoring and Control:
  - check progress and evidence quality through management-table and metrics rules
  - downgrade weakly supported conclusions to `unknown`
- Closure:
  - confirm the capability result is finalized as `done`, `unknown`, or `out_of_scope`
  - preserve unresolved and out-of-scope items for handoff or escalation
