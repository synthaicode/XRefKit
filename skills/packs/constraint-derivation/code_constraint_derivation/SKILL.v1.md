---
schema_version: 1
skill_id: code_constraint_derivation
xid: 7C4E9A1B2D60
summary: derive hidden assumptions and selected business constraints from explicit C# code choices
applies_when:
- AI-generated or manually reviewed C# code may embed asymmetric branches, implicit preconditions, or hidden business thresholds that need human confirmation
exclusions:
- Generic runtime possibilities without an explicit code choice are outside this Skill
- Language-level exception noise is outside business constraint derivation
- Implementation policy is not decided unless explicitly requested
inputs:
- C# code files, optional target classes or methods, and optional related design context
outputs:
- CCD-prefixed derivation file under `work/constraint_derivation/` by default, plus business-layer confirmation items and implementation-layer notes
criteria:
- id: explicit_code_choice
  statement: Every derivation is grounded in an explicit code choice such as a guard, branch, threshold, silent failure, multiplicity assumption, transaction span, or visibility choice
  verification: Inspect each derivation against the cited code evidence and record unsupported interpretations as unresolved
- id: confirmation_boundary
  statement: Signals are classified as business-layer confirmation or implementation-layer recording
  verification: Review the classification and hand off unsupported business meaning rather than inferring it
- id: output_closure
  statement: The derivation file exists at the declared output path and reports high-priority confirmation items and remaining gaps
  verification: Check the output path and closure report before handing off
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: constraint_derivation_framework
  query: constraint derivation framework
  required_when: Required for deriving and classifying code-choice signals
  seed_xids:
  - 81A6C4E2B190
- id: code_constraint_derivation_catalog
  query: code constraint derivation catalog
  required_when: Required for selecting applicable code signal categories
  seed_xids:
  - A1D4E8C93B71
control_refs:
- 111D282CA0EA
aliases:
- D4701BFC6EA4
- D4701BFC6EA5
---
<!-- xid: 7C4E9A1B2D60 -->
<a id="xid-7C4E9A1B2D60"></a>

# Skill: code_constraint_derivation

## Purpose

Derive hidden assumptions and selected business constraints from explicit C#
code choices without treating generic runtime possibilities as business
signals.

## Inputs

- C# code files
- optional target classes or methods
- optional related design context

## Outputs

- CCD-prefixed derivation basis table written to a Markdown file
- high-priority confirmation items
- implementation-layer notes when justified
- written output path

## Startup

- Confirm the code input exists.
- Load the framework and the code-constraint catalog.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_code_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Detect explicit code-choice signals such as guard-plus-throw, silent failure, multiplicity assumptions, magic values, transaction spans, and visibility choices.
2. Ignore generic runtime possibilities that do not represent an explicit code choice.
3. Classify each signal by whether it requires business-layer confirmation or implementation-layer recording.
4. Write the result by using `references/upward_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not turn generic exceptions such as overflow or out-of-memory into business confirmation items.
- Stop if the interpretation depends on business meaning that is not supported by the code shape.

## Closure

- Return the written derivation path.
- Return the high-priority confirmation items and remaining gaps.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: code_constraint_derivation

## Purpose

Derive hidden assumptions and selected business constraints from explicit C#
code choices without treating generic runtime possibilities as business
signals.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Code constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/190_code_constraint_derivation_catalog.md#xid-A1D4E8C93B71)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Upward derivation output template](../references/upward_derivation_output_template.md#xid-3266CDEF3729)

## Inputs

- C# code files
- optional target classes or methods
- optional related design context

## Outputs

- CCD-prefixed derivation basis table written to a Markdown file
- high-priority confirmation items
- implementation-layer notes when justified
- written output path

## Startup

- Confirm the code input exists.
- Load the framework and the code-constraint catalog.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_code_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Detect explicit code-choice signals such as guard-plus-throw, silent failure, multiplicity assumptions, magic values, transaction spans, and visibility choices.
2. Ignore generic runtime possibilities that do not represent an explicit code choice.
3. Classify each signal by whether it requires business-layer confirmation or implementation-layer recording.
4. Write the result by using `references/upward_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not turn generic exceptions such as overflow or out-of-memory into business confirmation items.
- Stop if the interpretation depends on business meaning that is not supported by the code shape.

## Closure

- Return the written output path.
- Return the high-priority confirmation items and remaining gaps.

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

- summary: derive hidden assumptions and selected business constraints from generated or reviewed C# code

- use_when: AI-generated or manually reviewed C# code may embed asymmetric branches, implicit preconditions, or hidden business thresholds that need human confirmation

- input: C# code files, optional target classes or methods, and optional related design context

- output: CCD-prefixed derivation file under `work/constraint_derivation/` by default, plus business-layer confirmation items and implementation-layer notes

- constraints: derive only from explicit code choices rather than generic runtime possibilities; keep language-level exception noise out; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm code input exists and load the framework plus the code-constraint catalog
  - planning: identify review scope, code signals, and where business-layer confirmation may be required
  - execution: detect selected code signals, classify them, and write the CCD result file
  - monitoring_and_control: stop if unsupported business meaning is being inferred from generic runtime behavior rather than explicit code choices
  - closure: return the written derivation path, high-priority confirmation items, and remaining gaps

- tags: `review`, `code`, `.NET`, `requirements-derivation`

- knowledge_slots:
  - name=working_area_policy; bind=111D282CA0EA
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=code_constraint_derivation_catalog; bind=A1D4E8C93B71

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
