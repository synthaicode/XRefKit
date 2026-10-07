---
schema_version: 1
skill_id: editorial_ops_index
xid: C8E1A6D3B270
summary: route editorial requests to the correct editorial-ops Skills and keep review and release stages explicit
applies_when:
- a user asks to turn notes, sources, or a draft into a managed article workflow instead of one-shot prompting
exclusions:
- do not skip intake when audience, sources, or channel targets are unclear
- draft generation is not implicit publication approval
inputs:
- topic notes, source links, existing draft state, desired publication channels, and optional urgency or quality concerns
outputs:
- selected Skill sequence, routing rationale, unresolved prerequisites, and a routing note under `work/editorial_ops/` unless another path is specified
criteria:
- id: stage_routing
  statement: The visible editorial state is mapped to the minimum required Skill sequence.
  verification: Compare the routing note with the supplied idea, draft, review, and release state.
- id: review_gate
  statement: Both review Skills precede crosspost release unless draft-only output is explicit.
  verification: Inspect stage order and any recorded skip reason.
- id: unresolved_prerequisites
  statement: Missing audience, source, channel, and approval prerequisites remain explicit.
  verification: Review the routing note open items and next handoff.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: editorial_framework
  query: editorial operations framework for routing and publication boundaries
  required_when: Required for every editorial routing decision unless applicability is explicitly recorded.
  seed_xids:
  - F9E58E2BAD21
control_refs: []
aliases:
- 67179146EEB3
- 14BEA21097F6
---
<!-- xid: C8E1A6D3B270 -->
<a id="xid-C8E1A6D3B270"></a>

# Skill: editorial_ops_index

## Purpose
Route editorial work to the correct pack Skills so intake, drafting, review, and release do not collapse into one prompt.

## Method
1. Confirm whether the request starts from an idea, draft, review, or release state and identify target channels.
2. Resolve the editorial framework Knowledge and preserve its selected XID.
3. Classify the request into `editorial_intake`, `draft_authoring`, `fact_review`, `reader_experience_review`, and/or `crosspost_release`.
4. Require intake when topic framing, source basis, audience, or publication boundary is unclear.
5. Require both reviews before `crosspost_release` unless draft-only output is explicit.
6. Keep skipped stages and reasons explicit, then write the routing note to `work/editorial_ops/` with a date-prefixed filename unless another path is supplied.

## Monitoring, stop, and handoff
- Stop if review is skipped while release readiness is claimed, or if channel adaptation would overwrite source meaning.
- Do not treat one strong source as permission to skip factual separation.
- Return the selected sequence, unresolved prerequisites, and next execution handoff; publication approval remains with the human requester.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: editorial_ops_index

## Purpose

Route editorial work to the correct pack Skills so intake, drafting, review,
and release do not collapse into one prompt.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- topic fragments, notes, or article seeds
- source links or evidence set
- optional existing draft
- publication channels and timeline

## Outputs

- selected Skill sequence
- routing rationale
- explicit missing prerequisites
- routing note path

## Startup

- Confirm whether the request starts from idea, draft, review, or release state.
- Identify which channels the article is intended for.
- Load the routing table and shared principles from the framework knowledge page.

## Execution

1. Classify the request into one or more stages:
   - `editorial_intake`
   - `draft_authoring`
   - `fact_review`
   - `reader_experience_review`
   - `crosspost_release`
2. Require `editorial_intake` when topic framing, source basis, audience, or publication boundary is still unclear.
3. Require both review Skills before `crosspost_release` unless the user explicitly asks for a draft-only output.
4. Keep skipped stages explicit with reason.
5. Write the routing result to the output path and return that path.

## Monitoring and Control

- Stop if review is being skipped while the request still claims release readiness.
- Do not treat one strong source as automatic permission to skip factual separation.
- Do not let channel adaptation silently overwrite the source article meaning.

## Closure

- Return the selected Skill set and order.
- Return the unresolved prerequisites.
- Return the routing note path.

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

- summary: route editorial requests to the correct editorial-ops Skills and keep review and release stages explicit

- use_when: a user asks to turn notes, sources, or a draft into a managed article workflow instead of one-shot prompting

- input: topic notes, source links, existing draft state, desired publication channels, and optional urgency or quality concerns

- output: selected Skill sequence, routing rationale, unresolved prerequisites, and a routing note under `work/editorial_ops/` unless another path is specified

- constraints: do not skip intake when audience, sources, or channel targets are still unclear; do not treat draft generation as implicit approval; keep shared routing rules in knowledge instead of duplicating them across pack Skills; write the routing note to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm whether the request starts from idea fragments, an existing draft, or a release-ready article and identify the target channels
  - planning: map the visible state to the minimum required Skill sequence and determine which prerequisites are still missing
  - execution: route the request, preserve review before release, and keep skipped stages explicit with reason
  - monitoring_and_control: stop if the task tries to publish unresolved factual or audience-fit gaps as completed work
  - closure: return the selected Skill sequence, routing basis, unresolved gaps, and the next execution handoff

- tags: `editorial`, `routing`, `writing`, `review`

- knowledge_slots:
  - name=editorial_framework; bind=F9E58E2BAD21
