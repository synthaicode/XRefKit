<!-- xid: 867B78FF702F -->
<a id="xid-867B78FF702F"></a>

# Capability: CAP-INV-001 Scope Classification

## Definition

- capability_id: `CAP-INV-001`
- capability_name: `scope_classification`
- work_type: `execution`
- summary: classify request scope into in-scope and out-of-scope targets using available catalog or equivalent domain evidence

## Preconditions

- a request exists
- a service catalog is available directly or through domain knowledge lookup

## Trigger

- investigation workflow step 1 starts

## Inputs

- request
- service catalog or equivalent service reference
- optional business-domain constraints

## Outputs

- in-scope service list
- out-of-scope service list with reasons
- uncertainty list for unresolved scope questions

## Required Domain Knowledge

- service catalog definitions
- business domain rules used to interpret the request
- scope classification criteria

## Constraints

- classify scope only
- do not decide implementation policy
- do not decide design policy
- record missing evidence as `unknown`

## Assignment

- investigation phase step 1
- [Planning Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- Workflow belongs in `docs/`.
- Executable procedure belongs in `skills/investigation_flow/`.
- Domain evidence belongs in `knowledge/`.
- `service catalog analysis` is a business activity in the investigation workflow.
- This capability is the reusable classification ability used by that activity.

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


