---
schema_version: 1
skill_id: planning_flow
xid: 6A4F8C2D1E71
summary: Prepare traceable work planning and change policies from approved requirements and current source findings.
applies_when:
- user needs planning after requirements are approved
exclusions:
- Finalizing business priority or resource allocation.
- Inventing target structure or hiding unresolved policy and dependency assumptions.
inputs:
- approved requirements, change target list, current source structure findings, domain knowledge references
outputs:
- work plan, source modification policy, data change policy, data correction tool policy, test policy, test tool policy, release policy, planning basis source list, created or refreshed current-source-structure finding XIDs when target structure was missing
criteria:
- id: approved_input_scope
  statement: Planning starts from approved requirements and named change targets while preserving the requirement difference as the planning anchor.
  verification: Inspect planning scope and traceability rows for approved input references and concrete target mappings.
- id: canonical_source_basis
  statement: Every source modification target has a current canonical source structure finding XID or an explicit out_of_scope reason.
  verification: Compare all target rows with registered finding XIDs and confirm missing or stale findings have pre analysis and registration handoffs.
- id: policy_coverage
  statement: Work planning covers source modification, data change and correction, test and test tools, and separate test environment and production release policies.
  verification: Inspect each policy output and its recorded source or domain basis.
- id: unknown_handoff
  statement: Weak assumptions, unsupported impact mappings, and unresolved policy or assignment questions remain unknown with an explicit downstream owner.
  verification: Review unknown rows for evidence gaps, affected targets, downstream impact, and analysis, confirmation, or reassignment handoff.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: xddp_basics
  query: XDDP basics
  required_when: Required to anchor requirement differences and planning traceability.
  seed_xids:
  - 7A2F4C8D1701
- id: xddp_supporting_methods
  query: XDDP supporting methods
  required_when: Required when selecting planning traceability and policy methods.
  seed_xids:
  - 7A2F4C8D1711
- id: common_source_analysis_criteria
  query: common source analysis criteria
  required_when: Required to assess current source structure evidence for planning targets.
  seed_xids:
  - 5F21C8A41001
- id: custom_framework_common_criteria
  query: custom framework common criteria
  required_when: Required when the target uses the custom framework and its common structure criteria.
  seed_xids:
  - 5F21C8A41002
- id: custom_framework_analysis_criteria
  query: C# custom framework analysis criteria
  required_when: Required when planning a C# custom framework source target.
  seed_xids:
  - 30E6A4F6F3AB
- id: ipa_release_activity_catalog
  query: IPA release activity catalog
  required_when: Required to build release policies from IPA release activity areas.
  seed_xids:
  - 7B3E5D1A6101
control_refs: []
aliases:
- 486C9EEE8A9D
- E3F2F376922F
---
<!-- xid: 6A4F8C2D1E71 -->
<a id="xid-6A4F8C2D1E71"></a>

# Skill: planning_flow

## Purpose

Prepare work planning outputs from approved requirements, domain Knowledge, and current source findings.

## Method

1. Confirm approved requirements, change targets, current source findings, and required Knowledge references. Record `unknown` when inputs are missing. Use the requirement difference as the planning anchor.
2. For each source modification target, verify that a current canonical source structure finding XID exists and covers the needed structure pivots, runtime flows, persistence boundaries, extension mechanisms, variation points, and verification needs. If missing or stale, tell the user that local source inspection is required, run `source_structure_overview`, and publish the result through `source_structure_findings_registration` before using it as a planning basis.
3. Build the change traceability view from each requirement difference to impacted modules, files, documents, registrations, or operational assets. Separate common and project-specific impact and record the basis source for each planning policy.
4. Define planning scope and downstream design policy targets. Prepare management rows for planning outputs, source finding creation or registration, dependencies, policy assumptions, and unresolved ownership. Do not finalize business priority or resource allocation.
5. Draft source modification policy from current source structure, recording an explicit reason for any departure. Draft data change policy and state whether a dedicated correction tool is required, including how it will be created and verified.
6. Draft test policy and selected test tool policy, including how a missing suitable tool would be created and verified. Build release policy from the IPA release activity catalog and separate test environment and production environment plans.
7. Finalize work plan, planning basis source list, change design basis notes, and all policy outputs with rows marked `done`, `unknown`, or `out_of_scope`. Downgrade weak assumptions, unsupported source claims, and unclear impact mappings to `unknown`.

## Stop and handoff

- Stop planning closure when an in scope source target lacks a current canonical source finding and is not explicitly out of scope. Route source inspection and canonical registration first.
- Do not invent target structure, use unregistered local notes as the planning basis, finalize priority or resource allocation, or hide requirement-to-target differences.
- Hand off the work plan, planning basis source list, change design basis notes, policies, current finding XIDs, and unresolved items to design work. Escalate out_of_scope planning questions when reassignment is required.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: planning_flow

## Purpose

Execute `CAP-PLN-001` and prepare work planning outputs from approved requirements, domain knowledge, and current-source findings.

## Required Capability Definitions (XID)


## Inputs

- approved requirements
- change target list
- current source structure findings
- domain knowledge references

## Required Knowledge (XID)

- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)
- [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)
- [C# custom framework analysis criteria](../../knowledge/csharp/110_custom_framework_analysis_criteria.md#xid-30E6A4F6F3AB)
- [IPA release activity catalog](../../knowledge/operations/100_ipa_release_activity_catalog.md#xid-7B3E5D1A6101)

## Outputs

- work plan
- change traceability view for planning scope
- source modification policy
- data change policy
- data correction tool policy
- test policy
- test tool policy
- release policy
- planning basis source list
- change-design basis notes
- created or refreshed current-source-structure finding XIDs when target
  structure was missing at planning start

## Startup

- Confirm approved requirements exist.
- Confirm change targets are available.
- Confirm current source findings and domain knowledge references are available
  for every source-modification target.
- If a target lacks current source structure findings, do not proceed by
  guessing the structure. Tell the user that this run must inspect local source
  files to create or refresh current structure information, then run
  `source_structure_overview` for that local source scope. Register the result
  as canonical domain knowledge through `source_structure_findings_registration`
  before using it as a planning basis.
- Record `unknown` if planning inputs are missing.

## Planning

- Define planning scope and downstream design-policy targets.
- Identify which domain knowledge and current-source findings govern the target scope.
- Decide whether current source structure information is missing or stale for
  any target:
  - no current source structure finding exists for the target in the canonical
    knowledge catalog
  - the finding predates the relevant source shape
  - the finding does not cover the target's structure pivots, runtime flows,
    state/persistence boundaries, extension/convention mechanisms, or known
    variation points needed for planning
  - the source modification policy would otherwise rely on an unverified
    structure assumption
- When current structure information is missing, create a management row for
  the source-structure creation and registration handoff before source
  modification policy drafting.
- Build a traceability view from requirement differences to impacted modules, files, documents, or operational assets.
- Separate common impact and project-specific impact when the same asset serves multiple change areas.
- Map the business activity to its supporting capability:
  - work planning and policy drafting -> `CAP-PLN-001`
- Prepare management rows for planning outputs and unresolved policy assumptions.

## Execution

- Perform work planning and policy drafting by executing `CAP-PLN-001`.
- Use the requirement difference as the planning anchor, not only the final desired state.
- Before drafting source modification policy for a source target, verify that a
  current-source-structure finding XID exists in canonical domain knowledge.
- When missing or stale, run `source_structure_overview` for that target and
  first state to the user that local source inspection is required for the
  current run. Route the output through `source_structure_findings_registration`
  with authorized publication before using the finding as planning basis.
- Record which requirement difference maps to which target file, function, module, document, registration, or operational artifact.
- Build policy outputs so they can serve as pre-code change-design guidance rather than only as broad planning notes.
- Build source modification policy from the current source structure by default.
- Record an explicit reason if the plan intentionally departs from the current structure.
- Build release policy by checking IPA-derived release activity areas, not only deployment steps.
- Separate release policy into at least test-environment and production-environment plans.
- For data change work, state whether a dedicated correction tool is required and how that tool will be created and verified.
- For test work, state which test tools are selected and, if no suitable tool exists, how a new tool will be created and verified.
- Record the source files, modules, registrations, or framework artifacts used as the basis of each planning policy.
- Produce planning outputs and preserve unresolved planning assumptions explicitly.

## Monitoring and Control

- Check that all required planning outputs have a recorded result.
- Downgrade weakly supported planning assumptions to `unknown`.
- Downgrade source-structure claims to `unknown` if no current-source finding supports them.
- Stop planning closure when a source-modification target lacks a current
  canonical source-structure finding and is not explicitly out of scope.
- Downgrade impact mappings to `unknown` when the requirement-to-target relation cannot be traced clearly enough for downstream design or review.
- Preserve unresolved policy, dependency, or assignment questions.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Confirm every source-modification target has a current source-structure
  finding XID in canonical domain knowledge or an explicit `out_of_scope`
  reason.
- Confirm any source-structure findings created during planning were registered
  through `source_structure_findings_registration` before they are used as
  planning basis.
- Hand off the planning outputs, planning basis source list, and unresolved planning items to design work.
- Escalate out-of-scope planning questions when reassignment is required.

## Rules

- Do not finalize resource allocation.
- Do not finalize business priority.
- Do not invent a target structure without checking the current codebase first.
- Do not use a local work report as the planning source-structure basis until
  it has been registered as canonical domain knowledge.
- Do not let planning outputs hide which concrete difference they are meant to realize.

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

- summary: execute planning business activity through reusable work-and-policy planning capability grounded in domain knowledge and current-source findings

- use_when: user needs planning after requirements are approved

- input: approved requirements, change target list, current source structure findings, domain knowledge references

- output: work plan, source modification policy, data change policy, data correction tool policy, test policy, test tool policy, release policy, planning basis source list, created or refreshed current-source-structure finding XIDs when target structure was missing

- constraints: draft only; do not finalize priority or resource allocation; keep requirement-to-target difference tracing explicit for downstream design and review; do not use unregistered local source-structure notes as planning basis; when current source structure findings are missing or stale, create latest structure information with `source_structure_overview` and register it through `source_structure_findings_registration` before planning relies on it

- lifecycle:
  - startup: confirm approved requirements, current source findings, and domain knowledge references exist; if target structure information is missing or stale, require `source_structure_overview` plus `source_structure_findings_registration` before using it as planning basis
  - planning: define planning scope, policy targets, requirement-to-target traceability, current-source-finding gaps, structure-creation/registration rows, and management rows from domain knowledge and current-source findings
  - execution: perform work planning and policy drafting through `CAP-PLN-001` while preserving impacted target mapping and creating/registering missing current source structure findings before source policy relies on them
  - monitoring_and_control: downgrade weak planning assumptions, unsupported source-structure claims, and unclear impact mappings to `unknown`; stop closure when an in-scope source target lacks a canonical current-source-structure finding
  - closure: finalize states and hand off planning outputs, planning basis source list, current-source-structure finding XIDs, and change-design basis notes with unresolved items

- tags: `planning`, `execution`, `policy`

- knowledge_slots:
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=common_source_analysis_criteria; bind=5F21C8A41001
  - name=custom_framework_common_criteria; bind=5F21C8A41002
  - name=custom_framework_analysis_criteria; bind=30E6A4F6F3AB
  - name=ipa_release_activity_catalog; bind=7B3E5D1A6101
