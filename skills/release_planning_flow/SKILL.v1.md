---
schema_version: 1
skill_id: release_planning_flow
xid: F5C8A2E6B710
summary: prepare release materials, procedures, monitoring, event response, readiness, and verification evidence for CAB
applies_when:
- user needs release-planning work after manufacturing and testing
exclusions:
- Human final approval or release decision remains outside this Skill
- Unsupported conclusions remain unresolved rather than being silently completed
inputs:
- manufacturing outputs, requirements, design materials, optional performance data
outputs:
- release plan draft, release procedure draft, release confirmation procedure draft, rollback procedure draft, monitoring specification, event-response procedure draft, operational readiness result
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
knowledge_needs:
- id: ipa_release_activity_catalog
  query: IPA release activity catalog
  required_when: Required when checking release-planning activity coverage
  seed_xids:
  - 7B3E5D1A6101
control_refs: []
aliases:
- D216FD3C726C
- 22DE60C2BBCB
---
<!-- xid: F5C8A2E6B710 -->
<a id="xid-F5C8A2E6B710"></a>

# Skill: release_planning_flow

## Purpose

Prepare release materials, monitoring, event response, readiness, and verification in that order for CAB.

## Inputs

- manufacturing outputs
- integration regression verification result
- release policy
- planning basis source list
- design materials
- requirement materials
- optional performance data

## Outputs

- test-environment release plan
- production-environment release plan
- release basis reference
- environment release basis reference
- release procedure draft
- release confirmation procedure draft
- rollback procedure draft
- monitoring specification
- event-response procedure draft
- operational readiness result
- release verification result
- release verification basis reference
- unresolved list

## Startup

- Confirm manufacturing outputs exist.
- Confirm design and requirement materials exist.
- Confirm performance evidence exists when needed.
- Record `unknown` if required evidence is missing.

## Planning

- Define the release-planning scope.
- Map each business activity to its supporting capability:
  - release plan draft creation
  - monitoring design
  - event-response procedure drafting
  - operational readiness gate
  - release verification
- Define the step order explicitly.
- Prepare management rows for planning, monitoring, response procedures, readiness findings, and release verification findings.

## Execution

- Draft the release plan.
- Split the release plan into test-environment and production-environment versions.
- Prepare release, release-confirmation, and rollback procedures as part of the release materials.
- Define placement confirmation steps and behavior confirmation steps inside the release-confirmation procedure.
- Record which release policy entry and planning basis source each environment-specific release plan realizes.
- Check IPA-derived release activity areas and keep missing areas explicit.
- Define monitoring and thresholds.
- Draft event-response procedures.
- Evaluate operational readiness with evidence.
- Evaluate release verification with evidence.
- Check that both placement confirmation evidence and behavior confirmation evidence are present.
- Record which release plan item, release confirmation procedure item, and release basis reference each release verification result confirms.

## Monitoring and Control

- Check that each required release-planning and release-verification artifact has a recorded state.
- Downgrade unsupported readiness conclusions to `unknown`.
- Preserve explicit operational evidence gaps.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off release materials, release basis references, and release verification basis reference to CAB.
- Escalate out-of-scope operational items when reassignment is required.

## Rules

- Do not approve final release timing.
- Do not approve final go/no-go.
- Every judgment in the readiness gate must cite evidence.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Source summary discrepancy

The historical metadata sequence stops at CAP-OPS-004, while the detailed source procedure includes CAP-OPS-005 and release verification. Preserve the detailed procedure and its outputs; this discrepancy is reported, not an inferred runtime capability.

### Original Skill-specific procedure

# Skill: release_planning_flow

## Purpose

Execute `CAP-OPS-001 -> CAP-OPS-002 -> CAP-OPS-003 -> CAP-OPS-004 -> CAP-OPS-005` and prepare release materials and procedures for CAB.

## Required Capability Definitions (XID)


## Inputs

- manufacturing outputs
- integration regression verification result
- release policy
- planning basis source list
- design materials
- requirement materials
- optional performance data

## Outputs

- test-environment release plan
- production-environment release plan
- release basis reference
- environment release basis reference
- release procedure draft
- release confirmation procedure draft
- rollback procedure draft
- monitoring specification
- event-response procedure draft
- operational readiness result
- release verification result
- release verification basis reference
- unresolved list

## Required Knowledge (XID)

- [IPA release activity catalog](../../knowledge/operations/100_ipa_release_activity_catalog.md#xid-7B3E5D1A6101)

## Startup

- Confirm manufacturing outputs exist.
- Confirm design and requirement materials exist.
- Confirm performance evidence exists when needed.
- Record `unknown` if required evidence is missing.

## Planning

- Define the release-planning scope.
- Map each business activity to its supporting capability:
  - release plan draft creation -> `CAP-OPS-001`
  - monitoring design -> `CAP-OPS-002`
  - event-response procedure drafting -> `CAP-OPS-003`
  - operational readiness gate -> `CAP-OPS-004`
  - release verification -> `CAP-OPS-005`
- Define the step order: `CAP-OPS-001 -> CAP-OPS-002 -> CAP-OPS-003 -> CAP-OPS-004 -> CAP-OPS-005`.
- Prepare management rows for planning, monitoring, response procedures, readiness findings, and release verification findings.

## Execution

- Draft the release plan.
- Split the release plan into test-environment and production-environment versions.
- Prepare release, release-confirmation, and rollback procedures as part of the release materials.
- Define placement confirmation steps and behavior confirmation steps inside the release-confirmation procedure.
- Record which release policy entry and planning basis source each environment-specific release plan realizes.
- Check IPA-derived release activity areas and keep missing areas explicit.
- Define monitoring and thresholds.
- Draft event-response procedures.
- Evaluate operational readiness with evidence.
- Evaluate release verification with evidence.
- Check that both placement confirmation evidence and behavior confirmation evidence are present.
- Record which release plan item, release confirmation procedure item, and release basis reference each release verification result confirms.

## Monitoring and Control

- Check that each required release-planning and release-verification artifact has a recorded state.
- Downgrade unsupported readiness conclusions to `unknown`.
- Preserve explicit operational evidence gaps.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off release materials, release basis references, and release verification basis reference to CAB.
- Escalate out-of-scope operational items when reassignment is required.

## Rules

- Do not approve final release timing.
- Do not approve final go/no-go.
- Every judgment in the readiness gate must cite evidence.

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

- summary: execute release-planning business activities through reusable release-material, release-procedure, release-confirmation, signal-specification, response-structuring, and readiness-evaluation capabilities

- use_when: user needs release-planning work after manufacturing and testing

- input: manufacturing outputs, requirements, design materials, optional performance data

- output: release plan draft, release procedure draft, release confirmation procedure draft, rollback procedure draft, monitoring specification, event-response procedure draft, operational readiness result

- constraints: do not approve release timing or final go or no-go

- lifecycle:
  - startup: confirm manufacturing outputs and release-planning evidence exist
  - planning: define release-planning scope and management rows
  - execution: perform release plan drafting, monitoring design, event-response drafting, and operational readiness gate work through `CAP-OPS-001 -> CAP-OPS-002 -> CAP-OPS-003 -> CAP-OPS-004`
  - monitoring_and_control: downgrade unsupported readiness conclusions to `unknown`
  - closure: finalize states and hand off release materials to CAB

- tags: `operations`, `release`, `planning`

- knowledge_slots:
