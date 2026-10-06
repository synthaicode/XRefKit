---
schema_version: 1
skill_id: editorial_intake
xid: 7C4E9A2D6F81
summary: scope an article task into topic, audience, evidence basis, quality target, and publication boundary before drafting
applies_when:
- article work starts from fragments, loose notes, or vague publication intent and the execution target is not yet stable enough for drafting
exclusions:
- drafting or publication approval
- unsupported claims presented as established evidence
inputs:
- article idea, raw notes, optional links, target audience hints, optional reader capability assumption, and target channels
outputs:
- intake record with topic focus, audience hypothesis, reader capability assumption, evidence basis, channel target, quality checkpoints, and explicit open questions
criteria:
- id: intake_scope
  statement: The intake record states the topic focus, audience, reader capability assumption, and channel boundary.
  verification: Inspect the declared intake record and apply Workflow verification and closure gates.
- id: evidence_basis
  statement: Confirmed evidence, framing assumptions, and missing support are separated.
  verification: Check the intake record for explicit evidence and unknown entries.
- id: draft_handoff
  statement: Quality checkpoints and open questions are recorded for the drafting handoff.
  verification: Inspect the handoff fields and apply Workflow verification and closure gates.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: editorial_operations_framework
  query: editorial operations framework for intake scope and publication boundary
  required_when: Required for every editorial intake unless the parent explicitly records why it is not applicable.
  seed_xids:
  - F9E58E2BAD21
- id: reader_capability_model
  query: reader capability model for audience and prior knowledge assumptions
  required_when: Required when audience capability or assumed prior knowledge affects the intake.
  seed_xids:
  - 125B6C5E3630
control_refs: []
aliases:
- 77F7D4CB9F99
- 54437A84B3D0
---
<!-- xid: 7C4E9A2D6F81 -->
<a id="xid-7C4E9A2D6F81"></a>

# Skill: editorial_intake

## Purpose

Turn a loose article idea into a drafting-ready intake record with an explicit
topic, audience, reader capability assumption, evidence basis, quality target,
and publication boundary.

## Context boundaries

Keep confirmed facts, source-supported claims, framing hypotheses, and missing
support separate. Treat audience labels as hypotheses until the reader's prior
knowledge and capability assumption are stated. The intake may define a
drafting boundary, but it does not approve publication or settle unsupported
claims.

## Method

1. Confirm what the article is trying to say, the intended channels, and the
   smallest useful topic boundary.
2. Resolve the applicable Knowledge needs at the point they are required;
   record the selected XIDs and any unresolved applicability as `unknown`.
3. Separate confirmed facts and supplied evidence from framing assumptions and
   missing source support.
4. State the intended audience, likely reader question, and reader capability
   assumption. For a Zenn technical article, use
   `zenn_practitioner_web_ai` only as the default when stronger evidence is
   absent; override it for learners or specialists.
5. Define quality checkpoints, explanations that can be omitted, and details
   that must remain explicit for the assumed reader.
6. Write the intake record to `work/editorial_ops/` using a date-prefixed name
   unless another output path is specified.
7. Return the intake path, highest-priority open questions, and the
   `draft_authoring` handoff when the boundary is draft-ready.

## Stop, unknowns, and handoff

Preserve missing source support as `unknown`. Stop and hand off when the task
tries to lock publication claims without a source basis or without a usable
reader capability assumption. Keep release approval with the human requester;
the next owner is `draft_authoring` after the intake boundary is accepted.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: editorial_intake

## Purpose

Turn a loose article idea into a drafting-ready intake record with explicit
topic, audience, reader capability assumption, evidence basis, and publication
boundary.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Reader capability model](../../../../knowledge/packs/editorial-ops/120_reader_capability_model.md#xid-125B6C5E3630)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- idea, memo, or topic prompt
- optional source links or citations
- target audience hints
- optional reader capability assumption
- target channels

## Outputs

- intake record path
- topic focus
- reader capability assumption
- evidence basis
- open questions

## Startup

- Confirm what the article is trying to say.
- Confirm what evidence already exists and what is still missing.
- Confirm the intended audience, assumed prior knowledge, and channels.

## Execution

1. Write the article goal in one or two sentences.
2. Separate confirmed facts from framing assumptions.
3. Capture the intended audience, likely reader question, and channel set.
4. Select or describe the reader capability assumption:
   - default to `zenn_practitioner_web_ai` for Zenn technical articles unless stronger evidence points elsewhere
   - override it when the article clearly targets learners or specialists
5. List the evidence basis and missing evidence.
6. Define the quality checkpoints that later review must cover.
7. Record which explanations may be safely omitted and which must remain explicit for the assumed reader.
8. Write the intake result to the output path and return it.

## Monitoring and Control

- Keep missing source support explicit as `unknown`.
- Do not let preferred tone substitute for topic scope.
- Do not let a vague audience label replace a reader capability assumption.
- Stop short of release approval.

## Closure

- Return the intake record path.
- Return the top open questions.
- State that the next step is `draft_authoring` when the intake is draft-ready.

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

- summary: scope an article task into topic, audience, evidence basis, quality target, and publication boundary before drafting

- use_when: article work starts from fragments, loose notes, or vague publication intent and the execution target is not yet stable enough for drafting

- input: article idea, raw notes, optional links, target audience hints, optional reader capability assumption, and target channels

- output: intake record with topic focus, audience hypothesis, reader capability assumption, evidence basis, channel target, quality checkpoints, and explicit open questions

- constraints: do not start from writing style before topic and evidence basis are visible; do not treat audience label alone as enough reader definition when capability assumptions matter; keep facts and framing hypotheses separate; preserve missing source support as `unknown`; write the intake record to `work/editorial_ops/` with a date-prefixed filename unless another path is specified

- lifecycle:
  - startup: confirm the article seed, current source set, audience hints, reader capability assumption, and desired channels
  - planning: decide the smallest viable article boundary and what must be confirmed about both audience and prior knowledge before drafting
  - execution: structure the intake record and separate confirmed inputs from authoring assumptions
  - monitoring_and_control: downgrade unsupported framing claims to open questions and stop if the task tries to lock publication claims without source basis or without a usable reader capability assumption
  - closure: return the intake path, highest-priority open questions, and the drafting handoff

- tags: `editorial`, `intake`, `writing`, `planning`

- knowledge_slots:
  - name=editorial_operations_framework; bind=F9E58E2BAD21
  - name=reader_capability_model; bind=125B6C5E3630
