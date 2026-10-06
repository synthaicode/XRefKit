---
schema_version: 1
skill_id: cross_constraint_derivation
xid: F4A8D2C6B190
summary: compare DDL structure and C# processing structure to surface missing flows and implicit assumptions
applies_when:
- DDL and corresponding C# code both exist and their mismatch may expose missing use-case handling or undocumented assumptions
exclusions:
- Generic runtime possibilities without explicit structural evidence are outside this Skill
- Implementation policy is not decided unless explicitly requested
inputs:
- DDL or schema definitions, corresponding C# code, and optional mapping hints between tables and code paths
outputs:
- XCD-prefixed derivation file under `work/constraint_derivation/` by default, plus missing-flow and implicit-assumption confirmations
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
- id: cross_constraint_derivation_catalog
  query: cross constraint derivation catalog
  required_when: Required for this Skill's derivation and classification
  seed_xids:
  - B2E5F9DA4C82
control_refs:
- 111D282CA0EA
aliases:
- E5812C0D7FB7
- E5812C0D7FB6
---
<!-- xid: F4A8D2C6B190 -->
<a id="xid-F4A8D2C6B190"></a>

# Skill: cross_constraint_derivation

## Purpose

Compare DDL and C# code as two projections of the same use case and surface
missing flows, undocumented assumptions, and duplicated rule ownership.

## Inputs

- DDL or schema definitions
- corresponding C# code
- optional mapping hints

## Outputs

- XCD-prefixed derivation basis table written to a Markdown file
- missing-flow confirmations
- implicit-assumption confirmations
- written output path

## Startup

- Confirm both DDL and code inputs exist.
- Load the framework and the cross-constraint catalog.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_cross_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Extract valid data-side variations from DDL.
2. Extract handled processing variations from code.
3. Compare the two sides for nullability, multiplicity, state coverage, FK behavior, validation ownership, and default handling.
4. Write the result by using `references/upward_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not silently choose DDL or code as the winner when they disagree.
- Stop if the comparison no longer points to a concrete structural mismatch.

## Closure

- Return the written output path.
- Return the highest-priority mismatches and remaining gaps.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: cross_constraint_derivation

## Purpose

Compare DDL and C# code as two projections of the same use case and surface
missing flows, undocumented assumptions, and duplicated rule ownership.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Cross constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/200_cross_constraint_derivation_catalog.md#xid-B2E5F9DA4C82)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Upward derivation output template](../references/upward_derivation_output_template.md#xid-3266CDEF3729)

## Inputs

- DDL or schema definitions
- corresponding C# code
- optional mapping hints

## Outputs

- XCD-prefixed derivation basis table written to a Markdown file
- missing-flow confirmations
- implicit-assumption confirmations
- written output path

## Startup

- Confirm both DDL and code inputs exist.
- Load the framework and the cross-constraint catalog.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_cross_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Extract valid data-side variations from DDL.
2. Extract handled processing variations from code.
3. Compare the two sides for nullability, multiplicity, state coverage, FK behavior, validation ownership, and default handling.
4. Write the result by using `references/upward_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not silently choose DDL or code as the winner when they disagree.
- Stop if the comparison no longer points to a concrete structural mismatch.

## Closure

- Return the written output path.
- Return the highest-priority mismatches and remaining gaps.

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

- summary: compare DDL structure and C# processing structure to surface missing flows, implicit assumptions, and duplicated rule ownership

- use_when: DDL and corresponding C# code both exist and their mismatch may expose missing use-case handling or undocumented assumptions

- input: DDL or schema definitions, corresponding C# code, and optional mapping hints between tables and code paths

- output: XCD-prefixed derivation file under `work/constraint_derivation/` by default, plus missing-flow and implicit-assumption confirmations

- constraints: compare valid DDL variations against actual code handling instead of assuming one side is authoritative; keep mismatches explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm both DDL and code inputs exist and load the framework plus the cross-constraint catalog
  - planning: identify the entities, fields, states, and flows that must be compared
  - execution: compare DDL and code structures, classify mismatches, and write the XCD result file
  - monitoring_and_control: stop if the comparison drifts into guessed business meaning without structural support
  - closure: return the written derivation path, highest-priority mismatches, and remaining gaps

- tags: `review`, `cross-check`, `.NET`, `requirements-derivation`

- knowledge_slots:
  - name=working_area_policy; bind=111D282CA0EA
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=cross_constraint_derivation_catalog; bind=B2E5F9DA4C82

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
