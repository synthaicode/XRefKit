---
schema_version: 1
skill_id: cab_review_flow
xid: C7A4E9B2D610
summary: execute CAB evaluation gates for quality, operational readiness, and value alignment before human release confirmation
applies_when:
- user needs CAB-style evaluation before release confirmation
exclusions:
- Human final approval or release decision remains outside this Skill
- Unsupported conclusions remain unresolved rather than being silently completed
inputs:
- release plan materials, manufacturing outputs, requirement and design evidence, value and constraint definitions
outputs:
- quality-gate result, operational readiness result, value-gate result, unresolved list
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
- 33D0A3A01B47
- AE3979CD83C0
---
<!-- xid: C7A4E9B2D610 -->
<a id="xid-C7A4E9B2D610"></a>

# Skill: cab_review_flow

## Purpose

Execute CAB-facing evaluation in the order quality suitability, operational readiness, and value and constraint fit.

## Inputs

- release plan materials
- manufacturing outputs
- design and requirement evidence
- value, constraint, and priority definitions

## Outputs

- quality-gate result
- operational readiness result
- value-gate result
- unresolved list

## Startup

- Confirm CAB input materials exist.
- Confirm design, requirement, and value evidence exists.
- Record `unknown` if required evidence is missing.

## Planning

- Define the CAB evaluation scope.
- Map each business activity to its supporting capability:
  - release plan suitability review
  - operational readiness gate
  - value and constraint fit evaluation
- Prepare management rows for quality, operations, business, and unresolved risk items.

## Execution

- Evaluate release-plan suitability from the quality perspective.
- Evaluate operational readiness.
- Evaluate value and constraint fit.
- Return the three results with explicit evidence and unresolved items.

## Monitoring and Control

- Check that each CAB gate has a recorded result.
- Preserve explicit unresolved risks.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the three gate results to the human decision layer.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Evaluate only; do not decide final release approval.
- Every judgment must cite evidence.
- Preserve unresolved risks explicitly.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: cab_review_flow

## Purpose

Execute CAB-facing evaluation using `CAP-QA-003`, `CAP-OPS-004`, and `CAP-BIZ-001`.

## Required Capability Definitions (XID)


## Inputs

- release plan materials
- manufacturing outputs
- design and requirement evidence
- value, constraint, and priority definitions

## Outputs

- quality-gate result
- operational readiness result
- value-gate result
- unresolved list

## Startup

- Confirm CAB input materials exist.
- Confirm design, requirement, and value evidence exists.
- Record `unknown` if required evidence is missing.

## Planning

- Define the CAB evaluation scope.
- Map each business activity to its supporting capability:
  - release plan suitability review -> `CAP-QA-003`
  - operational readiness gate -> `CAP-OPS-004`
  - value and constraint fit evaluation -> `CAP-BIZ-001`
- Prepare management rows for quality, operations, business, and unresolved risk items.

## Execution

- Evaluate release-plan suitability from the quality perspective.
- Evaluate operational readiness.
- Evaluate value and constraint fit.
- Return the three results with explicit evidence and unresolved items.

## Monitoring and Control

- Check that each CAB gate has a recorded result.
- Preserve explicit unresolved risks.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the three gate results to the human decision layer.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Evaluate only; do not decide final release approval.
- Every judgment must cite evidence.
- Preserve unresolved risks explicitly.

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

- summary: execute CAB business activities through reusable quality, operational-readiness, and value-alignment evaluation capabilities

- use_when: user needs CAB-style evaluation before release confirmation

- input: release plan materials, manufacturing outputs, requirement and design evidence, value and constraint definitions

- output: quality-gate result, operational readiness result, value-gate result, unresolved list

- constraints: evaluate only; do not make final release decision

- lifecycle:
  - startup: confirm CAB evidence exists
  - planning: define gate scope and management rows
  - execution: perform release plan suitability review, operational readiness gate work, and value-constraint fit evaluation through `CAP-QA-003 -> CAP-OPS-004 -> CAP-BIZ-001`
  - monitoring_and_control: downgrade unsupported judgments to `unknown`
  - closure: finalize states and hand off the three gate results to the decision layer

- tags: `cab`, `review`, `release`

- knowledge_slots:
