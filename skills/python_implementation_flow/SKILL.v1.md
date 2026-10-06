---
schema_version: 1
skill_id: python_implementation_flow
xid: E8C1A7D4B920
aliases: [C5D6E7F8A9B1, C5D6E7F8A9B0]
summary: Execute an approved and bounded Python change and prepare it for Python or QA review.
applies_when:
  - The requested Python work has an approved design or equivalent bounded instruction.
  - Target files and configured validation commands are identified.
  - Implementation can proceed without inventing missing structural behavior.
exclusions:
  - Discovering new design intent.
  - Resolving design, requirement, release, security, business, dependency, or license decisions locally.
  - Closing a quality source finding from the implementation context.
inputs:
  - Approved design or equivalent scoped instruction.
  - Target Python files, packages, tests, or service boundaries.
  - Coding rules and configured test, type-check, lint, format, or dependency commands.
  - Optional quality-feedback items.
outputs:
  - Python code changes and unit-level verification results.
  - Configured static baseline evidence when applicable.
  - Implementation basis design reference.
  - Quality-feedback response, uncertainty list, out-of-scope list, and handoff items.
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
  - id: python_review_spec
    query: Python review criteria and evidence requirements
    required_when: The completed Python implementation is handed to Python review.
    seed_xids: [A9B7C6D5E4F1]
control_refs: []
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
