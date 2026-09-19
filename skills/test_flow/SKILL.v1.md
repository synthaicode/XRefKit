---
schema_version: 1
skill_id: test_flow
xid: F9D2B6E5C130
aliases: [62F9F44D7711, 2D7B0A661990]
summary: Produce a reviewed test package from approved requirements, design evidence, and test-tool knowledge.
applies_when:
  - The user needs a reviewed test package from planning outputs, requirements, and approved design evidence.
  - Test scope can be derived from design-to-test inputs and traceability rows.
  - Required test-tool facts are available or can remain explicit as unknown.
exclusions:
  - Redefining requirement, business, or design intent.
  - Inventing domain-specific or environment-specific test-tool behavior.
  - Treating target-specific helper tools as shared assets without adoption.
inputs:
  - Approved requirements, work plan, test policy, and test-tool policy.
  - Approved design and design-to-test input package.
  - XDDP traceability rows and planning basis source list.
  - Available domain/environment test-tool catalog metadata when required.
outputs:
  - Test plan, test design, and requirement/design traceability reference.
  - Test execution preparation and local-domain helper-script plans.
  - Integration/regression test design and manufacturing test review result.
  - Selected test-tool basis and unresolved tool gaps.
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
knowledge_needs:
  - id: test_design_criteria
    query: test design criteria
    required_when: Test scope and test items are being drafted or reviewed.
    seed_xids: [8C4D2A7E5102]
control_refs: []
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
