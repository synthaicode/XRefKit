<!-- xid: 3D7A91B54210 -->
<a id="xid-3D7A91B54210"></a>

# Skill: design_flow

## Purpose

Execute `CAP-DSN-001` and prepare implementation-ready design artifacts from planning outputs.

## Required Capability Definitions (XID)

- [CAP-DSN-001 Solution Design Structuring](../../capabilities/design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501)
- [CAP-DSN-002 Test Design Structuring](../../capabilities/design/110_cap_dsn_002_test_design_structuring.md#xid-6C1A2D9F4502)
- [CAP-DSN-003 Integration and Regression Test Design Structuring](../../capabilities/design/120_cap_dsn_003_integration_regression_test_design_structuring.md#xid-6C1A2D9F4503)

## Required Knowledge (XID)

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)

## Inputs

- approved requirements
- work plan
- source modification policy
- data change policy
- test policy
- planning basis source list

## Outputs

- approved design
- target paths
- source modification design
- data change design
- test design
- design basis policy reference
- test design basis policy reference
- integration regression test design
- integration regression test basis policy reference

## Startup

- Confirm planning outputs exist.
- Confirm source modification policy and work plan are approved.
- Record `unknown` if required design inputs are missing.

## Planning

- Define design scope and handoff boundaries.
- Map the business activity to its supporting capability:
  - solution design drafting -> `CAP-DSN-001`
  - test design drafting -> `CAP-DSN-002`
  - integration and regression test design drafting -> `CAP-DSN-003`
- Prepare management rows for design outputs and unresolved assumptions.

## Execution

- Perform solution design drafting by executing `CAP-DSN-001`.
- Perform test design drafting by executing `CAP-DSN-002`.
- Perform integration and regression test design drafting by executing `CAP-DSN-003`.
- Record which planning policy and planning basis source entry each design artifact realizes.
- Produce implementation-ready design artifacts and preserve unresolved design assumptions explicitly.

## Monitoring and Control

- Check that all required design areas have a recorded result.
- Downgrade weakly supported design assumptions to `unknown`.
- Preserve unresolved design constraints for manufacturing handoff.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the approved design package, design basis policy reference, test design basis policy reference, integration regression test basis policy reference, and unresolved design items.
- Escalate out-of-scope design questions when reassignment is required.

## Rules

- Do not redefine business scope.
- Do not start manufacturing changes in this skill.
