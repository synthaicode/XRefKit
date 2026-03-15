<!-- xid: 7A2F4C8D1101 -->
<a id="xid-7A2F4C8D1101"></a>

# Management Table Schema

This page defines the shared management table used to track work status across tasks and groups.

## Purpose

Use one row per `(work, target)` pair so completion, uncertainty, and out-of-scope handling are visible.

## Required Columns

| Column | Meaning |
|------|------|
| `work` | work item or capability step being executed |
| `target` | file, service, document, or other target under evaluation |
| `owner` | current responsible person or group |
| `status` | current state of the row |
| `evidence` | main basis used for the current state |
| `confidence` | confidence level for the current state |
| `context_usage` | context consumption estimate: `small`, `medium`, `large` |
| `notes` | unresolved detail, handoff note, or reason |

## Status Values

| Status | Meaning | Handling |
|------|------|------|
| `done` | in scope and resolved | hand off as normal output |
| `unknown` | in scope but unresolved | carry to uncertainty or unresolved list |
| `out_of_scope` | outside current scope | record reason and escalate if needed |
| `missing` | not yet processed or leak detected | return for follow-up before closure |

## Operational Rules

- Every row must end in `done`, `unknown`, or `out_of_scope` before task closure.
- `missing` is a control status, not a valid final status.
- Every `unknown` row must record the missing evidence.
- Every `out_of_scope` row must record the reason and likely next owner if known.
- If `confidence` is effectively low, upgrade the row to `unknown`.

## Closure Rules

1. Check that all rows have a final status.
2. Move unresolved `unknown` rows to the handoff list.
3. Move `out_of_scope` rows to escalation handling.
4. Preserve table state in the work-management record.
