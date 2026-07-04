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
- test tool policy
- approved design
- design-to-test input package from `design_flow`
- XDDP traceability matrix or rows from the approved design package
- planning basis source list
- available domain/environment test tool catalog metadata supplied by the
  runtime/MCP domain knowledge catalog

## Outputs

- test plan
- test plan basis policy reference
- selected test tool basis reference
- test design
- test design basis policy reference
- test-item requirement traceability reference
- integration regression test design
- integration regression test basis policy reference
- manufacturing test review result
- unresolved test tool gaps
- unresolved list

## Startup

- Confirm approved requirements, approved design, and test policy exist.
- Confirm the planning output includes a test tool policy.
- Confirm the approved design includes the design-to-test input package and XDDP
  traceability rows needed to derive test scope, test items, integration or
  regression coverage, and verification handoff.
- Confirm available domain/environment test tool catalog metadata is present
  when the test scope requires domain-specific, environment-specific, or
  organization-specific tooling.
- Select test tool knowledge by XID from the available domain knowledge catalog;
  do not infer local tool behavior from memory or local paths.
- Record `unknown` if required test evidence is missing.
- Record `unknown` if the needed test tool catalog entry, environment condition,
  supported test target, or tool verification method is missing.
- When the needed domain/environment test tool catalog does not exist, hand off
  to `test_tool_catalog_preparation` before freezing tool-dependent test plan
  rows.

## Planning

- Define test scope and handoff boundaries.
- Define test tool selection boundaries for each domain, target environment,
  test level, and verification target.
- Map the business activities to their supporting capabilities:
  - test plan drafting -> `CAP-DSN-004`
  - test item drafting -> `CAP-DSN-002`
  - integration and regression test design drafting -> `CAP-DSN-003`
  - manufacturing-side test-method review -> `CAP-MFG-003`
- Prepare management rows for test plans, test items, traceability, review findings, and unresolved assumptions.
- Use the design-to-test input package to seed test scope, test item candidates,
  integration/regression targets, DB verification points, and unknown or
  out-of-scope test questions.
- Use the test tool policy and selected domain/environment test tool knowledge
  to decide which existing tool can cover each test scope row.
- When no suitable tool exists, record the tool gap, creation/verification
  requirement, owner handoff, and whether affected test items remain `unknown`
  or `out_of_scope` until the tool is available.

## Execution

- Perform test plan drafting.
- Perform test item drafting with requirement traceability.
- Perform integration and regression test design drafting.
- Perform manufacturing-side test-method review.
- Record which requirement and design artifact each test item realizes.
- Record which XDDP traceability row, design item, and verification point each
  test item realizes.
- Record which selected test tool knowledge XID, environment condition, and
  tool capability each test item depends on.
- Include tool setup, input data, execution environment, result capture, and
  evidence retention method when they are required by the selected tool
  knowledge or test tool policy.

## Monitoring and Control

- Check that each required test item has requirement traceability.
- Check that each design-to-test input row is covered by a test item,
  integration/regression test design row, explicit `unknown`, or explicit
  `out_of_scope` reason.
- Check that each tool-dependent test item has a selected tool basis or an
  explicit unresolved tool gap.
- Check that selected tools match the target domain, environment, test level,
  required data setup, automation/manual split, and evidence-retention needs.
- Downgrade weakly supported test assumptions to `unknown`.
- Downgrade weakly supported tool assumptions to `unknown`.
- Preserve unsupported test methods explicitly for redesign or escalation.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Confirm the reviewed test package traces back to the approved design package's
  XDDP traceability rows and design-to-test input package.
- Confirm the reviewed test package records selected test tool knowledge XIDs,
  environment conditions, unresolved tool gaps, and tool-creation handoffs.
- Hand off the reviewed test package to manufacturing and quality verification work.
- Escalate out-of-scope test questions when reassignment is required.
- Escalate unresolved test tool gaps when test execution cannot proceed with the
  approved tool set.
- Hand missing catalog preparation to `test_tool_catalog_preparation` when the
  gap is about cataloging existing tools rather than designing new tests.

## Rules

- Do not redefine requirement intent.
- Do not redefine business scope.
- Manufacturing review confirms method suitability only.
- Do not invent domain-specific or environment-specific test tool behavior.
- Do not embed target-service test tool catalogs in this Skill; select them as
  runtime domain knowledge by XID.
