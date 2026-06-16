<!-- xid: A365F4499AA7 -->
<a id="xid-A365F4499AA7"></a>

# Capability: CAP-MGT-001 Execution Management

## Definition

- capability_id: `CAP-MGT-001`
- capability_name: `execution_management`
- work_type: `management`
- summary: initialize and maintain the management table for active work

## Preconditions

- a plan, scoped work list, or equivalent task set exists

## Trigger

- a phase starts
- a new task or target is added

## Inputs

- plan or scoped task list
- target list
- management table schema

## Outputs

- initialized or updated management table
- progress notes
- return instructions when follow-up is required

## Required Domain Knowledge

- `../../knowledge/organization/110_management_table_schema.md#xid-7A2F4C8D1101`

## Constraints

- manage state only
- do not judge deliverable quality
- preserve unresolved rows explicitly

## Assignment

- [All Groups](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- execution management role
