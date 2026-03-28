<!-- xid: 62F9F44D7711 -->
<a id="xid-62F9F44D7711"></a>

# Skill: test_flow

## Purpose

Execute `CAP-DSN-004 -> CAP-DSN-002 -> CAP-DSN-003 -> CAP-MFG-003` and prepare a reviewed test package for manufacturing execution and quality verification.

## Required Capability Definitions (XID)

- [CAP-DSN-004 Test Plan Structuring](../../capabilities/design/130_cap_dsn_004_test_plan_structuring.md#xid-6C1A2D9F4504)
- [CAP-DSN-002 Test Design Structuring](../../capabilities/design/110_cap_dsn_002_test_design_structuring.md#xid-6C1A2D9F4502)
- [CAP-DSN-003 Integration and Regression Test Design Structuring](../../capabilities/design/120_cap_dsn_003_integration_regression_test_design_structuring.md#xid-6C1A2D9F4503)
- [CAP-MFG-003 Test Method Review](../../capabilities/manufacturing/130_cap_mfg_003_test_method_review.md#xid-55CC9027ACAE)

## Required Knowledge (XID)

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)

## Inputs

- approved requirements
- work plan
- test policy
- approved design
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
- Record `unknown` if required test evidence is missing.

## Planning

- Define test scope and handoff boundaries.
- Map the business activities to their supporting capabilities:
  - test plan drafting -> `CAP-DSN-004`
  - test item drafting -> `CAP-DSN-002`
  - integration and regression test design drafting -> `CAP-DSN-003`
  - manufacturing-side test-method review -> `CAP-MFG-003`
- Prepare management rows for test plans, test items, traceability, review findings, and unresolved assumptions.

## Execution

- Perform test plan drafting.
- Perform test item drafting with requirement traceability.
- Perform integration and regression test design drafting.
- Perform manufacturing-side test-method review.
- Record which requirement and design artifact each test item realizes.

## Monitoring and Control

- Check that each required test item has requirement traceability.
- Downgrade weakly supported test assumptions to `unknown`.
- Preserve unsupported test methods explicitly for redesign or escalation.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the reviewed test package to manufacturing and quality verification work.
- Escalate out-of-scope test questions when reassignment is required.

## Rules

- Do not redefine requirement intent.
- Do not redefine business scope.
- Manufacturing review confirms method suitability only.
