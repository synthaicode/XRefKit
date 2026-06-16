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
