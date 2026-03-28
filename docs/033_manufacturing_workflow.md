<!-- xid: 8B31F02A4002 -->
<a id="xid-8B31F02A4002"></a>

# Manufacturing Workflow

This workflow defines how implementation and unit testing are orchestrated inside an approved scope.

## Purpose

Produce code changes and unit-test results without crossing the approved design boundary.

## Group Interaction

| Item | Value |
|------|------|
| Owner group | Manufacturing Group |
| Input from | approved design and detailed design outputs from Design Group, reviewed test package from Test workflow, requirement context from Planning Group when needed |
| Output to | Quality Group review and Operations Group release-planning preparation |
| Main handoff artifacts | implemented code, unit test results, unit test execution basis reference, implementation basis design reference, self-check result, uncertainty list, out-of-scope list |
| Escalation path | implementation assumption gaps stay `unknown` or become `out_of_scope`; `out_of_scope` items go to Coordinator routing |

## Business Activities and Supporting Capabilities

- Implementation:
  - supported by [CAP-MFG-001 Scoped Code Realization](../capabilities/manufacturing/100_cap_mfg_001_implementation.md#xid-1A12C5C61269)
- Unit test execution:
  - supported by [CAP-MFG-002 Unit-Level Verification](../capabilities/manufacturing/110_cap_mfg_002_unit_test_execution.md#xid-55CC9027ACAD)
- Manufacturing self check:
  - supported by [CAP-MFG-004 Design Alignment Self Evaluation](../capabilities/manufacturing/120_cap_mfg_004_manufacturing_self_check.md#xid-6F5A9C1B4401)

## Sequence

1. Confirm the approved design or equivalent scoped instruction.
2. Perform implementation by applying [CAP-MFG-001 Scoped Code Realization](../capabilities/manufacturing/100_cap_mfg_001_implementation.md#xid-1A12C5C61269).
3. Perform unit test execution by applying [CAP-MFG-002 Unit-Level Verification](../capabilities/manufacturing/110_cap_mfg_002_unit_test_execution.md#xid-55CC9027ACAD).
4. Perform manufacturing self check by applying [CAP-MFG-004 Design Alignment Self Evaluation](../capabilities/manufacturing/120_cap_mfg_004_manufacturing_self_check.md#xid-6F5A9C1B4401).
5. Hand off implementation results to QA review.
6. Record unresolved items and out-of-scope items for control handling.

## Inputs

- approved design or equivalent explicit scope
- source modification design
- data change design when applicable
- test plan when needed
- test design or explicit test viewpoints
- test design basis policy reference
- test-item requirement traceability reference
- manufacturing test review result
- target paths
- coding and naming rules
- optional test viewpoints from investigation or design

## Outputs

- implemented code
- unit test results
- unit test execution basis reference
- self-check result
- implementation basis design reference
- unresolved list
- uncertainty list
- out-of-scope list

## Control Rules

- Manufacturing does not change design policy.
- Manufacturing stays inside the approved boundary.
- Manufacturing performs a group-internal self-check within the manufacturing responsibility boundary before external QA review.
- That self-check covers only manufacturing-owned work:
  - implementation result
  - unit-test result
  - implementation assumption-gap handling
- Manufacturing must preserve traceability from each code change back to the design artifact or design basis reference it implements.
- Manufacturing must preserve traceability from each executed unit test back to the reviewed test item and requirement reference it realizes.
- Implementation assumption gaps must be recorded and classified before closure.
- Unresolved items must remain explicit.
- Out-of-scope items must preserve reasons for escalation.

## Related Skills

- [implementation_flow](../skills/implementation_flow/SKILL.md#xid-0ACF69A599D3)
- [manufacturing_self_check](../skills/manufacturing_self_check/SKILL.md#xid-5D4E91B0D110)
- [qa_gate_review](../skills/qa_gate_review/SKILL.md#xid-09B250B1A8FB)
- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)
