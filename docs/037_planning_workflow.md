<!-- xid: 8B31F02A4006 -->
<a id="xid-8B31F02A4006"></a>

# Planning Workflow

This workflow defines how approved requirements are converted into executable plan drafts.

## Purpose

Prepare task decomposition, execution order, and group assignment drafts before implementation starts.

## Group Interaction

| Item | Value |
|------|------|
| Owner group | Design Group |
| Input from | approved requirements from Planning Group |
| Output to | Manufacturing Group execution work and management control initialization |
| Main handoff artifacts | task list, dependency map, execution order, effort estimate, group assignment draft |
| Escalation path | unresolved planning assumptions remain explicit; scope conflicts go to Coordinator routing |

## Business Activities and Supporting Capabilities

- Task decomposition and plan drafting:
  - supported by [CAP-PLN-001 Work Decomposition Structuring](../capabilities/planning/100_cap_pln_001_task_decomposition_plan_draft.md#xid-F5193313AB79)

## Sequence

1. Confirm requirements are approved.
2. Perform task decomposition and plan drafting by applying [CAP-PLN-001 Work Decomposition Structuring](../capabilities/planning/100_cap_pln_001_task_decomposition_plan_draft.md#xid-F5193313AB79).
3. Initialize management control for the resulting task and target lists.

## Related Skills

- [planning_flow](../skills/planning_flow/SKILL.md#xid-486C9EEE8A9D)
- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)

