---
schema_version: 1
skill_id: planning_flow
xid: 6A4F8C2D1E71
aliases: [486C9EEE8A9D, E3F2F376922F]
summary: Prepare traceable work planning and change policies from approved requirements and current source findings.
applies_when:
  - Approved requirements and a concrete change target list are available.
  - Current source structure findings and required domain Knowledge can be resolved, or a pre analysis handoff is needed.
exclusions:
  - Finalizing business priority or resource allocation.
  - Inventing target structure or hiding unresolved policy and dependency assumptions.
inputs:
  - Approved requirements and change target list.
  - Canonical current source structure findings and relevant domain Knowledge references.
outputs:
  - Work plan, change traceability view, source and data change policies, test and release policies, and planning basis source list.
  - Data correction and test tool policy decisions, change design basis notes, and current source finding XIDs created or refreshed during planning.
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
knowledge_needs:
  - id: xddp_basics
    query: XDDP basics
    required_when: Required to anchor requirement differences and planning traceability.
    seed_xids: [7A2F4C8D1701]
  - id: xddp_supporting_methods
    query: XDDP supporting methods
    required_when: Required when selecting planning traceability and policy methods.
    seed_xids: [7A2F4C8D1711]
  - id: common_source_analysis_criteria
    query: common source analysis criteria
    required_when: Required to assess current source structure evidence for planning targets.
    seed_xids: [5F21C8A41001]
  - id: custom_framework_common_criteria
    query: custom framework common criteria
    required_when: Required when the target uses the custom framework and its common structure criteria.
    seed_xids: [5F21C8A41002]
  - id: custom_framework_analysis_criteria
    query: C# custom framework analysis criteria
    required_when: Required when planning a C# custom framework source target.
    seed_xids: [30E6A4F6F3AB]
  - id: ipa_release_activity_catalog
    query: IPA release activity catalog
    required_when: Required to build release policies from IPA release activity areas.
    seed_xids: [7B3E5D1A6101]
control_refs: []
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
