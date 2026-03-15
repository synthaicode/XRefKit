<!-- xid: 8B31F02A4002 -->
<a id="xid-8B31F02A4002"></a>

# Manufacturing Workflow

This workflow defines how implementation and unit testing are orchestrated inside an approved scope.

## Purpose

Produce code changes and unit-test results without crossing the approved design boundary.

## Sequence

1. Confirm the approved design or equivalent scoped instruction.
2. Run [CAP-MFG-001 Implementation](../capabilities/manufacturing/100_cap_mfg_001_implementation.md#xid-1A12C5C61269).
3. Run [CAP-MFG-002 Unit Test Execution](../capabilities/manufacturing/110_cap_mfg_002_unit_test_execution.md#xid-55CC9027ACAD).
4. Run [CAP-MFG-004 Manufacturing Self Check](../capabilities/manufacturing/120_cap_mfg_004_manufacturing_self_check.md#xid-6F5A9C1B4401).
5. Hand off implementation results to QA review.
6. Record unresolved items and out-of-scope items for control handling.

## Inputs

- approved design or equivalent explicit scope
- target paths
- coding and naming rules
- optional test viewpoints from investigation or design

## Outputs

- implemented code
- unit test results
- self-check result
- unresolved list
- uncertainty list
- out-of-scope list

## Control Rules

- Manufacturing does not change design policy.
- Manufacturing stays inside the approved boundary.
- Manufacturing performs an internal design-alignment self-check before external QA review.
- Unresolved items must remain explicit.
- Out-of-scope items must preserve reasons for escalation.

## Related Skills

- [implementation_flow](../skills/implementation_flow/SKILL.md#xid-0ACF69A599D3)
- [manufacturing_self_check](../skills/manufacturing_self_check/SKILL.md#xid-5D4E91B0D110)
- [qa_gate_review](../skills/qa_gate_review/SKILL.md#xid-09B250B1A8FB)
- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)
