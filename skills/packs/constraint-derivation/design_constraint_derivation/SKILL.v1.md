---
schema_version: 1
skill_id: design_constraint_derivation
xid: A6D9F3B1C720
summary: derive requirement confirmation gates from data-structure, database, relationship, and operation design
applies_when:
- DDL, schema, ER, or CRUD-oriented design structures may hide unresolved behavior that AI would otherwise complete implicitly
exclusions:
- Generic runtime possibilities without explicit structural evidence are outside this Skill
- Implementation policy is not decided unless explicitly requested
inputs:
- DDL, schema definitions, ER models, CRUD design notes, and related operation descriptions
outputs:
- DCD-prefixed derivation file under `work/constraint_derivation/` by default, plus design-time decision list and any required combination-expansion matrix
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
- id: design_constraint_derivation_catalog
  query: design constraint derivation catalog
  required_when: Required for this Skill's derivation and classification
  seed_xids:
  - 2D14F88A6C01
control_refs:
- 111D282CA0EA
aliases:
- B214C6D8E012
- B214C6D8E011
---
<!-- xid: A6D9F3B1C720 -->
<a id="xid-A6D9F3B1C720"></a>

# Skill: design_constraint_derivation

## Purpose

Derive requirement confirmation gates from data-structure design before
implementation starts.

## Inputs

- DDL, schema definitions, ER diagrams, and CRUD design notes

## Outputs

- DCD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- design-time decision list
- combination-expansion matrix when structurally required
- written output path

## Startup

- Confirm the input contains schema or operation structure.
- Load the framework and the design catalog.
- Identify any nullable, relational, state, or operation axes that may require matrix expansion.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_design_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate design elements by type, constraint, relation, operation, and business pattern.
2. Apply the design catalog mechanically and assign `DCD-` ids.
3. Separate requirement confirmations from design-time decisions.
4. Expand combination cases only when the design structure actually creates them.
5. Emit unresolved items as `未確定`; do not fill them in from implied defaults.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not collapse `null`, `0`, `not found`, and `multiple` into one vague case.
- Stop if the task tries to move into implementation before DCD items are confirmed.
- Keep the derivation basis traceable back to the design structure.

## Closure

- Return the derivation table and grouped unresolved items.
- Highlight any matrix expansions that must be confirmed before implementation.
- Return the written output path.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: design_constraint_derivation

## Purpose

Derive requirement confirmation gates from data-structure design before
implementation starts.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Design constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/120_design_constraint_derivation_catalog.md#xid-2D14F88A6C01)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md#xid-FF9A33B945ED)

## Inputs

- DDL, schema definitions, ER diagrams, and CRUD design notes

## Outputs

- DCD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- design-time decision list
- combination-expansion matrix when structurally required
- written output path

## Startup

- Confirm the input contains schema or operation structure.
- Load the framework and the design catalog.
- Identify any nullable, relational, state, or operation axes that may require matrix expansion.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_design_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate design elements by type, constraint, relation, operation, and business pattern.
2. Apply the design catalog mechanically and assign `DCD-` ids.
3. Separate requirement confirmations from design-time decisions.
4. Expand combination cases only when the design structure actually creates them.
5. Emit unresolved items as `未確定`; do not fill them in from implied defaults.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not collapse `null`, `0`, `not found`, and `multiple` into one vague case.
- Stop if the task tries to move into implementation before DCD items are confirmed.
- Keep the derivation basis traceable back to the design structure.

## Closure

- Return the derivation table and grouped unresolved items.
- Highlight any matrix expansions that must be confirmed before implementation.
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

- summary: derive requirement confirmation gates from data-structure, database, relationship, and operation design

- use_when: DDL, schema, ER, or CRUD-oriented design structures may hide unresolved behavior that AI would otherwise complete implicitly

- input: DDL, schema definitions, ER models, CRUD design notes, and related operation descriptions

- output: DCD-prefixed derivation file under `work/constraint_derivation/` by default, plus design-time decision list and any required combination-expansion matrix

- constraints: keep derivation mechanical and structure-driven; do not invent missing business behavior; separate design-time decisions from requirement confirmations; expand combinations only when structural axes are present; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the input contains data or operation structure and load the shared framework plus the design catalog
  - planning: identify design elements and likely combination axes
  - execution: enumerate elements, derive DCD items, expand matrices where required, and emit unresolved items explicitly
  - monitoring_and_control: downgrade unsupported assumptions to unresolved and stop if the user tries to bypass unconfirmed structural cases
  - closure: return the derivation table, grouped confirmation items, design-time decisions, and remaining gaps

- tags: `design`, `data-structure`, `requirements-derivation`

- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=design_constraint_derivation_catalog; bind=2D14F88A6C01

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
