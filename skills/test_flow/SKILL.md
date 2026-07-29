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
- test execution preparation plan for test data, environment setup, initial
  state, cleanup/reset, and evidence-capture readiness
- local-domain test execution helper script plan for simplifying repeatable test
  setup, execution, reset, and evidence capture
- local-domain test tool creation plan for scope that has no suitable existing
  tool
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
- Define pre-execution preparation for every executable test scope row. Include
  test data, environment setup, initial state, dependency/service availability,
  access/credential needs, cleanup/reset method, and evidence-capture readiness.
- Treat preparation items as testware: test data, environment items, helper
  scripts, setup/clear-up procedures, files, databases, stubs, drivers,
  simulators, service virtualizations, and evidence capture must be planned when
  they are needed for execution.
- Define execution configuration explicitly when behavior or coverage differs by
  browser, OS, runtime, database, deployment version, tenant, feature flag,
  external service condition, or other environment variable.
- Define local-domain helper scripts when repeatable setup, test data creation,
  tool invocation, reset/cleanup, or evidence capture would otherwise require
  fragile manual steps. The plan must record script purpose, target environment,
  input parameters, generated or mutated data, selected tool invocation,
  cleanup/reset behavior, evidence output, verification method, owner, and local
  placement.
- When no suitable tool exists, include a test tool creation plan in the test
  plan. The plan must record the uncovered test scope, required tool purpose,
  target environment, required input data, expected evidence output,
  verification method for the new tool, creation owner, dependency/handoff,
  local-domain placement/ownership, availability condition, and whether affected
  test items remain `unknown` or `out_of_scope` until the tool is available.
- Treat the newly created test tool as a local-domain artifact for the target
  system, project, tenant, or organization. Do not assume it belongs in shared
  XRefKit knowledge or reusable base tooling unless a separate adoption or
  publication decision explicitly promotes it.

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
- Write the test execution preparation plan as part of the test plan and trace
  each preparation row to the affected XDDP row, design item, verification
  point, test item, selected tool, and target environment.
- Include data availability and acquisition method for automated tests. If
  required data cannot be acquired on demand, record the blocked tests, impact,
  and data-preparation handoff.
- Write the helper script plan as part of the test plan and trace each script to
  the preparation rows, test items, selected tools, XDDP rows, and evidence it
  simplifies.
- For rows without a suitable existing tool, write the test tool creation plan
  as a first-class part of the test plan and trace it to the affected XDDP row,
  design item, verification point, and test items.
- Record the planned tool's local-domain boundary, storage/publication target,
  and whether it will later be cataloged as local domain knowledge for MCP/XID
  access.

## Monitoring and Control

- Check that each required test item has requirement traceability.
- Check that each design-to-test input row is covered by a test item,
  integration/regression test design row, explicit `unknown`, or explicit
  `out_of_scope` reason.
- Check that each tool-dependent test item has a selected tool basis or an
  explicit unresolved tool gap.
- Check that each unresolved tool gap has a corresponding test tool creation
  plan row unless the gap is explicitly `out_of_scope`.
- Check that selected tools match the target domain, environment, test level,
  required data setup, automation/manual split, and evidence-retention needs.
- Check that each test tool creation plan row includes creation, verification,
  owner, local-domain boundary, handoff, and availability conditions.
- Check that each executable test item has preparation coverage for test data,
  environment setup, initial state, cleanup/reset, and evidence capture, or an
  explicit `unknown`/`out_of_scope` reason.
- Check that configuration-dependent tests are represented with explicit
  configuration rows rather than implicit environment assumptions.
- Check that automated tests are not blocked by missing on-demand test data, or
  record the data gap and handoff explicitly.
- Check that repeated or fragile test execution steps have a helper script plan,
  or an explicit reason why scripting is not needed.
- Check that each helper script plan row includes inputs, side effects,
  idempotency or reset behavior, evidence outputs, verification method, owner,
  and local-domain placement.
- Downgrade weakly supported test assumptions to `unknown`.
- Downgrade weakly supported preparation assumptions to `unknown`.
- Downgrade weakly supported tool assumptions to `unknown`.
- Preserve unsupported test methods explicitly for redesign or escalation.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Confirm the reviewed test package traces back to the approved design package's
  XDDP traceability rows and design-to-test input package.
- Confirm the reviewed test package records selected test tool knowledge XIDs,
  environment conditions, unresolved tool gaps, and tool-creation handoffs.
- Confirm the reviewed test package includes test execution preparation rows
  before handoff to test execution or quality verification.
- Confirm the reviewed test package includes local-domain helper script rows for
  repeatable setup, execution, cleanup/reset, or evidence capture where they are
  needed.
- Confirm the reviewed test package includes a test tool creation plan for every
  in-scope test need that lacks a suitable existing tool.
- Confirm newly planned test tools are marked as local-domain artifacts unless a
  separate publication/adoption decision is recorded.
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
- Do not hand off executable test items without explicit pre-execution
  preparation or an unresolved-state reason.
- Do not rely on manual repeated test setup or execution when a local-domain
  helper script is needed to make the run reproducible.
- Do not embed target-service test tool catalogs in this Skill; select them as
  runtime domain knowledge by XID.
- Do not treat test tools created for a target as shared XRefKit assets by
  default; they are local-domain artifacts until explicitly adopted or
  published.

## Reporting Contract (共通報告)



- reporting_profile: phase_summary

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
