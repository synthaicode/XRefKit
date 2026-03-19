<!-- xid: 8B31F02A4015 -->
<a id="xid-8B31F02A4015"></a>

# Design Workflow

This workflow defines how planning outputs are converted into implementation-ready design artifacts.

## Purpose

Prepare design artifacts and test design that realize approved planning policies before manufacturing starts.

## Group Interaction

| Item | Value |
|------|------|
| Owner group | Design Group |
| Input from | approved planning outputs from Design Group planning work, planning basis source list, approved requirements from Planning Group |
| Output to | Manufacturing Group execution work |
| Main handoff artifacts | approved design, target paths, source modification design, data change design, test design, design basis policy reference, test design basis policy reference, integration regression test design, integration regression test basis policy reference |
| Escalation path | unresolved design evidence remains explicit; scope conflicts go to Coordinator routing |

## Business Activities and Supporting Capabilities

- Solution design drafting:
  - supported by [CAP-DSN-001 Solution Design Structuring](../capabilities/design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501)
- Test design drafting:
  - supported by [CAP-DSN-002 Test Design Structuring](../capabilities/design/110_cap_dsn_002_test_design_structuring.md#xid-6C1A2D9F4502)
- Integration and regression test design drafting:
  - supported by [CAP-DSN-003 Integration and Regression Test Design Structuring](../capabilities/design/120_cap_dsn_003_integration_regression_test_design_structuring.md#xid-6C1A2D9F4503)

## Sequence

1. Confirm work plan and implementation policies are approved.
2. Perform solution design drafting by applying [CAP-DSN-001 Solution Design Structuring](../capabilities/design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501).
3. Perform test design drafting by applying [CAP-DSN-002 Test Design Structuring](../capabilities/design/110_cap_dsn_002_test_design_structuring.md#xid-6C1A2D9F4502).
4. Perform integration and regression test design drafting by applying [CAP-DSN-003 Integration and Regression Test Design Structuring](../capabilities/design/120_cap_dsn_003_integration_regression_test_design_structuring.md#xid-6C1A2D9F4503).
5. Record which planning policy and planning basis source entry each design artifact realizes.
6. Prepare approved design artifacts and target paths for manufacturing handoff.

## Related Skills

- [design_flow](../skills/design_flow/SKILL.md#xid-3D7A91B54210)
- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)
