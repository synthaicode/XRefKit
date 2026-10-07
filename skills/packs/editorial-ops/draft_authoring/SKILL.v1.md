---
schema_version: 1
skill_id: draft_authoring
xid: B6A9D3F1C720
summary: produce an article draft from explicit intake framing and source basis without hiding unsupported claims
applies_when:
- intake has already defined the article boundary and a first draft or revision draft is needed
exclusions:
- Publication approval remains with the human requester
- Unsupported claims or audience assumptions remain unresolved rather than being silently completed
inputs:
- intake record, source set, channel intent, optional structure preference, and optional existing draft
outputs:
- authoring draft under `work/editorial_ops/` by default, plus claim-to-source notes and unresolved authoring questions
criteria:
- id: evidence_and_audience_boundary
  statement: Claims, evidence, reader assumptions, and unresolved support remain explicitly separated
  verification: Inspect the result for traceable evidence and explicit unknowns
- id: human_publication_authority
  statement: The Skill does not approve publication or convert review feedback into factual approval
  verification: Check the handoff and publication boundary before closure
- id: output_closure
  statement: The declared editorial result exists and the next handoff is stated
  verification: Check the output path, open items, and handoff
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: editorial_operations_framework
  query: editorial operations framework
  required_when: Required when applying this Skill's editorial or reader evaluation criteria
  seed_xids:
  - F9E58E2BAD21
control_refs: []
aliases:
- BFEF855AAA8D
- 51FDA8671D61
---
<!-- xid: B6A9D3F1C720 -->
<a id="xid-B6A9D3F1C720"></a>

# Skill: draft_authoring

## Purpose

Produce a usable article draft from explicit framing and sources while keeping
unsupported claims visible instead of polishing them into hidden assumptions.

## Inputs

- intake record
- source set
- optional existing draft
- channel intent

## Outputs

- draft path
- claim-to-source notes
- unresolved authoring questions

## Startup

- Confirm the intake record exists.
- Confirm the source set is enough to support at least a first draft.
- Confirm whether the target is a new draft or revision.

## Execution

1. Build the article spine from the intake goal and audience.
2. Write the draft in that order.
3. Keep unsupported claims marked for later review.
4. Add claim-to-source notes for concrete assertions, numbers, names, and URLs.
5. Write the draft to the output path and return it.

## Monitoring and Control

- Do not convert missing evidence into confident prose.
- Do not treat smooth structure as factual validity.
- Keep channel-specific wording changes reversible.

## Closure

- Return the draft path.
- Return the unresolved authoring questions.
- State that the next steps are `fact_review` and `reader_experience_review`.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: draft_authoring

## Purpose

Produce a usable article draft from explicit framing and sources while keeping
unsupported claims visible instead of polishing them into hidden assumptions.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- intake record
- source set
- optional existing draft
- channel intent

## Outputs

- draft path
- claim-to-source notes
- unresolved authoring questions

## Startup

- Confirm the intake record exists.
- Confirm the source set is enough to support at least a first draft.
- Confirm whether the target is a new draft or revision.

## Execution

1. Build the article spine from the intake goal and audience.
2. Write the draft in that order.
3. Keep unsupported claims marked for later review.
4. Add claim-to-source notes for concrete assertions, numbers, names, and URLs.
5. Write the draft to the output path and return it.

## Monitoring and Control

- Do not convert missing evidence into confident prose.
- Do not treat smooth structure as factual validity.
- Keep channel-specific wording changes reversible.

## Closure

- Return the draft path.
- Return the unresolved authoring questions.
- State that the next steps are `fact_review` and `reader_experience_review`.

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

- summary: produce an article draft from explicit intake framing and source basis without hiding unsupported claims

- use_when: intake has already defined the article boundary and a first draft or revision draft is needed

- input: intake record, source set, channel intent, optional structure preference, and optional existing draft

- output: authoring draft under `work/editorial_ops/` by default, plus claim-to-source notes and unresolved authoring questions

- constraints: do not invent missing facts to smooth the narrative; keep unsupported wording visible for later review; preserve channel-neutral source meaning before channel-specific adaptation; write the draft to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm intake exists and the source basis is sufficient to start drafting
  - planning: define the draft spine, claim order, and where unresolved questions must stay visible
  - execution: write the draft, attach claim-to-source notes, and keep unsupported sections explicit
  - monitoring_and_control: downgrade unsupported certainty to tentative wording and stop if the task tries to bury factual gaps in polished prose
  - closure: return the draft path, major unresolved questions, and the review handoff

- tags: `editorial`, `writing`, `drafting`, `authoring`

- knowledge_slots:
  - name=editorial_framework; bind=F9E58E2BAD21
