<!-- xid: 0ACF69A599D3 -->
<a id="xid-0ACF69A599D3"></a>

# Skill: implementation_flow

## Purpose

Execute the manufacturing sequence `CAP-MFG-001 -> CAP-MFG-002` and prepare output for QA review.

## Required Capability Definitions (XID)

- [CAP-MFG-001 Scoped Code Realization](../../capabilities/manufacturing/100_cap_mfg_001_implementation.md#xid-1A12C5C61269)
- [CAP-MFG-002 Unit-Level Verification](../../capabilities/manufacturing/110_cap_mfg_002_unit_test_execution.md#xid-55CC9027ACAD)

## Inputs

- approved design or equivalent scoped instruction
- design basis policy reference
- test design
- test design basis policy reference
- target paths
- coding and naming rules
- optional test viewpoints

## Required Knowledge (XID)

- [Implementation assumption gap handling](../../knowledge/organization/150_implementation_assumption_gap_handling.md#xid-7A2F4C8D1501)

## Outputs

- implemented code
- unit test results
- unresolved list
- uncertainty list
- out-of-scope list
- implementation basis design reference

## Startup

- Confirm approved scope exists.
- Confirm target files are identified.
- Confirm coding rules are available.
- Record `unknown` if required evidence is missing.

## Planning

- Define the implementation targets and test targets.
- Map each business activity to its supporting capability:
  - implementation -> `CAP-MFG-001`
  - unit test execution -> `CAP-MFG-002`
- Define the step order: `CAP-MFG-001 -> CAP-MFG-002`.
- Prepare management rows for code changes, tests, and unresolved items.

## Execution

- Perform implementation by executing `CAP-MFG-001`.
- Perform unit test execution by executing `CAP-MFG-002`.
- Record which design artifact or design basis reference each implementation change realizes.
- Record which test design item each executed unit test realizes.
- When an implementation assumption gap appears, classify it as:
  - `clarification_needed`
  - `evidence_missing`
  - `scope_conflict`
  - `local_choice_allowed`
- Record the gap using the implementation assumption gap handling rule.
- Record `unknown` and `out_of_scope` where needed.

## Monitoring and Control

- Check that every target file or change area has a recorded state.
- Check that every implementation assumption gap has a recorded classification and handling result.
- Downgrade weakly supported completion claims to `unknown`.
- Preserve explicit reasons for `out_of_scope` items.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off code, test results, and implementation basis design reference to QA review.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Never change design policy inside this skill.
- Never hide unresolved items.
- Never resolve an implementation assumption gap by guessing design or business intent.
- Every out-of-scope item must include a reason.
- Keep changes traceable to explicit scope.
- Keep executed unit tests traceable to explicit test design.
