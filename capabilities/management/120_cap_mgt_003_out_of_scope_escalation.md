<!-- xid: 1E3B2AA5B328 -->
<a id="xid-1E3B2AA5B328"></a>

# Capability: CAP-MGT-003 Out-of-Scope Escalation

## Definition

- capability_id: `CAP-MGT-003`
- capability_name: `out_of_scope_escalation`
- work_type: `management`
- summary: escalate out-of-scope items after closure checks so they can be reassigned or explicitly handled

## Preconditions

- at least one management-table row or result item is marked `out_of_scope`
- closure check has completed or equivalent control review exists

## Trigger

- task closure
- explicit out-of-scope handoff event

## Inputs

- out-of-scope list with reasons
- current owner or originating group
- optional suggested next owner

## Outputs

- escalation report
- reassignment request
- escalation record

## Required Domain Knowledge

- `../../knowledge/organization/110_management_table_schema.md#xid-7A2F4C8D1101`

## Constraints

- report and route only
- do not decide final reassignment policy by itself
- preserve original reason and evidence gap

## Assignment

- [All Groups](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- execution management role
- [Coordinator](../../docs/040_group_definitions.md#xid-8B31F02A4009) handoff path
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


