<!-- xid: F5193313AB79 -->
<a id="xid-F5193313AB79"></a>

# Capability: CAP-PLN-001 Work Decomposition Structuring

## Definition

- capability_id: `CAP-PLN-001`
- capability_name: `work_decomposition_structuring`
- work_type: `execution`
- summary: decompose approved requirements into tasks, dependencies, and execution order

## Preconditions

- approved requirement definition exists

## Trigger

- planning phase starts

## Inputs

- approved requirements
- change target list

## Outputs

- task list
- dependency map
- execution order
- effort estimate
- group assignment draft

## Required Domain Knowledge

- process rules
- approval flow

## Constraints

- draft only
- do not decide final priority or resource allocation
- preserve unresolved planning assumptions explicitly

## Assignment

- planning phase
- [Design Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `task decomposition and plan draft` is a business activity in planning work.
- This capability is the reusable work-decomposition ability used by that activity.
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


