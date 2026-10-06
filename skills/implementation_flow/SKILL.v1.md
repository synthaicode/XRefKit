---
schema_version: 1
skill_id: implementation_flow
xid: D7B4E9A2C610
aliases: [0ACF69A599D3, 1832ADA8D6D4]
summary: Execute an approved and bounded software change and prepare it for QA review.
applies_when:
  - The requested work has an approved design or equivalent bounded instruction.
  - Target source and test areas are known or can be named before coding.
  - Implementation can proceed without inventing missing structural behavior.
exclusions:
  - Discovering new design intent.
  - Resolving unresolved business, security, release, dependency, or license decisions locally.
  - Replacing QA review or closing a quality source finding from implementation context.
inputs:
  - Approved design or equivalent scoped instruction.
  - Design basis policy reference and reviewed test plan or test design.
  - Test design basis policy and test-item requirement traceability reference.
  - Manufacturing test review result, target paths, and coding rules.
  - Optional quality-feedback items and test viewpoints.
outputs:
  - Implemented code and unit test results.
  - Unit test execution basis and implementation basis design references.
  - Unresolved, uncertainty, and out-of-scope lists.
  - Quality-feedback response when applicable.
criteria:
  - id: bounded_scope
    statement: Every implementation change is traced to an approved design difference or an in-scope concrete quality finding.
    verification: Review the target and change rows against the approved design basis and finding disposition.
  - id: unit_verification
    statement: Unit-level verification is executed and its evidence is returned with the implementation handoff.
    verification: Inspect recorded test results and their links to test design items.
  - id: unresolved_handling
    statement: Missing structural behavior, uncertainty, and out-of-scope items remain explicit and are handed off when required.
    verification: Review planning, monitoring, and closure records for named unknowns and escalation reasons.
knowledge_needs:
  - id: implementation_assumption_gap_handling
    query: implementation assumption gap classification and handling
    required_when: An implementation assumption gap appears while planning or coding.
    seed_xids: [7A2F4C8D1501]
  - id: temporary_traceability_comment_rule
    query: temporary traceability comment applicability and cleanup
    required_when: Source comments are considered for human review traceability.
    seed_xids: [22E4C7AC7063]
  - id: quality_feedback_return_rules
    query: quality feedback return and handoff rules
    required_when: The run handles a quality or source review feedback item.
    seed_xids: [7A2F4C8D1901]
  - id: xddp_basics
    query: XDDP basics for implementation traceability
    required_when: Implementation or tests must be traced to XDDP design evidence.
    seed_xids: [7A2F4C8D1701]
  - id: xddp_supporting_methods
    query: XDDP supporting methods for implementation evidence
    required_when: Supporting XDDP methods are needed to prepare implementation evidence.
    seed_xids: [7A2F4C8D1711]
control_refs: []
---

<!-- xid: D7B4E9A2C610 -->
<a id="xid-D7B4E9A2C610"></a>

# Skill: implementation_flow

## Purpose

Execute the manufacturing sequence `CAP-MFG-001 -> CAP-MFG-002` and prepare output for QA review.

## Inputs

- approved design or equivalent scoped instruction
- quality/source review feedback items when this run is a feedback return
- design basis policy reference
- test plan
- test design
- test design basis policy reference
- test-item requirement traceability reference
- manufacturing test review result
- target paths
- coding and naming rules
- optional test viewpoints

## Outputs

- implemented code
- unit test results
- unit test execution basis reference
- unresolved list
- uncertainty list
- out-of-scope list
- implementation basis design reference
- quality-feedback response when applicable

## Startup

- Confirm approved scope exists.
- Confirm target files are identified.
- Confirm coding rules are available.
- If the run starts from quality feedback, confirm each finding has evidence, remediation direction, scope, and a tradeoff assessment basis.
- Record `unknown` if required evidence is missing.
- If the task still depends on unresolved structural behavior from DDL, UI, state transitions, integrations, batch rules, or auth rules, route through `constraint_derivation_index` before coding.

## Planning

- Define the implementation targets and test targets.
- Treat implementation as realization of an already-defined difference, not as a place to discover new design intent.
- For quality feedback returns, classify each finding as `implementation_local`, `tradeoff_or_scope_conflict`, `requires_design_or_requirement_decision`, or `requires_specialist_or_dependency_decision`.
- Check whether the incoming design package still leaves structural behavior implicit. If yes, stop implementation planning and route through constraint derivation before coding.
- Prepare management rows for code changes, tests, and unresolved items.

## Execution

- Perform implementation and unit test execution against traced and approved differences only after required derivation or design confirmation exists.
- When a quality feedback item is implementation-local, concrete, evidence-backed, in scope, and has no tradeoff with other active findings, implement the fix and record the linked finding id plus verification evidence.
- When a quality feedback item has a tradeoff, scope conflict, or requires a design, requirement, release, security, business, dependency, or license decision, do not decide locally; record and escalate it.
- Modify source code only against the traced target set and approved change-design basis.
- Record which design artifact each implementation change realizes and which test design item each executed unit test realizes.
- Mark temporary traceability comments with the `TRACE-TEMP:` prefix when the applicable rule requires them, and keep lasting traceability in external evidence.
- Classify implementation assumption gaps as `clarification_needed`, `evidence_missing`, `scope_conflict`, `local_choice_allowed`, or `basis_refuted`; record `unknown` and `out_of_scope` where needed.

## Monitoring and Control

- Check that every target file or change area has a recorded state.
- Check that every quality feedback item is fixed with evidence or escalated with the reason named.
- Check that every implementation assumption gap has a recorded classification and handling result.
- Downgrade weakly supported completion claims or untraced diffs to `unknown`.
- Stop if coding starts to choose unresolved structural behavior locally instead of escalating back through design or constraint derivation.
- Preserve explicit reasons for `out_of_scope` items.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- When code review completion is declared, remove `TRACE-TEMP:` comments from the completed scope.
- Hand off code, test results, and implementation basis design reference to QA review.
- When this run handled quality feedback, return finding ids, disposition, fix evidence, verification evidence, and remaining validation handoff to the quality source.
- Do not mark the quality source's finding closed from the implementation context.
- When a `basis_refuted` gap was recorded, register a correction handoff artifact targeting the originating run or artifact.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Never change design policy inside this skill.
- Never hide unresolved items.
- Never resolve an implementation assumption gap by guessing design or business intent.
- Never choose between conflicting quality findings locally; escalate the tradeoff.
- Keep changes traceable to explicit scope and keep executed unit tests traceable to explicit test design.
- Do not broaden the implementation diff beyond the traced target set without recording a new explicit reason.
- Do not leave `TRACE-TEMP:` comments in final code handed off as completed output.
