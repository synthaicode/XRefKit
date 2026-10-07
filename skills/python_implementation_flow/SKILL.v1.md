---
schema_version: 1
skill_id: python_implementation_flow
xid: E8C1A7D4B920
summary: Execute an approved and bounded Python change and prepare it for Python or QA review.
applies_when:
- user asks to implement Python changes based on an approved design, explicitly bounded instructions, or concrete quality-feedback items
exclusions:
- Discovering new design intent.
- Resolving design, requirement, release, security, business, dependency, or license decisions locally.
- Closing a quality source finding from the implementation context.
inputs:
- approved design or equivalent scope instruction, design basis policy reference, test plan or test intent, test design basis reference when available, target files, applicable Python coding rules, configured test and static baseline commands, optional quality-feedback items
outputs:
- Python code changes, unit test or unit-level verification results, static baseline evidence when configured, implementation basis design reference, quality-feedback response when applicable, uncertainty list, out-of-scope list, and handoff items for Python review or QA review
criteria:
- id: bounded_python_change
  statement: Python changes remain within the approved traced target set and preserve project boundaries.
  verification: Review the diff and implementation records against the approved basis.
- id: configured_validation
  statement: Applicable configured tests and static validation commands are run and recorded.
  verification: Inspect validation evidence and its relation to the changed code or test design.
- id: explicit_handoff
  statement: Unknowns, out-of-scope items, and quality feedback are returned to the appropriate review owner.
  verification: Review closure and handoff records for disposition and evidence.
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
- id: python_review_spec
  query: Python review criteria and evidence requirements
  required_when: The completed Python implementation is handed to Python review.
  seed_xids:
  - A9B7C6D5E4F1
control_refs: []
aliases:
- C5D6E7F8A9B1
- C5D6E7F8A9B0
---

<!-- xid: E8C1A7D4B920 -->
<a id="xid-E8C1A7D4B920"></a>

# Skill: python_implementation_flow

## Purpose

Execute Python manufacturing work and prepare the result for Python review or QA review. This Skill realizes an already-approved, bounded difference; it is not a place to invent missing design behavior.

## Inputs

- approved design or equivalent scoped instruction
- target Python files, packages, tests, or service boundaries
- applicable coding and naming rules
- configured validation commands such as test, type-check, lint, format-check, or dependency checks
- optional quality/source review feedback items

## Outputs

- Python code changes
- unit test or unit-level verification results
- configured static baseline evidence when applicable
- implementation basis design reference
- quality-feedback response when applicable
- uncertainty list, out-of-scope list, and handoff items

## Startup

- Confirm approved scope exists.
- Confirm target files and validation commands are identified or explicitly unavailable.
- Confirm coding rules are available.
- If the run starts from quality feedback, confirm each finding has evidence, remediation direction, scope, and tradeoff assessment basis.
- Record `unknown` if required evidence is missing.
- If the task depends on unresolved structural behavior from DDL, UI, state transitions, integrations, batch rules, auth rules, or external contracts, route through `constraint_derivation_index` before coding.

## Planning

- Define implementation targets and test targets.
- Treat implementation as realization of an already-approved difference.
- For quality feedback returns, classify each finding as `implementation_local`, `tradeoff_or_scope_conflict`, `requires_design_or_requirement_decision`, or `requires_specialist_or_dependency_decision`.
- Check whether the incoming design package leaves structural behavior implicit. If yes, stop implementation planning and route to matching constraint-derivation Skills first.
- Define validation commands and expected evidence: unit or focused tests, type checker, linter or formatter, and dependency checks when configured and relevant.
- Prepare management rows for code changes, tests, static baseline, unresolved items, and handoff items.

## Execution Role

- The executor modifies code, runs validation, and records artifacts.
- The executor never advances the check phase and never closes the run.

## Execution

- Modify source code only against the traced target set and approved change-design basis.
- Preserve project structure, package boundaries, dependency direction, public interfaces, and test style unless the approved scope says otherwise.
- For implementation-local quality feedback, implement the fix when it is evidence-backed, in scope, concrete, and has no tradeoff with other active findings.
- Escalate quality feedback that has tradeoffs, scope conflicts, or requires a design, requirement, release, security, business, dependency, or license decision.
- Record which design artifact or quality-feedback item each change and validation action realizes.
- Use temporary `TRACE-TEMP:` comments only when the applicable rule requires them; keep durable traceability in external evidence.
- Classify implementation assumption gaps as `clarification_needed`, `evidence_missing`, `scope_conflict`, `local_choice_allowed`, or `basis_refuted`. Record `unknown` and `out_of_scope` where needed.

## Monitoring and Control

- Check that every target file or change area has a recorded state.
- Check that every quality feedback item is fixed with evidence or escalated with the reason named.
- Check that every implementation assumption gap has a classification and handling result.
- Downgrade completion claims to `unknown` when the implementation cannot be traced to the approved basis.
- Stop if coding starts to choose unresolved structural behavior locally.
- Preserve explicit reasons for out-of-scope items.

## Check Role

- The check role is the protocol-owned deterministic run-record check.
- Record code changes as output artifacts and validation commands/results as evidence artifacts.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Remove `TRACE-TEMP:` comments from completed review scope when code-review completion is declared.
- Hand off code, validation evidence, and implementation basis to `python_review` or `qa_gate_review`.
- When this run handled quality feedback, return finding ids, disposition, fix evidence, verification evidence, and remaining validation handoff to the quality source.
- Do not mark the quality source's finding closed from the implementation context.
- When a `basis_refuted` gap was recorded, register a correction handoff artifact targeting the originating run or artifact.

## Rules

- Never change design policy inside this Skill.
- Never hide unresolved items.
- Never resolve an implementation assumption gap by guessing design or business intent.
- Never use pending runtime, integration, or manual tests as a reason to skip source-quality feedback that can be evaluated from source evidence.
- Never choose between conflicting quality findings locally; escalate the tradeoff.
- Keep changes traceable to explicit scope and keep executed tests traceable to explicit test design or quality-feedback items.
- Do not broaden the implementation diff beyond the traced target set without recording a new explicit reason.

## Additional bound references retained at repository cutover

These references were explicitly bound by the prior repository Skill. Apply them to the relevant method work; resolve their XIDs on demand.

- [Constraint Derivation Framework](../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: python_implementation_flow

## Purpose

Execute Python manufacturing work and prepare the result for Python review or
QA review. This Skill realizes an already-approved, bounded difference; it is
not a place to invent missing design behavior.

## Required Knowledge (XID)

- [Implementation assumption gap handling](../../knowledge/organization/150_implementation_assumption_gap_handling.md#xid-7A2F4C8D1501)
- [Temporary traceability comment rule](../../knowledge/organization/151_temporary_traceability_comment_rule.md#xid-22E4C7AC7063)
- [Quality feedback return rules](../../knowledge/organization/190_quality_feedback_return_rules.md#xid-7A2F4C8D1901)
- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)
- [Python review spec](../../knowledge/python/100_python_review_spec.md#xid-A9B7C6D5E4F1)

## Inputs

- approved design or equivalent scoped instruction
- target Python files, packages, tests, or service boundaries
- applicable coding and naming rules
- configured validation commands such as test, type-check, lint, format-check,
  or dependency checks
- optional quality/source review feedback items

## Outputs

- Python code changes
- unit test or unit-level verification results
- configured static baseline evidence when applicable
- implementation basis design reference
- quality-feedback response when applicable
- uncertainty list, out-of-scope list, and handoff items

## Startup

- Confirm approved scope exists.
- Confirm target files and validation commands are identified or explicitly
  unavailable.
- Confirm coding rules are available.
- If the run starts from quality feedback, confirm each finding has evidence,
  remediation direction, scope, and tradeoff assessment basis.
- Record `unknown` if required evidence is missing.
- If the task depends on unresolved structural behavior from DDL, UI, state
  transitions, integrations, batch rules, auth rules, or external contracts,
  route through `constraint_derivation_index` before coding.

## Planning

- Define implementation targets and test targets.
- Treat implementation as realization of an already-defined difference.
- For quality feedback returns, classify each finding as:
  - `implementation_local`
  - `tradeoff_or_scope_conflict`
  - `requires_design_or_requirement_decision`
  - `requires_specialist_or_dependency_decision`
- Check whether the incoming design package leaves structural behavior implicit.
- If yes, stop implementation planning and route to matching
  constraint-derivation Skills first.
- Define validation commands and expected evidence:
  - unit or focused tests
  - type checker when configured
  - linter or formatter check when configured
  - dependency or package checks when configured and relevant
- Prepare management rows for code changes, tests, static baseline, unresolved
  items, and handoff items.

## Execution Role

- The executor modifies code, runs validation, and records artifacts.
- The executor never advances the check phase and never closes the run.

## Execution

- Modify source code only against the traced target set and approved
  change-design basis.
- Prefer one coordinated pass over repeated local rework when the required
  change set is already known.
- Preserve the current Python project structure, package boundaries, dependency
  direction, public interfaces, and test style unless the approved scope says
  otherwise.
- For implementation-local quality feedback, implement the fix when it is
  evidence-backed, in scope, concrete, and has no tradeoff with other active
  findings.
- Escalate quality feedback that has tradeoffs, scope conflicts, or requires a
  design, requirement, release, security, business, dependency, or license
  decision.
- Record which design artifact or design basis reference each implementation
  change realizes.
- Record which test design item or quality-feedback item each executed test
  verifies.
- Use temporary `TRACE-TEMP:` comments only under the temporary traceability
  rule's applicability conditions; keep durable traceability in external
  evidence.
- When an implementation assumption gap appears, classify it as
  `clarification_needed`, `evidence_missing`, `scope_conflict`,
  `local_choice_allowed`, or `basis_refuted`.
- Record `unknown` and `out_of_scope` where needed.

## Monitoring and Control

- Check that every target file or change area has a recorded state.
- Check that every quality feedback item is fixed with evidence or escalated
  with the reason named.
- Check that every implementation assumption gap has a classification and
  handling result.
- Downgrade completion claims to `unknown` when the implemented diff cannot be
  traced to the approved basis.
- Stop if coding starts to choose unresolved structural behavior locally.
- Preserve explicit reasons for out-of-scope items.

## Check Role

- The check role is the protocol-owned deterministic run-record check.
- Record code changes as `output` artifacts and validation commands/results as
  `evidence` artifacts.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Remove any `TRACE-TEMP:` comments from source files in the completed review
  scope when code-review completion is declared.
- Hand off code, validation evidence, and implementation basis to
  `python_review` or `qa_gate_review`.
- When this run handled quality feedback, hand back finding ids, disposition,
  fix evidence, verification evidence, and remaining validation handoff to the
  quality source.
- Do not mark the quality source's finding closed from the implementation
  context.
- When a `basis_refuted` gap was recorded, register a correction handoff
  artifact targeting the originating run or artifact.

## Rules

- Never change design policy inside this Skill.
- Never hide unresolved items.
- Never resolve an implementation assumption gap by guessing design or business
  intent.
- Never use pending runtime, integration, or manual tests as a reason to skip
  source-quality feedback that can be evaluated from source evidence.
- Never choose between conflicting quality findings locally; escalate the
  tradeoff.
- Keep changes traceable to explicit scope.
- Keep executed tests traceable to explicit test design or quality-feedback
  item.
- Do not broaden the implementation diff beyond the traced target set without
  recording a new explicit reason.

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

- summary: execute Python manufacturing activities through scoped realization and unit-level verification

- use_when: user asks to implement Python changes based on an approved design, explicitly bounded instructions, or concrete quality-feedback items

- input: approved design or equivalent scope instruction, design basis policy reference, test plan or test intent, test design basis reference when available, target files, applicable Python coding rules, configured test and static baseline commands, optional quality-feedback items

- output: Python code changes, unit test or unit-level verification results, static baseline evidence when configured, implementation basis design reference, quality-feedback response when applicable, uncertainty list, out-of-scope list, and handoff items for Python review or QA review

- constraints: do not change design policy; keep unresolved behavior explicit; implement only traced and approved differences by default; when coding would require guessing unresolved structural behavior from design artifacts, route through the constraint-derivation pack before implementation; handle concrete in-scope quality feedback when no tradeoff exists among active findings; keep Python-specific implementation evidence tied to configured tests and static baseline commands where available

- lifecycle:
  - startup: confirm approved scope, reviewed test basis or test intent, target files, Python coding rules, and configured validation commands exist; stop if the task still depends on unresolved structural behavior that should be derived before coding
  - planning: define implementation, test, and static-baseline targets from design and reviewed test evidence; if structural behavior remains implicit, route back through constraint derivation before coding
  - execution: perform Python implementation and unit-level verification against traced and approved differences only after required derivation or design confirmation exists
  - monitoring_and_control: downgrade weak completion claims or untraced diffs to `unknown`; preserve out-of-scope reasons; stop if coding starts to choose missing design behavior locally
  - closure: finalize states and hand off code changes, validation evidence, and implementation basis to Python review or QA review

- tags: `python`, `implementation`, `manufacturing`, `engineering`

- knowledge_slots:
  - name=implementation_assumption_gap_handling; bind=7A2F4C8D1501
  - name=temporary_traceability_comment_rule; bind=22E4C7AC7063
  - name=quality_feedback_return_rules; bind=7A2F4C8D1901
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=python_review_spec; bind=A9B7C6D5E4F1

- observation_refs:
  - `../../observations/2026-07-07_session_python_skill_authoring.md`
