<!-- xid: 62F9F44D7711 -->
<a id="xid-62F9F44D7711"></a>

# Skill: test_flow

## Purpose

Execute `CAP-DSN-004 -> CAP-DSN-002 -> CAP-DSN-003 -> CAP-MFG-003` and prepare a reviewed test package for manufacturing execution and quality verification.

## Required Capability Definitions (XID)


## Required Knowledge (XID)

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)

## Inputs

- approved requirements
- work plan
- test policy
- approved design
- design-to-test input package from `design_flow`
- XDDP traceability matrix or rows from the approved design package
- planning basis source list

## Outputs

- test plan
- test plan basis policy reference
- test design
- test design basis policy reference
- test-item requirement traceability reference
- integration regression test design
- integration regression test basis policy reference
- manufacturing test review result
- unresolved list

## Startup

- Confirm approved requirements, approved design, and test policy exist.
- Confirm the approved design includes the design-to-test input package and XDDP
  traceability rows needed to derive test scope, test items, integration or
  regression coverage, and verification handoff.
- Record `unknown` if required test evidence is missing.

## Planning

- Define test scope and handoff boundaries.
- Map the business activities to their supporting capabilities:
  - test plan drafting -> `CAP-DSN-004`
  - test item drafting -> `CAP-DSN-002`
  - integration and regression test design drafting -> `CAP-DSN-003`
  - manufacturing-side test-method review -> `CAP-MFG-003`
- Prepare management rows for test plans, test items, traceability, review findings, and unresolved assumptions.
- Use the design-to-test input package to seed test scope, test item candidates,
  integration/regression targets, DB verification points, and unknown or
  out-of-scope test questions.

## Execution

- Perform test plan drafting.
- Perform test item drafting with requirement traceability.
- Perform integration and regression test design drafting.
- Perform manufacturing-side test-method review.
- Record which requirement and design artifact each test item realizes.
- Record which XDDP traceability row, design item, and verification point each
  test item realizes.

## Monitoring and Control

- Check that each required test item has requirement traceability.
- Check that each design-to-test input row is covered by a test item,
  integration/regression test design row, explicit `unknown`, or explicit
  `out_of_scope` reason.
- Downgrade weakly supported test assumptions to `unknown`.
- Preserve unsupported test methods explicitly for redesign or escalation.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Confirm the reviewed test package traces back to the approved design package's
  XDDP traceability rows and design-to-test input package.
- Hand off the reviewed test package to manufacturing and quality verification work.
- Escalate out-of-scope test questions when reassignment is required.

## Rules

- Do not redefine requirement intent.
- Do not redefine business scope.
- Manufacturing review confirms method suitability only.
