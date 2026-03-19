<!-- xid: 8B31F02A4006 -->
<a id="xid-8B31F02A4006"></a>

# Planning Workflow

This workflow defines how approved requirements are converted into executable plan drafts.

## Purpose

Prepare work planning and implementation policies before design starts, using domain knowledge and current-source analysis so the plan stays aligned with the existing codebase structure.

## Group Interaction

| Item | Value |
|------|------|
| Owner group | Design Group |
| Input from | approved requirements from Planning Group, investigation outputs, domain knowledge references, current-source findings |
| Output to | Design Group design work and management control initialization |
| Main handoff artifacts | work plan, source modification policy, data change policy, test policy, release policy, planning basis source list |
| Escalation path | unresolved planning assumptions remain explicit; scope conflicts go to Coordinator routing |

## Business Activities and Supporting Capabilities

- Work planning and policy drafting:
  - supported by [CAP-PLN-001 Work and Policy Planning Structuring](../capabilities/planning/100_cap_pln_001_task_decomposition_plan_draft.md#xid-F5193313AB79)

## Sequence

1. Confirm requirements are approved.
2. Read domain knowledge and current-source findings relevant to the target scope.
3. Perform work planning and policy drafting by applying [CAP-PLN-001 Work and Policy Planning Structuring](../capabilities/planning/100_cap_pln_001_task_decomposition_plan_draft.md#xid-F5193313AB79).
4. Keep source modification policy consistent with the current source structure unless a justified deviation is recorded.
5. Initialize management control for the resulting planning outputs and target lists.

## Outputs

- work plan
- source modification policy
- data change policy
- test policy
- release policy
- planning basis source list

## Control Rules

- Planning must read relevant domain knowledge before drafting policies.
- Planning must inspect current-source findings before defining source modification policy.
- Source modification policy should follow the current source structure by default.
- When a custom framework exists, planning must identify framework lifecycle, extension points, and convention rules before defining source modification policy.
- Planning must show which current source files, modules, registrations, or framework artifacts were used as the basis for each policy.
- Any planned structural deviation must include an explicit reason and downstream impact note.

## Related Skills

- [planning_flow](../skills/planning_flow/SKILL.md#xid-486C9EEE8A9D)
- [design_flow](../skills/design_flow/SKILL.md#xid-3D7A91B54210)
- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)

