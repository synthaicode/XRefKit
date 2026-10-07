---
schema_version: 1
skill_id: auth_constraint_derivation
xid: C8F2A6D1E430
summary: derive requirement confirmation gates from authentication and authorization structure
applies_when:
- auth or permission specs may leave session, role, or access-boundary behavior to implicit AI completion
exclusions:
- Generic runtime possibilities without explicit structural evidence are outside this Skill
- Implementation policy is not decided unless explicitly requested
inputs:
- auth design docs, role matrices, permission models, API-client auth notes, and account-governance rules
outputs:
- AACD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and permission or session matrices where required
criteria:
- id: evidence_boundary
  statement: Every derivation is grounded in explicit structural evidence and unsupported business meaning remains unresolved
  verification: Review each item against its source structure and record unresolved gaps
- id: output_closure
  statement: The derivation output exists at the declared path and reports confirmation items and remaining gaps
  verification: Check the output path and closure report before handoff
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: constraint_derivation_framework
  query: constraint derivation framework
  required_when: Required for this Skill's derivation and classification
  seed_xids:
  - 81A6C4E2B190
- id: auth_constraint_derivation_catalog
  query: auth constraint derivation catalog
  required_when: Required for this Skill's derivation and classification
  seed_xids:
  - 8B14D9E70326
control_refs:
- 111D282CA0EA
aliases:
- A7691B2D3457
- A7691B2D3456
---
<!-- xid: C8F2A6D1E430 -->
<a id="xid-C8F2A6D1E430"></a>

# Skill: auth_constraint_derivation

## Purpose

Derive requirement confirmation gates from authentication and authorization
structure before access behavior is completed implicitly.

## Inputs

- auth design docs, role matrices, permission models, and account rules

## Outputs

- AACD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- session or permission matrices where required
- written output path

## Startup

- Confirm the input contains authentication or authorization structure.
- Load the framework and the auth catalog.
- Identify session, role, tenant, client-auth, and account-lifecycle surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_auth_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate authentication, authorization, client-auth, and account-management elements.
2. Apply the auth catalog and assign `AACD-` ids.
3. Expand permission or session matrices where the design exposes those axes.
4. Group the results by auth surface.
5. Keep unresolved security behavior explicit instead of assuming safe defaults.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not infer permission behavior from UI visibility alone.
- Stop if session-expiry, role gaps, or tenant-boundary behavior is left implicit.
- Preserve explicit traceability from each AACD item back to the access structure.

## Closure

- Return the AACD table and grouped unresolved items.
- Highlight any session or permission gaps blocking implementation.
- Return the written output path.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: auth_constraint_derivation

## Purpose

Derive requirement confirmation gates from authentication and authorization
structure before access behavior is completed implicitly.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Auth constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/170_auth_constraint_derivation_catalog.md#xid-8B14D9E70326)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md#xid-FF9A33B945ED)

## Inputs

- auth design docs, role matrices, permission models, and account rules

## Outputs

- AACD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- session or permission matrices where required
- written output path

## Startup

- Confirm the input contains authentication or authorization structure.
- Load the framework and the auth catalog.
- Identify session, role, tenant, client-auth, and account-lifecycle surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_auth_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate authentication, authorization, client-auth, and account-management elements.
2. Apply the auth catalog and assign `AACD-` ids.
3. Expand permission or session matrices where the design exposes those axes.
4. Group the results by auth surface.
5. Keep unresolved security behavior explicit instead of assuming safe defaults.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not infer permission behavior from UI visibility alone.
- Stop if session-expiry, role gaps, or tenant-boundary behavior is left implicit.
- Preserve explicit traceability from each AACD item back to the access structure.

## Closure

- Return the AACD table and grouped unresolved items.
- Highlight any session or permission gaps blocking implementation.
- Return the written output path.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: derive requirement confirmation gates from authentication, authorization, and account-governance structure

- use_when: auth or permission specs may leave session, role, or access-boundary behavior to implicit AI completion

- input: auth design docs, role matrices, permission models, API-client auth notes, and account-governance rules

- output: AACD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and permission or session matrices where required

- constraints: derive from explicit access structure and account state, not nominal successful access; keep session, role, tenant-boundary, and account-lifecycle gaps explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the input contains auth or permission structure and load the shared framework plus the auth catalog
  - planning: identify authentication, authorization, client-auth, and account-lifecycle surfaces
  - execution: derive AACD items, expand permission or session matrices where needed, and keep unresolved security behavior explicit
  - monitoring_and_control: stop if auth behavior is being softened into generic best-effort wording or hidden defaults
  - closure: return the derivation table, grouped confirmation items, and blocking session or permission gaps

- tags: `design`, `security`, `requirements-derivation`

- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=auth_constraint_derivation_catalog; bind=8B14D9E70326

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
