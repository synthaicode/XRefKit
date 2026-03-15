<!-- xid: D6DDBAC513BF -->
<a id="xid-D6DDBAC513BF"></a>

# Skill: management_table_control

## Purpose

Execute the control sequence `CAP-QA-004 -> CAP-MGT-003` to detect leaks, confirm closure readiness, and escalate out-of-scope items.

## Required Capability Definitions (XID)

- [CAP-QA-004 Management Table Check](../../capabilities/quality/110_cap_qa_004_management_table_check.md#xid-AFEB172B97D8)
- [CAP-MGT-003 Out-of-Scope Escalation](../../capabilities/management/120_cap_mgt_003_out_of_scope_escalation.md#xid-1E3B2AA5B328)

## Required Knowledge (XID)

- [Management table schema](../../knowledge/organization/110_management_table_schema.md#xid-7A2F4C8D1101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Inputs

- management table
- optional metrics log
- optional out-of-scope list

## Outputs

- leak detection result
- return instructions
- closure confirmation result
- escalation record for out-of-scope items when present

## Startup

- Confirm the management table exists.
- Confirm metrics are available when confidence or context needs interpretation.
- Record `unknown` if required control evidence is missing.

## Planning

- Define the control scope and target rows.
- Prepare management rows for leak detection, closure checks, and escalations.

## Execution

- Inspect each management-table row.
- Detect `missing` rows and unresolved control leaks.
- Verify final rows are `done`, `unknown`, or `out_of_scope`.
- Build an escalation record for remaining `out_of_scope` items.

## Monitoring and Control

- Re-check low-confidence rows using the metrics rules.
- Preserve reasons for every escalation item.
- Return incomplete rows for follow-up instead of forcing closure.

## Closure

- Confirm closure readiness or issue return instructions.
- Preserve the escalation record.
- Hand off closure and escalation results to the responsible layer.

## Rules

- Do not change underlying judgment content.
- Do not silently accept unresolved risk.
- Every escalation item must preserve its reason.
