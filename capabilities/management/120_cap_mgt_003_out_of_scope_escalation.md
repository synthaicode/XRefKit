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

- [All Groups](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)
- execution management role
- [Coordinator](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009) handoff path
