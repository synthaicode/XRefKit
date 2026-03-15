<!-- xid: AFEB172B97D8 -->
<a id="xid-AFEB172B97D8"></a>

# Capability: CAP-QA-004 Management Table Check

## Definition

- capability_id: `CAP-QA-004`
- capability_name: `management_table_check`
- work_type: `management`
- summary: inspect the management table for leaks, return items, and closure readiness

## Preconditions

- a management table exists

## Trigger

- periodic control check during execution
- before a group output is finalized
- during task closure

## Inputs

- management table
- management table schema
- metrics definition when confidence or context state must be interpreted

## Outputs

- leak detection result
- return instructions
- closure confirmation result

## Required Domain Knowledge

- `../../knowledge/organization/110_management_table_schema.md#xid-7A2F4C8D1101`
- `../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201`

## Constraints

- inspect state only
- do not rewrite judgment content itself
- do not accept unresolved risk by itself

## Assignment

- [All Groups](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- quality-control role
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


