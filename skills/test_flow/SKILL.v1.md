---
schema_version: 1
skill_id: test_flow
xid: F9D2B6E5C130
summary: Produce a reviewed test package from approved requirements, design evidence, and test-tool knowledge.
applies_when:
- user needs a reviewed test package from planning outputs, requirements, and design evidence
exclusions:
- Redefining requirement, business, or design intent.
- Inventing domain-specific or environment-specific test-tool behavior.
- Treating target-specific helper tools as shared assets without adoption.
inputs:
- approved requirements, work plan, test policy, test tool policy, approved design, design-to-test input package, XDDP traceability matrix or rows from the approved design package, planning basis source list, selected domain/environment test tool knowledge XIDs when available
outputs:
- test plan with selected test tool basis, test execution preparation plan, local-domain test execution helper script plan, test tool creation plan when no suitable tool exists, test design, requirement and design traceability reference, integration regression test design, manufacturing test review result, unresolved tool gaps
criteria:
- id: requirement_traceability
  statement: Every required test item traces to approved requirements and design-to-test evidence.
  verification: Review test-item rows against requirements, XDDP rows, design items, and verification points.
- id: execution_preparation
  statement: Executable test scope has preparation coverage for data, environment, initial state, cleanup/reset, and evidence capture.
  verification: Inspect preparation rows or explicit unknown/out-of-scope reasons for each executable item.
- id: tool_boundary
  statement: Selected tools and tool gaps are supported by catalog knowledge or explicit creation and handoff plans.
  verification: Review tool basis, unresolved gaps, and local-domain ownership conditions.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: test_design_criteria
  query: test design criteria
  required_when: Test scope and test items are being drafted or reviewed.
  seed_xids:
  - 8C4D2A7E5102
control_refs: []
aliases:
- 62F9F44D7711
- 2D7B0A661990
---

<!-- xid: F9D2B6E5C130 -->
<a id="xid-F9D2B6E5C130"></a>

# Skill: test_flow

## Purpose

Execute test planning, test-item structuring, integration/regression test design, and manufacturing-side test-method review, then prepare a reviewed test package.

## Inputs

- approved requirements
- work plan
- test policy and test tool policy
- approved design and design-to-test input package from `design_flow`
- XDDP traceability matrix or rows from the approved design package
- planning basis source list
- available domain/environment test tool catalog metadata supplied by the runtime catalog

## Outputs

- test plan and test plan basis policy reference
- selected test tool basis reference
- test execution preparation plan
- local-domain test execution helper script plan
- local-domain test tool creation plan where no suitable tool exists
- test design and test design basis policy reference
- test-item requirement traceability reference
- integration regression test design and basis reference
- manufacturing test review result
- unresolved test tool gaps and unresolved list

## Startup

- Confirm approved requirements, approved design, and test policy exist.
- Confirm the planning output includes a test tool policy.
- Confirm the approved design includes the design-to-test input package and XDDP traceability rows needed to derive test scope, test items, integration or regression coverage, and verification handoff.
- Confirm available domain/environment test tool catalog metadata is present when the test scope requires domain-specific, environment-specific, or organization-specific tooling.
- Select test tool knowledge by XID from the available domain catalog; do not infer local tool behavior from memory or local paths.
- Record `unknown` if required test evidence, a needed catalog entry, environment condition, supported target, or tool verification method is missing.
- When the needed domain/environment test tool catalog does not exist, hand off to `test_tool_catalog_preparation` before freezing tool-dependent test-plan rows.

## Planning

- Define test scope and handoff boundaries.
- Define test-tool selection boundaries for each domain, target environment, test level, and verification target.
- Prepare management rows for test plans, test items, traceability, review findings, and unresolved assumptions.
- Use the design-to-test input package to seed test scope, test-item candidates, integration/regression targets, DB verification points, and unknown or out-of-scope questions.
- Use the test-tool policy and selected domain/environment knowledge to choose tools for each scope row.
- Define pre-execution preparation for every executable row, including test data, environment setup, initial state, dependencies, access, cleanup/reset, and evidence readiness.
- Plan helper scripts for fragile or repeated setup, execution, reset/cleanup, or evidence capture.
- When no suitable tool exists, include a creation plan with scope, purpose, environment, data, evidence, verification, owner, handoff, local placement, availability condition, and interim unknown/out-of-scope state.
- Treat newly created tools as local-domain artifacts unless a separate adoption or publication decision promotes them.

## Execution

- Perform test plan drafting, test-item drafting with requirement traceability, integration/regression test design drafting, and manufacturing-side test-method review.
- Record which requirement, design artifact, XDDP row, verification point, selected tool knowledge XID, environment condition, and tool capability each test item realizes.
- Include tool setup, input data, execution environment, result capture, and evidence retention where required by the selected tool knowledge or test policy.
- Trace every preparation row and helper script to affected design rows, test items, selected tools, target environment, and evidence.
- Record data gaps, unsupported tools, local-domain boundaries, storage/publication targets, and handoffs explicitly.

## Monitoring and Control

- Check that every required test item has requirement traceability.
- Check that each design-to-test row is covered by a test item, integration/regression row, explicit `unknown`, or explicit `out_of_scope` reason.
- Check that each tool-dependent item has a selected tool basis or unresolved tool gap, and each gap has a creation plan unless out of scope.
- Check that executable items have preparation coverage or an explicit unresolved reason.
- Check that configuration-dependent tests have explicit configuration rows.
- Check that repeated or fragile execution has a helper-script plan or a recorded reason why scripting is not needed.
- Downgrade weakly supported test, preparation, or tool assumptions to `unknown`.
- Preserve unsupported test methods for redesign or escalation.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Confirm the reviewed package traces to approved design XDDP rows, design-to-test inputs, selected tool knowledge, environment conditions, unresolved gaps, and preparation/helper-script rows.
- Confirm every in-scope test need without a suitable tool has a tool-creation plan.
- Confirm newly planned tools are local-domain artifacts unless separate publication/adoption is recorded.
- Hand off the reviewed package to manufacturing and quality verification.
- Escalate out-of-scope test questions and unresolved tool gaps when execution cannot proceed.
- Hand catalog preparation to `test_tool_catalog_preparation` when the gap is cataloging existing tools.

## Rules

- Do not redefine requirement intent, business scope, or design intent.
- Manufacturing review confirms method suitability only.
- Do not invent domain-specific or environment-specific test-tool behavior.
- Do not hand off executable items without preparation or an explicit unresolved-state reason.
- Do not embed target-service test-tool catalogs in this Skill; select them as runtime domain knowledge by XID.
- Do not treat target-specific tools or helper scripts as shared XRefKit assets by default.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

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

### Original Skill-specific declarations

- summary: execute test-planning, test-item structuring, integration/regression test design, and manufacturing-side test-method review

- use_when: user needs a reviewed test package from planning outputs, requirements, and design evidence

- input: approved requirements, work plan, test policy, test tool policy, approved design, design-to-test input package, XDDP traceability matrix or rows from the approved design package, planning basis source list, selected domain/environment test tool knowledge XIDs when available

- output: test plan with selected test tool basis, test execution preparation plan, local-domain test execution helper script plan, test tool creation plan when no suitable tool exists, test design, requirement and design traceability reference, integration regression test design, manufacturing test review result, unresolved tool gaps

- constraints: do not redefine requirement intent, business scope, design intent, final release judgment, or domain/environment test tool facts; derive test scope from the approved design's design-to-test input package and XDDP traceability rows rather than broad design prose; select test tools from planning test tool policy and available domain/environment test tool knowledge; include pre-execution preparation such as test data, environment setup, initial state, cleanup/reset, and evidence-capture readiness before test execution; include local-domain helper scripts that simplify repeatable test execution when manual setup or tool invocation would be error-prone; when no suitable test tool exists, include a test tool creation plan in the test plan instead of leaving the gap as a bare unknown; treat newly created test tools and helper scripts as local-domain artifacts unless an explicit publication/adoption decision promotes them; record unsupported tool assumptions as unknown

- lifecycle:
  - startup: confirm requirements, planning outputs, test policy, test tool policy, approved design, design-to-test input package, XDDP traceability rows, and available domain/environment test tool catalog metadata exist when tool selection is needed
  - planning: define test scope, tool-selection scope, test execution preparation rows, local-domain helper script rows, local-domain test tool creation plan rows for uncovered scope, and management rows from the design-to-test input package and selected domain/environment test tool knowledge
  - execution: perform `CAP-DSN-004 -> CAP-DSN-002 -> CAP-DSN-003 -> CAP-MFG-003` and record requirement/design/tool traceability for each test item
  - monitoring_and_control: downgrade unsupported test assumptions, tool assumptions, or uncovered design-to-test rows to `unknown`
  - closure: finalize states and hand off the reviewed test package with requirement/design/tool/preparation/helper-script traceability and test tool creation plan rows for uncovered tool needs

- tags: `test`, `design`, `manufacturing`, `traceability`

- knowledge_slots:
  - name=test_design_criteria; bind=8C4D2A7E5102

- knowledge_inputs:
  - name=domain_environment_test_tool_catalog; required=false; accepts=test-tool-catalog,environment-test-tool-policy,domain-test-automation-map,local-test-runner-guide; purpose=select-test-tools-for-plan-and-test-design
