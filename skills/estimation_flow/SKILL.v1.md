---
schema_version: 1
skill_id: estimation_flow
xid: E2B7D9F4A130
summary: prepare estimation options, supplier checks, and assumption clarification before requirements
applies_when:
- user needs estimate options, supplier checks, or assumption clarification before requirements
exclusions:
- Human final approval or release decision remains outside this Skill
- Unsupported conclusions remain unresolved rather than being silently completed
inputs:
- request, change target list, supplier definitions, optional budget definition
outputs:
- supplier check results, cost patterns, solution options, assumption list, ambiguity classification
criteria:
- id: semantic_sequence
  statement: The Skill's evaluation sequence and semantic criteria are applied in order without embedding routing or capability identifiers
  verification: Inspect each phase result and evidence link against the method sequence
- id: decision_boundary
  statement: Human final-decision authority remains explicit and unsupported judgments remain unknown
  verification: Check closure, rules, and handoff for approval boundaries
- id: output_closure
  statement: The declared result and unresolved items are returned with a handoff
  verification: Check the output and handoff before closure
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs: []
control_refs: []
aliases:
- FB65EC653F0F
- EA208AA244DF
---
<!-- xid: E2B7D9F4A130 -->
<a id="xid-E2B7D9F4A130"></a>

# Skill: estimation_flow

## Purpose

Execute supplier checking, cost estimation, solution option generation, and assumption ambiguity classification in that order.

## Inputs

- request
- change target list
- supplier definitions
- optional budget definition

## Outputs

- four-condition comparison result
- issue list
- cost estimate patterns
- solution options with effort and risk
- assumption list
- ambiguity classification result
- confirmation-required item list

## Startup

- Confirm the request and change target list exist.
- Confirm supplier definitions are available.
- Confirm budget definitions exist when cost estimation is required.
- Record `unknown` for missing evidence before proceeding.

## Planning

- Define the estimation scope and target assumptions.
- Map each business activity to its supporting capability:
  - supplier four-condition check
  - cost estimation
  - solution option generation
  - assumption ambiguity classification
- Define the step order explicitly.
- Prepare management rows for supplier checks, cost patterns, options, and assumptions.

## Execution

- Perform the supplier four-condition check.
- Perform cost estimation.
- Perform solution option generation.
- Consult on option differences, direction tradeoffs, and assumption impacts when comparison cannot be closed inside the current boundary.
- Perform assumption ambiguity classification.

## Monitoring and Control

- Check that each required supplier and assumption item has a recorded result.
- Downgrade weakly supported assumptions to `unknown`.
- Preserve explicit assumption gaps for confirmation.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off assumptions that need confirmation.
- Escalate out-of-scope supplier or budget items when reassignment is required.

## Rules

- Do not approve supplier adoption.
- Do not approve final budget or delivery direction.
- Every unresolved assumption must remain explicit.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: estimation_flow

## Purpose

Execute the sequence `CAP-SUP-001 -> CAP-SUP-002 -> CAP-EST-001 -> CAP-EST-002` and prepare inputs for requirements work.

## Required Capability Definitions (XID)


## Inputs

- request
- change target list
- supplier definitions
- optional budget definition

## Outputs

- four-condition comparison result
- issue list
- cost estimate patterns
- solution options with effort and risk
- assumption list
- ambiguity classification result
- confirmation-required item list

## Startup

- Confirm the request and change target list exist.
- Confirm supplier definitions are available.
- Confirm budget definitions exist when cost estimation is required.
- Record `unknown` for missing evidence before proceeding.

## Planning

- Define the estimation scope and target assumptions.
- Map each business activity to its supporting capability:
  - supplier four-condition check -> `CAP-SUP-001`
  - cost estimation -> `CAP-SUP-002`
  - solution option generation -> `CAP-EST-001`
  - assumption ambiguity classification -> `CAP-EST-002`
- Define the step order: `CAP-SUP-001 -> CAP-SUP-002 -> CAP-EST-001 -> CAP-EST-002`.
- Prepare management rows for supplier checks, cost patterns, options, and assumptions.

## Execution

- Perform supplier four-condition check by executing `CAP-SUP-001`.
- Perform cost estimation by executing `CAP-SUP-002`.
- Perform solution option generation by executing `CAP-EST-001`.
- Consult on option differences, direction tradeoffs, and assumption impacts when comparison cannot be closed inside the current boundary.
- Perform assumption ambiguity classification by executing `CAP-EST-002`.

## Monitoring and Control

- Check that each required supplier and assumption item has a recorded result.
- Downgrade weakly supported assumptions to `unknown`.
- Preserve explicit assumption gaps for confirmation.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off assumptions that need confirmation.
- Escalate out-of-scope supplier or budget items when reassignment is required.

## Rules

- Do not approve supplier adoption.
- Do not approve final budget or delivery direction.
- Every unresolved assumption must remain explicit.

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

- summary: execute estimation business activities through reusable comparison, projection, option-structuring, and ambiguity-classification capabilities

- use_when: user needs estimate options, supplier checks, or assumption clarification before requirements

- input: request, change target list, supplier definitions, optional budget definition

- output: supplier check results, cost patterns, solution options, assumption list, ambiguity classification

- constraints: do not approve supplier adoption, budget, or final direction

- lifecycle:
  - startup: confirm request, change targets, supplier definitions, and budget evidence as needed
  - planning: define estimation scope and management rows
  - execution: perform supplier four-condition check, cost estimation, solution option generation, consultation on option tradeoffs when needed, and assumption ambiguity classification through `CAP-SUP-001 -> CAP-SUP-002 -> CAP-EST-001 -> CAP-EST-002`
  - monitoring_and_control: downgrade weak assumptions to `unknown`; preserve confirmation items
  - closure: finalize states and hand off unresolved assumptions

- tags: `estimation`, `planning`, `supplier`

- knowledge_slots:
