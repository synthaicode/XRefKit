---
schema_version: 1
skill_id: fact_review
xid: D4E8B2A6F190
summary: review article claims for factual separation, source support, names, numbers, links, and channel-sensitive wording risks
applies_when:
- a draft exists and the article needs evidence-backed checking before release or before further polishing
exclusions:
- Publication approval remains with the human requester
- Unsupported claims or audience assumptions remain unresolved rather than being silently completed
inputs:
- article draft, source links or evidence set, optional claim list, and optional channel targets
outputs:
- fact-review result under `work/editorial_ops/` by default, plus claim findings, unresolved unknowns, and release blockers
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
- 0AA2CEC66CB2
- 7687FD352C4C
---
<!-- xid: D4E8B2A6F190 -->
<a id="xid-D4E8B2A6F190"></a>

# Skill: fact_review

## Purpose

Review article claims against the visible evidence set so factual gaps,
unsupported wording, and release blockers stay explicit.

## Inputs

- article draft
- source links or evidence set
- optional claim list
- target channels

## Outputs

- fact-review result path
- release blockers
- unresolved unknowns

## Startup

- Confirm the draft and source set exist.
- Identify the highest-risk claim classes such as numbers, names, dates, URLs, and quoted assertions.
- Confirm whether the goal is draft feedback or release gating.

## Execution

1. Extract the concrete claims that need checking.
2. Compare each claim to the visible source basis.
3. Classify each result as supported, unsupported, ambiguous, or channel-risky.
4. Mark missing support as `unknown`.
5. Write the review result to the output path and return it.

## Monitoring and Control

- Do not rewrite the article and call it review.
- Do not treat likely truth as verified support.
- Keep opinion and fact findings separate.

## Closure

- Return the fact-review result path.
- Return the release blockers.
- Return the author revision handoff.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: fact_review

## Purpose

Review article claims against the visible evidence set so factual gaps,
unsupported wording, and release blockers stay explicit.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- article draft
- source links or evidence set
- optional claim list
- target channels

## Outputs

- fact-review result path
- release blockers
- unresolved unknowns

## Startup

- Confirm the draft and source set exist.
- Identify the highest-risk claim classes such as numbers, names, dates, URLs, and quoted assertions.
- Confirm whether the goal is draft feedback or release gating.

## Execution

1. Extract the concrete claims that need checking.
2. Compare each claim to the visible source basis.
3. Classify each result as supported, unsupported, ambiguous, or channel-risky.
4. Mark missing support as `unknown`.
5. Write the review result to the output path and return it.

## Monitoring and Control

- Do not rewrite the article and call it review.
- Do not treat likely truth as verified support.
- Keep opinion and fact findings separate.

## Closure

- Return the fact-review result path.
- Return the release blockers.
- Return the author revision handoff.

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

- summary: review article claims for factual separation, source support, names, numbers, links, and channel-sensitive wording risks

- use_when: a draft exists and the article needs evidence-backed checking before release or before further polishing

- input: article draft, source links or evidence set, optional claim list, and optional channel targets

- output: fact-review result under `work/editorial_ops/` by default, plus claim findings, unresolved unknowns, and release blockers

- constraints: review concrete article claims rather than generic writing advice; keep missing support explicit as `unknown`; do not silently rewrite the draft inside the review; write the review result to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the draft and evidence set exist and identify the highest-risk claims
  - planning: decide which claim classes need checking and what counts as a release blocker
  - execution: check claims, classify findings, and write the fact-review result
  - monitoring_and_control: downgrade unsupported conclusions to `unknown` and stop if the task drifts into opinion-only editing
  - closure: return the review path, release blockers, and the author revision handoff

- tags: `editorial`, `review`, `fact-check`, `quality`

- knowledge_slots:
  - name=editorial_framework; bind=F9E58E2BAD21
