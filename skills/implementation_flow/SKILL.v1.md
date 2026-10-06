---
schema_version: 1
skill_id: implementation_flow
xid: D7B4E9A2C610
summary: Execute an approved and bounded software change and prepare it for QA review.
applies_when:
- user asks to implement changes based on an approved design or explicitly bounded instructions
exclusions:
- Discovering new design intent.
- Resolving unresolved business, security, release, dependency, or license decisions locally.
- Replacing QA review or closing a quality source finding from implementation context.
inputs:
- approved design or equivalent scope instruction, design basis policy reference, test plan, test design, test design basis policy reference, test-item requirement traceability reference, manufacturing test review result, target files, applicable coding rules, optional test viewpoints
outputs:
- code changes, unit test results, unit test execution basis reference, implementation basis design reference, referenced constraint-derivation output paths when used, quality-feedback response when applicable, uncertainty list, out-of-scope list
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
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: implementation_assumption_gap_handling
  query: implementation assumption gap classification and handling
  required_when: An implementation assumption gap appears while planning or coding.
  seed_xids:
  - 7A2F4C8D1501
- id: temporary_traceability_comment_rule
  query: temporary traceability comment applicability and cleanup
  required_when: Source comments are considered for human review traceability.
  seed_xids:
  - 22E4C7AC7063
- id: quality_feedback_return_rules
  query: quality feedback return and handoff rules
  required_when: The run handles a quality or source review feedback item.
  seed_xids:
  - 7A2F4C8D1901
- id: xddp_basics
  query: XDDP basics for implementation traceability
  required_when: Implementation or tests must be traced to XDDP design evidence.
  seed_xids:
  - 7A2F4C8D1701
- id: xddp_supporting_methods
  query: XDDP supporting methods for implementation evidence
  required_when: Supporting XDDP methods are needed to prepare implementation evidence.
  seed_xids:
  - 7A2F4C8D1711
control_refs: []
aliases:
- 0ACF69A599D3
- 1832ADA8D6D4
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

## Additional bound references retained at repository cutover

These references were explicitly bound by the prior repository Skill. Apply them to the relevant method work; resolve their XIDs on demand.

- [Constraint Derivation Framework](../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: implementation_flow

## Purpose

Execute the manufacturing sequence `CAP-MFG-001 -> CAP-MFG-002` and prepare output for QA review.

## Required Capability Definitions (XID)


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

## Required Knowledge (XID)

- [Implementation assumption gap handling](../../knowledge/organization/150_implementation_assumption_gap_handling.md#xid-7A2F4C8D1501)
- [Temporary traceability comment rule](../../knowledge/organization/151_temporary_traceability_comment_rule.md#xid-22E4C7AC7063)
- [Quality feedback return rules](../../knowledge/organization/190_quality_feedback_return_rules.md#xid-7A2F4C8D1901)
- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)

## Client-Delivered Runtime Use

When this Skill is obtained through XRefKit MCP, the client treats the
transferred `meta.md` and `SKILL.md` bodies as the procedure source.

- Resolve capability and knowledge links by XID through the client-visible XRef
  resolver, not by assuming a local XRefKit checkout.
- Use the MCP-provided Skill catalog and `get_skill` response to load this
  procedure before execution.
- Run `xrefkit skill run` in the client execution environment to create the runtime
  envelope before opening the procedure for operational use.
- Execute deterministic `xrefkit` commands and any implementation tools in the
  client environment; the MCP server distributes content and contracts only.
- Keep the run log, work items, artifacts, concerns, verification evidence, and
  handoff records on the client side unless a separate approved publication
  flow transfers them back.

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
- Confirm the client has loaded this Skill through the active XRefKit routing
  surface and can resolve required capability and knowledge XIDs on demand.
- If the run starts from quality feedback, confirm each finding has evidence,
  remediation direction, scope, and a tradeoff assessment basis.
- Record `unknown` if required evidence is missing.
- If the task still depends on unresolved structural behavior from DDL, UI, state transitions, integrations, batch rules, or auth rules, route through `constraint_derivation_index` before coding.

## Planning

- Define the implementation targets and test targets.
- Treat implementation as realization of an already-defined difference, not as a place to discover new design intent.
- For quality feedback returns, classify each finding as
  `implementation_local`, `tradeoff_or_scope_conflict`,
  `requires_design_or_requirement_decision`, or
  `requires_specialist_or_dependency_decision`.
- Check whether the incoming design package still leaves structural behavior implicit.
- If yes, stop implementation planning and route to the matching constraint-derivation Skills first.
- Map each business activity to its supporting capability:
  - implementation -> `CAP-MFG-001`
  - unit test execution -> `CAP-MFG-002`
- Define the step order: `CAP-MFG-001 -> CAP-MFG-002`.
- Prepare management rows for code changes, tests, and unresolved items.

## Execution

- Perform implementation by executing `CAP-MFG-001`.
- Perform unit test execution by executing `CAP-MFG-002`.
- When a quality feedback item is implementation-local, concrete,
  evidence-backed, in scope, and has no tradeoff with other active findings,
  implement the fix and record the linked finding id plus verification
  evidence.
- When a quality feedback item has a tradeoff, scope conflict, or requires a
  design, requirement, release, security, business, dependency, or license
  decision, do not decide locally; record and escalate it.
- Modify source code only against the traced target set and approved change-design basis.
- Treat confirmed constraint-derivation outputs as part of the coding basis when those outputs were needed to prevent guessed behavior.
- Record the derivation output path in the implementation basis design reference or equivalent handoff artifact when derivation was required.
- Prefer one coordinated pass over repeated local rework when the required change set is already known.
- Record which design artifact or design basis reference each implementation change realizes.
- Record which test design item each executed unit test realizes.
- Use temporary source comments for human traceability under the temporary
  traceability comment rule's applicability conditions: default ON when a
  human review stage exists outside this run, default OFF for single-run
  autonomous remediation whose traceability completes in external artifacts
  (record the omission decision in planning or judgment notes).
- Mark temporary traceability comments with the `TRACE-TEMP:` prefix and keep the lasting traceability in external evidence.
- When an implementation assumption gap appears, classify it as:
  - `clarification_needed`
  - `evidence_missing`
  - `scope_conflict`
  - `local_choice_allowed`
  - `basis_refuted` (implementation-time hard evidence contradicts the
    upstream basis; do not apply the refuted instruction)
- Record the gap using the implementation assumption gap handling rule.
- Record `unknown` and `out_of_scope` where needed.

## Monitoring and Control

- Check that every target file or change area has a recorded state.
- Check that every quality feedback item is either fixed with evidence or
  escalated with the reason named.
- Check that every implementation assumption gap has a recorded classification and handling result.
- Downgrade weakly supported completion claims to `unknown`.
- Downgrade completion claims to `unknown` when the implemented diff cannot be traced back to the approved change-design basis.
- Stop if coding starts to choose unresolved structural behavior locally instead of escalating back through design or constraint derivation.
- Preserve explicit reasons for `out_of_scope` items.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- When code review completion is declared for the target scope, remove any `TRACE-TEMP:` comments from source files in that scope before final completion.
- Hand off code, test results, unit test execution basis reference, and implementation basis design reference to QA review.
- When this run handled quality feedback, hand back the finding ids,
  disposition, fix evidence, verification evidence, and remaining validation
  handoff to the quality source.
- Do not mark the quality source's finding closed from the implementation
  context. The quality source must re-run or re-dispose the relevant check
  using the returned evidence.
- When a `basis_refuted` gap was recorded, register a correction handoff
  artifact targeting the originating skill run or artifact (for example the
  review findings document), so the refuted basis is annotated at its source
  instead of diverging silently; the refuting evidence and the non-trivial
  judgment must be linked from that handoff.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Never change design policy inside this skill.
- Never hide unresolved items.
- Never resolve an implementation assumption gap by guessing design or business intent.
- Never use pending runtime, integration, or manual tests as a reason to skip
  source-quality feedback that can be evaluated from source evidence.
- Never choose between conflicting quality findings locally; escalate the
  tradeoff.
- Fix implementation-local quality findings when there is no tradeoff and the
  fix remains inside approved scope.
- Every out-of-scope item must include a reason.
- Keep changes traceable to explicit scope.
- Keep executed unit tests traceable to explicit test design.
- Do not broaden the implementation diff beyond the traced target set without recording a new explicit reason.
- Do not leave `TRACE-TEMP:` comments in final code handed off as completed output.
- Treat a user declaration of code review completion plus a target scope such as `projects` as the cleanup trigger for `TRACE-TEMP:` comments in that scope.

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

- summary: execute manufacturing business activities through reusable scoped realization and unit-level verification capabilities

- use_when: user asks to implement changes based on an approved design or explicitly bounded instructions

- intent:
  - implement an approved and bounded software change
  - execute scoped code realization followed by unit-level verification
  - return implementation evidence and unresolved items to QA review

- applies_when:
  - the requested work has an approved design or equivalent bounded instruction or concrete quality-feedback item
  - target source and test areas are known or can be named before coding
  - implementation can proceed without locally inventing missing structural behavior

- target_artifacts:
  - source code changes
  - unit tests or unit-level verification evidence
  - implementation basis design reference
  - unit test execution basis reference
  - unresolved and uncertainty and out-of-scope and quality-feedback handoff records

- not_for:
  - discovering new design intent
  - resolving unresolved business or security or release or dependency or license decisions locally
  - deriving hidden structural behavior from DDL or UI or state transitions or integrations or batch rules or auth rules
  - replacing QA review or closing the quality source finding from the implementation context

- required_tools:
  - `xrefkit skill run`
  - `xrefkit skill workitem`
  - `xrefkit skill artifact`
  - `xrefkit skill concern`
  - `xrefkit skill verify`
  - `xrefkit skill close`
  - `xrefkit xref search`
  - `xrefkit xref show`

- input: approved design or equivalent scope instruction, design basis policy reference, test plan, test design, test design basis policy reference, test-item requirement traceability reference, manufacturing test review result, target files, applicable coding rules, optional test viewpoints

- output: code changes, unit test results, unit test execution basis reference, implementation basis design reference, referenced constraint-derivation output paths when used, quality-feedback response when applicable, uncertainty list, out-of-scope list

- constraints: do not change design policy; keep unresolved items explicit; implement only traced and approved differences by default; when coding would require guessing unresolved structural behavior from design artifacts, route through the constraint-derivation pack before implementation; handle concrete in-scope quality feedback when no tradeoff exists among active findings

- lifecycle:
  - startup: confirm approved scope, reviewed test package, target files, and coding rules exist; stop if the task still depends on unresolved structural behavior that should be derived before coding
  - planning: define implementation and test targets and management rows from design and reviewed test design; if structural behavior remains implicit, route back through constraint derivation before coding
  - execution: perform implementation and unit test execution through `CAP-MFG-001 -> CAP-MFG-002` against traced and approved differences only after the required derivation or design confirmation exists
  - monitoring_and_control: downgrade weak completion claims or untraced diffs to `unknown`; preserve out-of-scope reasons; stop if coding starts to choose missing design behavior locally
  - closure: finalize states and hand off results and implementation basis design reference to QA review

- tags: `implementation`, `manufacturing`, `engineering`

- knowledge_slots:
  - name=temporary_traceability_comment_rule; bind=22E4C7AC7063
  - name=quality_feedback_return_rules; bind=7A2F4C8D1901
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=constraint_derivation_framework; bind=81A6C4E2B190

- observation_refs:
  - `../../observations/2026-06-12_skill_run_implementation_flow.md`
  - `../../observations/2026-06-12_skill_run_implementation_flow_2.md`
  - `../../observations/2026-06-12_skill_run_implementation_flow_3.md`
  - `../../observations/2026-06-12_implementation_flow_improvement_proposal.md`
