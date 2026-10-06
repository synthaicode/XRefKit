---
schema_version: 1
skill_id: investigation_flow
xid: E8B2D6A4C190
summary: investigate service scope, dependencies, viewpoints, and change targets before estimation or design
applies_when:
- user needs impact investigation before estimation or design
exclusions:
- do not decide design or implementation policy
- and preserve unknowns explicitly
inputs:
- request, optional service candidates, optional service catalog path, optional repository or document paths
outputs:
- in-scope service list, out-of-scope service list with reasons, change viewpoints, test viewpoints, change target list, uncertainty list
criteria:
- id: coverage
  statement: Every investigation coverage area has a recorded state.
  verification: Compare the coverage checklist with the investigation record.
- id: target_trace
  statement: Requested change, current affected behavior, and impacted targets are mapped.
  verification: Inspect target evidence and difference statements.
- id: scope_reasons
  statement: Every out-of-scope item and uncertain item has an explicit reason or missing evidence.
  verification: Review the scope and uncertainty lists.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: xddp_basics
  query: XDDP basics
  required_when: Required for change-difference and traceability structure
  seed_xids:
  - 7A2F4C8D1701
- id: xddp_supporting_methods
  query: XDDP supporting methods
  required_when: Required for investigation method selection
  seed_xids:
  - 7A2F4C8D1711
- id: investigation_coverage_checklist
  query: investigation coverage checklist
  required_when: Required for complete investigation coverage
  seed_xids:
  - 91E2A7C56101
control_refs: []
aliases:
- 9C0115875B0C
- 3C06EF778A20
---
<!-- xid: E8B2D6A4C190 -->
<a id="xid-E8B2D6A4C190"></a>

# Skill: investigation_flow

## Purpose
Investigate service scope, dependencies, and change targets before estimation or design.

## Method
1. Confirm the request, service catalog, analysis targets, and coverage checklist; record missing evidence as `unknown`.
2. Resolve the XDDP and investigation Knowledge needs.
3. Define targets and the requested difference; use selective spec-out when documents are weak or stale.
4. Analyze service catalog, source/dependencies, and change-target summaries in order.
5. Preserve mappings from requested change to current behavior and impacted candidates; finalize coverage states.

## Stop and handoff
- Do not decide design or implementation policy.
- Stop or downgrade claims when evidence cannot localize impact; hand unresolved and out-of-scope items to estimation or design.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: investigation_flow

## Purpose

Execute the investigation sequence `CAP-INV-001 -> CAP-INV-002 -> CAP-INV-003` and produce scoped change targets for later estimation or design.

## Required Capability Definitions (XID)


## Required Knowledge (XID)

- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)
- [Investigation coverage checklist](../../knowledge/investigation/100_investigation_coverage_checklist.md#xid-91E2A7C56101)

## Inputs

- request
- optional service catalog path
- optional candidate services supplied by the user
- optional repository or document paths for deeper analysis

## Outputs

- in-scope service list
- out-of-scope service list with reasons
- change-difference investigation view
- change viewpoints
- test viewpoints
- change target list
- change-test viewpoint table
- uncertainty list

## Startup

- Confirm the request exists.
- Confirm the service catalog is available directly or can be located.
- Confirm deeper analysis targets are available when step 2 is needed.
- Load the investigation coverage checklist.
- If required evidence is missing, record `unknown` before proceeding.

## Planning

- Define the investigation targets.
- Treat the request as a difference to existing behavior, assets, or interfaces.
- When official documents are weak or stale, plan selective spec-out rather than broad unfocused code reading.
- Map each business activity to its supporting capability:
  - service catalog analysis -> `CAP-INV-001`
  - source and dependency analysis -> `CAP-INV-002`
  - change-target summarization -> `CAP-INV-003`
- Define the step order: `CAP-INV-001 -> CAP-INV-002 -> CAP-INV-003`.
- Prepare management rows for services, source areas, unresolved questions, and each investigation coverage area.

## Execution

- Perform service catalog analysis by executing `CAP-INV-001`.
- Perform source and dependency analysis by executing `CAP-INV-002`.
- Perform change-target summarization by executing `CAP-INV-003`.
- Preserve the mapping between:
  - requested change
  - current affected behavior or asset
  - impacted target candidates
- Use spec-out style investigation when source code must be used to reconstruct missing understanding.

## Monitoring and Control

- Check that every investigation coverage area has a recorded state.
- Treat any unrecorded coverage area as a leak.
- Downgrade impacted-target claims to `unknown` when the current source or document evidence is not strong enough to localize the change.
- Preserve the reason for every `out_of_scope` item.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Confirm no investigation coverage area remains unrecorded.
- Hand off unresolved items for later estimation or design.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Do not decide implementation policy.
- Do not decide design policy.
- Every out-of-scope item must include a reason.
- Every uncertain item must include the missing evidence.
- Do not skip the current-behavior investigation when the change difference cannot be stated from documents alone.

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

- summary: execute the investigation workflow from service catalog analysis through change-target summary using reusable investigation capabilities

- use_when: user needs impact investigation before estimation or design

- input: request, optional service candidates, optional service catalog path, optional repository or document paths

- output: in-scope service list, out-of-scope service list with reasons, change viewpoints, test viewpoints, change target list, uncertainty list

- constraints: do not decide design or implementation policy; record unknowns explicitly; preserve requested difference and impacted-target discovery explicitly

- lifecycle:
  - startup: confirm request, service catalog, analysis targets, and coverage checklist exist
  - planning: define investigation targets, requested difference, coverage areas, and management rows
  - execution: run service catalog analysis, source and dependency analysis, and change-target summarization through `CAP-INV-001 -> CAP-INV-002 -> CAP-INV-003`, including selective spec-out when needed
  - monitoring_and_control: treat unrecorded coverage areas as leaks and downgrade weak impact evidence to `unknown`
  - closure: finalize states and hand off unresolved or out-of-scope items with impacted-target notes

- tags: `investigation`, `scope`, `planning`

- knowledge_slots:
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=investigation_coverage_checklist; bind=91E2A7C56101
