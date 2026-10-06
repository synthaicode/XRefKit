---
schema_version: 1
skill_id: requirements_flow
xid: D4A7C91E2B60
summary: draft requirements and performance constraints while preserving explicit change differences
applies_when:
- user needs requirement drafting after investigation and estimation
exclusions:
- do not approve final requirements
- hide unresolved assumptions
- or collapse change reason and specification
inputs:
- confirmed assumptions, change target list, test viewpoints, request, optional performance constraints
outputs:
- requirement draft, performance requirement definition, load-test draft plan, unresolved list
criteria:
- id: difference_trace
  statement: Change reason, change requirement, and change specification remain explicit and traceable.
  verification: Inspect the draft for before/after or equivalent difference mapping.
- id: evidence_state
  statement: Weak claims and missing performance evidence remain unknown or out_of_scope.
  verification: Check every requirement row for a recorded status and evidence gap.
- id: handoff
  statement: Unresolved requirement items are handed off without implying approval.
  verification: Inspect the unresolved list and next owner.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: xddp_basics
  query: XDDP basics
  required_when: Required for structuring requirement differences and traceability
  seed_xids:
  - 7A2F4C8D1701
- id: xddp_supporting_methods
  query: XDDP supporting methods
  required_when: Required for selecting supporting requirement methods
  seed_xids:
  - 7A2F4C8D1711
control_refs: []
aliases:
- 2B70BBF7B7BB
- 6720268498FD
---
<!-- xid: D4A7C91E2B60 -->
<a id="xid-D4A7C91E2B60"></a>

# Skill: requirements_flow

## Purpose
Prepare requirement outputs for planning and validation while preserving change differences.

## Method
1. Confirm assumptions, targets, viewpoints, and performance evidence when in scope; record missing evidence as `unknown`.
2. Resolve the XDDP Knowledge needs.
3. Define requirement areas and separate change reason, change requirement, and change specification, preferably in before/after form.
4. Draft requirement and performance outputs at a precision usable downstream; preserve unresolved gaps.
5. Write outputs to the requested location and finalize rows as `done`, `unknown`, or `out_of_scope`.

## Stop and handoff
- Record unclear or unsupported difference items as `unknown` and hand them off without claiming approval.
- Do not approve the draft; hand unresolved items to review or approval owners.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: requirements_flow

## Purpose

Execute `CAP-REQ-001 -> CAP-REQ-002` and prepare requirement outputs for planning and later validation.

## Required Capability Definitions (XID)


## Inputs

- confirmed assumptions
- change target list
- change-test viewpoint table
- request
- optional performance constraints

## Outputs

- requirement draft
- performance requirement definition
- load-test draft plan
- change-requirement specification view for downstream tracing
- unresolved list when evidence is insufficient

## Required Knowledge (XID)

- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)

## Startup

- Confirm assumptions are confirmed.
- Confirm change targets and test viewpoints exist.
- Confirm performance evidence exists when performance requirements are needed.
- Record `unknown` if required evidence is missing.

## Planning

- Define the requirement sections to draft.
- Treat the request as a difference against existing behavior, not only as a fresh requirement statement.
- Separate change reason, change requirement, and change specification explicitly.
- When possible, describe the intended difference in `before / after` form so downstream impact tracing can stay narrow.
- Map each business activity to its supporting capability:
  - requirement draft creation -> `CAP-REQ-001`
  - performance requirement definition -> `CAP-REQ-002`
- Define whether performance work is in scope.
- Prepare management rows for each requirement area and unresolved point.

## Execution

- Perform requirement draft creation by executing `CAP-REQ-001`.
- Perform performance requirement definition by executing `CAP-REQ-002` when performance concerns exist.
- Produce requirement statements at a precision level that can serve as downstream work instructions.
- Preserve the mapping between:
  - change reason
  - change requirement
  - change specification
- Preserve explicit change-difference statements so planning and QA can trace the same delta.
- Preserve unresolved evidence gaps as follow-up items.

## Monitoring and Control

- Check that each requirement area has a recorded status.
- Downgrade weakly supported requirement statements to `unknown`.
- Downgrade requirement text to `unknown` when the difference from current behavior cannot be stated clearly enough for tracing.
- Preserve explicit follow-up items for approval.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off unresolved requirement items for review or approval.
- Escalate out-of-scope requirement questions when reassignment is required.

## Rules

- Do not approve the requirement draft.
- Do not hide unresolved assumptions or performance evidence gaps.
- Do not collapse change reason and change specification into one statement.

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

- summary: execute requirements business activities through reusable requirement and performance-constraint structuring capabilities

- use_when: user needs requirement drafting after investigation and estimation

- input: confirmed assumptions, change target list, test viewpoints, request, optional performance constraints

- output: requirement draft, performance requirement definition, load-test draft plan, unresolved list

- constraints: draft only; do not approve final requirements; preserve change reason, change requirement, and change specification as explicit difference artifacts

- lifecycle:
  - startup: confirm confirmed assumptions and requirement inputs exist
  - planning: define requirement areas, change-difference structure, and management rows
  - execution: perform requirement draft creation and performance requirement definition through `CAP-REQ-001 -> CAP-REQ-002` while preserving change reason and specification mapping
  - monitoring_and_control: downgrade weak requirement claims or unclear delta statements to `unknown`
  - closure: finalize states and hand off unresolved requirement items with traceable difference statements

- tags: `requirements`, `planning`, `analysis`

- knowledge_slots:
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
