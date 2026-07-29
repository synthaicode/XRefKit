<!-- xid: 0ACF69A599D3 -->
<a id="xid-0ACF69A599D3"></a>

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
