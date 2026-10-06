---
schema_version: 1
skill_id: logic_constraint_derivation
xid: 3D7A9E2B4C60
summary: derive requirement confirmation gates from branching, calculations, state transitions, and approval logic
applies_when:
- business-logic specs may leave boundary, exception, or transition behavior to implicit AI completion
exclusions:
- do not infer unspecified else-paths or business rules from examples
inputs:
- flowcharts, calculation rules, state models, approval rules, and logic design notes
outputs:
- LCD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and any required state-transition matrix
criteria:
- id: logic_evidence
  statement: Every LCD item is grounded in an observed branch, calculation, transition, approval, or control rule.
  verification: Check each item against the supplied logic evidence.
- id: boundary_coverage
  statement: Unresolved branches, invalid values, and calculation or transition boundaries remain explicit.
  verification: Review the transition matrix and unresolved items.
- id: output_closure
  statement: The derivation file exists at the declared output path with grouped confirmations and gaps.
  verification: Check the output path before handoff.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: constraint_derivation_framework
  query: constraint derivation framework
  required_when: Required for deriving and classifying logic signals
  seed_xids:
  - 81A6C4E2B190
- id: logic_constraint_derivation_catalog
  query: logic constraint derivation catalog
  required_when: Required for selecting logic signal categories
  seed_xids:
  - 4E5B8923C912
control_refs:
- 111D282CA0EA
aliases:
- D436E8FA0123
- D436E8FA0124
---
<!-- xid: 3D7A9E2B4C60 -->
<a id="xid-3D7A9E2B4C60"></a>

# Skill: logic_constraint_derivation

## Purpose
Derive requirement confirmation gates from business-logic structure before exception paths are filled in implicitly.

## Inputs
- logic specs, flowcharts, calculations, and state-transition definitions

## Outputs
- LCD-prefixed derivation basis table
- grouped requirement confirmation list
- state-transition matrix when required
- written output path

## Startup
- Confirm the input contains branch, calculation, or transition structure.
- Load framework and logic catalog Knowledge.
- Use `work/constraint_derivation/YYYY-MM-DD_logic_constraint_derivation_<topic>.md` unless an output path is supplied.

## Execution
1. Enumerate branches, calculations, transitions, approvals, and control rules.
2. Apply the logic catalog and assign `LCD-` ids.
3. Expand transition matrices where current-state and action axes are exposed.
4. Group results by logic unit and keep unresolved boundaries explicit.
5. Write the result using the primary derivation output template or an equivalent structure.

## Monitoring and Control
- Do not accept a single happy-path example as full logic coverage.
- Stop if invalid transitions or boundary calculations are skipped.
- Preserve confirmed rules separately from unconfirmed cases.

## Closure and Handoff
- Return the LCD table, grouped unresolved items, blocking matrices, and path.
- Hand unresolved business meaning to the responsible human or design owner.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: logic_constraint_derivation

## Purpose

Derive requirement confirmation gates from business-logic structure before
exception paths are filled in implicitly.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Logic constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/140_logic_constraint_derivation_catalog.md#xid-4E5B8923C912)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md#xid-FF9A33B945ED)

## Inputs

- logic specs, flowcharts, calculations, and state-transition definitions

## Outputs

- LCD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- state-transition matrix when required
- written output path

## Startup

- Confirm the input contains branch, calculation, or transition structure.
- Load the framework and the logic catalog.
- Identify where transition matrices or boundary cases are structurally required.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_logic_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate branches, calculations, transitions, approvals, and control rules.
2. Apply the logic catalog and assign `LCD-` ids.
3. Expand transition matrices where the design exposes current-state and action axes.
4. Group the results by logic unit.
5. Keep unresolved branches, invalid values, and boundary behavior explicit.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not accept a single happy-path example as full logic coverage.
- Stop if invalid transitions or boundary calculations are being skipped.
- Preserve the difference between confirmed rules and unconfirmed cases.

## Closure

- Return the LCD table and grouped unresolved items.
- Highlight any transition or calculation matrices that block implementation.
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

- summary: derive requirement confirmation gates from branching, calculations, state transitions, and approval logic

- use_when: business-logic specs may leave boundary, exception, or transition behavior to implicit AI completion

- input: flowcharts, calculation rules, state models, approval rules, and logic design notes

- output: LCD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and any required state-transition matrix

- constraints: derive all structurally implied branches and boundaries; do not infer unspecified else-paths; keep state-transition and calculation edge cases explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the input contains business logic structure and load the shared framework plus the logic catalog
  - planning: identify branching, calculations, transitions, and approval-flow areas
  - execution: derive LCD items, expand transition matrices where required, and keep unresolved logic explicit
  - monitoring_and_control: stop if unsupported business rules are being guessed from examples or happy paths
  - closure: return the derivation table, grouped confirmation items, and any transition matrices requiring approval

- tags: `design`, `logic`, `requirements-derivation`

- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=logic_constraint_derivation_catalog; bind=4E5B8923C912

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
