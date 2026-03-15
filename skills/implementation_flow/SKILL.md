<!-- xid: 0ACF69A599D3 -->
<a id="xid-0ACF69A599D3"></a>

# Skill: implementation_flow

## Purpose

Execute the manufacturing sequence `CAP-MFG-001 -> CAP-MFG-002` and prepare output for QA review.

## Required Capability Definitions (XID)

- [CAP-MFG-001 Implementation](../../capabilities/manufacturing/100_cap_mfg_001_implementation.md#xid-1A12C5C61269)
- [CAP-MFG-002 Unit Test Execution](../../capabilities/manufacturing/110_cap_mfg_002_unit_test_execution.md#xid-55CC9027ACAD)

## Inputs

- approved design or equivalent scoped instruction
- target paths
- coding and naming rules
- optional test viewpoints

## Outputs

- implemented code
- unit test results
- unresolved list
- uncertainty list
- out-of-scope list

## Startup

- Confirm approved scope exists.
- Confirm target files are identified.
- Confirm coding rules are available.
- Record `unknown` if required evidence is missing.

## Planning

- Define the implementation targets and test targets.
- Define the step order: `CAP-MFG-001 -> CAP-MFG-002`.
- Prepare management rows for code changes, tests, and unresolved items.

## Execution

- Execute `CAP-MFG-001` to implement the covered changes.
- Execute `CAP-MFG-002` to run or evaluate unit tests against the implemented scope.
- Record `unknown` and `out_of_scope` where needed.

## Monitoring and Control

- Check that every target file or change area has a recorded state.
- Downgrade weakly supported completion claims to `unknown`.
- Preserve explicit reasons for `out_of_scope` items.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off code and test results to QA review.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Never change design policy inside this skill.
- Never hide unresolved items.
- Every out-of-scope item must include a reason.
- Keep changes traceable to explicit scope.
