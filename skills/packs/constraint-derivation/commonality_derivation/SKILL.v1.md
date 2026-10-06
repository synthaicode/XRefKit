---
schema_version: 1
skill_id: commonality_derivation
xid: E7B3C951A2D0
summary: derive cross-cutting commonality candidates from completed primary constraint-derivation outputs
applies_when:
- multiple primary derivation outputs exist and the user needs a second pass for shared implementation candidates or scope-boundary checks
exclusions:
- Generic runtime possibilities without explicit structural evidence are outside this Skill
- Implementation policy is not decided unless explicitly requested
inputs:
- completed DCD/UCD/LCD/ICD/ACD/AACD/CCD/XCD/ISD lists with traceable ids and optional pack-level design context
outputs:
- CD-prefixed commonality file under `work/constraint_derivation/` by default, plus CB-prefixed boundary checks and grouped human confirmation points
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
- id: commonality_derivation_signals
  query: commonality derivation signals
  required_when: Required for this Skill's derivation and classification
  seed_xids:
  - 9C27AE51D648
control_refs:
- 111D282CA0EA
aliases:
- B87A2C3E4568
- B87A2C3E4567
---
<!-- xid: E7B3C951A2D0 -->
<a id="xid-E7B3C951A2D0"></a>

# Skill: commonality_derivation

## Purpose

Run a secondary pass over completed downward or upward derivation outputs to
identify commonality candidates and scope-boundary checks without deciding
integration automatically.

## Inputs

- completed derivation lists from one or more primary Skills

## Outputs

- CD-prefixed commonality candidate table written to a Markdown file
- CB-prefixed scope-boundary check table
- grouped human confirmation points
- written output path

## Startup

- Confirm the primary derivation outputs are available and traceable.
- Load the framework and the commonality signals.
- Verify this is a secondary pass, not a replacement for primary derivation.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_commonality_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Flatten all derivation outputs into one traceable list.
2. Match recurring patterns against the signal catalog.
3. Emit `CD-` items for commonality candidates and `CB-` items for boundary checks.
4. For each `CD-` item, show both the integration benefit and the non-integration risk.
5. Keep the final consolidation decision with the human.
6. Write the result by using `references/commonality_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not merge distinct rules just because their wording looks similar.
- Stop if primary derivation outputs are missing or incomplete.
- Keep source ids visible so later decisions remain traceable.

## Closure

- Return the candidate table, boundary-check table, and next human decisions.
- Highlight any missing primary outputs that reduce secondary-pass reliability.
- Return the written output path.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: commonality_derivation

## Purpose

Run a secondary pass over completed downward or upward derivation outputs to
identify commonality candidates and scope-boundary checks without deciding
integration automatically.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Commonality derivation signals](../../../../knowledge/packs/constraint-derivation/180_commonality_derivation_signals.md#xid-9C27AE51D648)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Commonality derivation output template](../references/commonality_derivation_output_template.md#xid-B6A11501AD6D)

## Inputs

- completed derivation lists from one or more primary Skills

## Outputs

- CD-prefixed commonality candidate table written to a Markdown file
- CB-prefixed scope-boundary check table
- grouped human confirmation points
- written output path

## Startup

- Confirm the primary derivation outputs are available and traceable.
- Load the framework and the commonality signals.
- Verify this is a secondary pass, not a replacement for primary derivation.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_commonality_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Flatten all derivation outputs into one traceable list.
2. Match recurring patterns against the signal catalog.
3. Emit `CD-` items for commonality candidates and `CB-` items for boundary checks.
4. For each `CD-` item, show both the integration benefit and the non-integration risk.
5. Keep the final consolidation decision with the human.
6. Write the result by using `references/commonality_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not merge distinct rules just because their wording looks similar.
- Stop if primary derivation outputs are missing or incomplete.
- Keep source ids visible so later decisions remain traceable.

## Closure

- Return the candidate table, boundary-check table, and next human decisions.
- Highlight any missing primary outputs that reduce secondary-pass reliability.
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

- summary: derive cross-cutting commonality candidates from completed primary constraint-derivation outputs

- use_when: multiple primary derivation outputs exist and the user needs a second pass for shared implementation candidates or scope-boundary checks

- input: completed DCD/UCD/LCD/ICD/ACD/AACD/CCD/XCD/ISD lists with traceable ids and optional pack-level design context

- output: CD-prefixed commonality file under `work/constraint_derivation/` by default, plus CB-prefixed boundary checks and grouped human confirmation points

- constraints: run only after primary derivation outputs exist; aggregate patterns without deciding the final abstraction; keep commonality candidates separate from scope-boundary concerns; write the result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm primary derivation lists are complete enough for a secondary pass and load the shared framework plus the commonality signals
  - planning: flatten all confirmed and unresolved items into one analyzable list while preserving source ids
  - execution: detect recurring patterns, emit CD and CB items, and present tradeoffs rather than deciding integration automatically
  - monitoring_and_control: stop if the task tries to collapse distinct business rules into one abstraction without human confirmation
  - closure: return the candidate table, boundary-check table, and the next human decisions required

- tags: `design`, `cross-cutting`, `requirements-derivation`

- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=commonality_derivation_signals; bind=9C27AE51D648

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
