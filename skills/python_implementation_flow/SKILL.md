<!-- xid: C5D6E7F8A9B1 -->
<a id="xid-C5D6E7F8A9B1"></a>

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
