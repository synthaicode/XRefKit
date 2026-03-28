<!-- xid: 3D7A91B54210 -->
<a id="xid-3D7A91B54210"></a>

# Skill: design_flow

## Purpose

Execute `CAP-DSN-001` and prepare implementation-ready solution-design artifacts from planning outputs.

## Required Capability Definitions (XID)

- [CAP-DSN-001 Solution Design Structuring](../../capabilities/design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501)

## Inputs

- approved requirements
- work plan
- source modification policy
- data change policy
- planning basis source list

## Outputs

- approved design
- target paths
- source modification design
- data change design
- design basis policy reference

## Startup

- Confirm planning outputs exist.
- Confirm source modification policy and work plan are approved.
- Record `unknown` if required design inputs are missing.

## Planning

- Define design scope and handoff boundaries.
- Map the business activity to its supporting capability:
  - solution design drafting -> `CAP-DSN-001`
- Prepare management rows for design outputs and unresolved assumptions.

## Execution

- Perform solution design drafting by executing `CAP-DSN-001`.
- Record which planning policy and planning basis source entry each design artifact realizes.
- Produce implementation-ready design artifacts and preserve unresolved design assumptions explicitly.

## Monitoring and Control

- Check that all required design areas have a recorded result.
- Downgrade weakly supported design assumptions to `unknown`.
- Preserve unresolved design constraints for manufacturing handoff.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the approved design package, design basis policy reference, and unresolved design items.
- Escalate out-of-scope design questions when reassignment is required.

## Rules

- Do not redefine business scope.
- Do not start manufacturing changes in this skill.
- Do not produce test artifacts in this skill.
