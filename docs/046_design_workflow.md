<!-- xid: 8B31F02A4015 -->
<a id="xid-8B31F02A4015"></a>

# Design Workflow

This workflow defines how planning outputs are converted into implementation-ready design artifacts.

## Purpose

Prepare design artifacts that realize the approved source modification policy and related implementation constraints before manufacturing starts.

## Group Interaction

| Item | Value |
|------|------|
| Owner group | Design Group |
| Input from | approved planning outputs from Design Group planning work, planning basis source list, approved requirements from Planning Group |
| Output to | Manufacturing Group execution work |
| Main handoff artifacts | approved design, target paths, source modification design, data change design, test design, design basis policy reference |
| Escalation path | unresolved design evidence remains explicit; scope conflicts go to Coordinator routing |

## Business Activities and Supporting Capabilities

- Solution design drafting:
  - supported by [CAP-DSN-001 Solution Design Structuring](../capabilities/design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501)

## Sequence

1. Confirm work plan and implementation policies are approved.
2. Perform solution design drafting by applying [CAP-DSN-001 Solution Design Structuring](../capabilities/design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501).
3. Record which planning policy and planning basis source entry each design artifact realizes.
4. Prepare approved design artifacts and target paths for manufacturing handoff.

## Related Skills

- [design_flow](../skills/design_flow/SKILL.md#xid-3D7A91B54210)
- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)
