<!-- xid: 8B31F02A4003 -->
<a id="xid-8B31F02A4003"></a>

# Closure Workflow

This workflow defines how work is checked for leaks, confirmed for closure, and escalated when scope cannot be completed inside the current boundary.

## Purpose

Prevent silent leaks and ensure unresolved or out-of-scope items are explicitly handed off.

## Sequence

1. Inspect the management table and supporting metrics.
2. Run [CAP-QA-004 Management Table Check](../capabilities/quality/110_cap_qa_004_management_table_check.md#xid-AFEB172B97D8).
3. Confirm that all rows end in `done`, `unknown`, or `out_of_scope`.
4. Return leaked or incomplete rows for follow-up.
5. Run [CAP-MGT-003 Out-of-Scope Escalation](../capabilities/management/120_cap_mgt_003_out_of_scope_escalation.md#xid-1E3B2AA5B328) for remaining out-of-scope items.
6. Preserve closure confirmation and escalation records.

## Inputs

- management table
- metrics log when confidence or context must be interpreted
- unresolved and out-of-scope lists

## Outputs

- leak detection result
- return instructions
- closure confirmation result
- escalation record

## Control Rules

- `missing` is not a valid final state.
- Low-confidence results must not be treated as normal completion.
- Out-of-scope reasons must be preserved without rewriting them away.
- Closure requires explicit handling of unresolved and out-of-scope items.

## Related Skills

- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)

