---
schema_version: 1
skill_id: business_learning_interview
xid: B6C4E9A2D781
summary: learn a business task through goal-first interview cycles and turn partial fragments into a structured provisional hypothesis
applies_when:
- a user wants to teach the AI about a business task conversationally, but can better explain the intended goal than the full process, or only knows fragments, tacit operational knowledge, bottlenecks, or partial handoffs
exclusions:
- detailed execution procedure design before the business boundary is explicit
- treating one anecdote or an AI inference as an established business rule
inputs:
- one or more starting seeds such as goal or expected result, task name, role name, artifact, bottleneck, repeated error, approval point, or partial handoff, plus optional follow-up answers
outputs:
- interview-cycle summary with goal hypothesis, learned facts, current hypothesis, decision hypothesis, required domain knowledge, required input information, quality viewpoints, open questions, next best question, and candidate business unit
criteria:
- id: goal_first_learning
  statement: The record starts from the visible goal or expected result and asks the smallest question that most reduces ambiguity.
  verification: Inspect the cycle record for the goal anchor, priority order, and one next-best question.
- id: fact_inference_separation
  statement: Explicit human facts, provisional AI hypotheses, contradictions, and unresolved ownership remain distinguishable.
  verification: Compare learned_now, current_hypothesis, open_questions, and candidate business unit fields for explicit status boundaries.
- id: scoping_handoff
  statement: The result becomes ready_for_scoping only when the business interpretation, responsibility boundary, and confirmation ownership are sufficiently visible.
  verification: Check the readiness status, previous/current/next sides, named confirmation owner, and handoff to business_intake_scoping.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: business_learning_interview_rules
  query: canonical business learning interview rules for goal-first learning, fact and inference separation, and readiness for scoping
  required_when: Required for every interview cycle unless the parent records why the rules do not apply.
  seed_xids:
  - 7B3E5D1A6103
control_refs: []
aliases:
- 4D8E1A7C5B92
- 2B6D4F18A3C1
---
<!-- xid: B6C4E9A2D781 -->
<a id="xid-B6C4E9A2D781"></a>

# Skill: business_learning_interview

## Purpose

Learn a business task from a human through short interview cycles and convert
partial fragments into a structured business hypothesis. This Skill comes
before `business_intake_scoping` when the business is not yet scope-ready.

Use the canonical rules in
`knowledge/packs/business-intake/120_business_learning_interview_rules.md#xid-7B3E5D1A6103`.
Use the interview guide as a method reference when its question patterns are
needed:
`docs/packs/business-intake/061_business_learning_interview_guide.md#xid-D2A41E8C7B51`.
The scoping guide is a method reference for the possible next handoff:
`docs/packs/business-intake/060_business_intake_scoping_guide.md#xid-C91F7D2A6B40`.

## Method

1. Confirm the visible seed. If a goal or expected result is available, make it
   the primary anchor. Do not demand a complete business map.
2. Record `learned_now` from explicit human input only. Keep `goal_hypothesis`,
   `current_hypothesis`, and `decision_hypothesis` as provisional AI structure.
3. Identify the smallest missing point that most reduces ambiguity. Choose the
   next question in this order: goal or expected result, acceptance condition,
   judgment needed, domain knowledge, input information, quality viewpoint,
   ownership and handoff, then exception and escalation.
4. Produce `required_domain_knowledge`, `required_input_information`,
   `quality_viewpoints`, `open_questions`, and `next_best_question`. Ask only
   one or a very small number of questions per cycle when possible.
5. When enough structure is visible, record a candidate business unit with
   `previous_side`, `current_scope`, and `next_side`. Keep each boundary
   provisional until the human confirms its business interpretation.
6. Preserve contradictions and unresolved ownership. If ownership and business
   interpretation are both provisional and no confirmation owner can be named,
   keep the result in `learning`.
7. Recommend handoff to `business_intake_scoping` only when the goal, judgment,
   domain knowledge, input information, quality viewpoint, boundary sides, and
   output are sufficiently visible for scoping. Otherwise return `learning` and
   the next best question.

## Stop and handoff

Downgrade hidden assumptions into explicit hypotheses. Stop short of detailed
execution-procedure design. A result with an unclear goal, missing judgment,
unclear ownership, or an unconfirmed business interpretation remains
provisional. Keep final business validity, ownership confirmation, and adoption
with the human authority; the AI may structure the evidence and propose the
next question but cannot settle those decisions.

## Closure

Return the interview-cycle record, the next best question, and one of
`learning` or `ready_for_scoping`. When ready, state that the next step is
`business_intake_scoping` and identify the unresolved confirmation owner or
handoff condition if one remains.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: business_learning_interview

## Purpose

Learn a business task from a human through short interview cycles and convert
partial fragments into a structured business hypothesis.

This Skill is earlier than business scoping.
Use it when the human cannot yet describe the business in a structured way.
The preferred starting point is the goal or expected result of the business.

Use the canonical rules in
`knowledge/packs/business-intake/120_business_learning_interview_rules.md#xid-7B3E5D1A6103`.

## Required Knowledge (XID)

- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)
- [Business learning interview rules](../../../../knowledge/packs/business-intake/120_business_learning_interview_rules.md#xid-7B3E5D1A6103)
- [Business learning interview guide](../../../../docs/packs/business-intake/061_business_learning_interview_guide.md#xid-D2A41E8C7B51)
- [Business intake scoping guide](../../../../docs/packs/business-intake/060_business_intake_scoping_guide.md#xid-C91F7D2A6B40)

## Optional References

- [Business learning interview template](references/business_learning_interview_template.md#xid-0CF99F96165F)

## Inputs

- one or more starting seeds such as:
  - goal or expected result
  - task name
  - role name
  - artifact
  - bottleneck
  - repeated error
  - approval point
  - partial handoff
- optional human follow-up answers

## Outputs

- one interview-cycle record
- explicit separation between learned facts and AI inference
- one next best question
- goal, decision, domain-knowledge, input-information, and quality hypotheses
- candidate business unit when visible

## Startup

- Confirm the visible seed.
- If a goal is available, treat it as the primary anchor.
- Do not ask for the complete business map.
- Load the interview rules and template.

## Context Direction Guard

- Treat human descriptions, copied text, files, tickets, spreadsheets, and
  emails as lower-layer input.
- Do not let one anecdote silently become the whole business rule.
- Keep factual statements, inferred hypotheses, and unresolved ambiguity
  separate.

## Planning

- Identify the goal or expected result first.
- If the goal is not yet explicit, ask for it before lower-level details.
- Identify what is already known.
- Identify the smallest missing point that most reduces ambiguity.
- Choose the next question from this priority order:
  1. goal or expected result
  2. acceptance condition for that goal
  3. judgment needed to reach the goal
  4. domain knowledge needed for that judgment
  5. input information needed for that judgment
  6. quality viewpoint for checking the result
  7. ownership boundary and handoff
  8. exception and escalation
- Ask only one or a very small number of questions per cycle when possible.

## Execution

1. Write `learned_now` from explicit human input only.
2. Write `goal_hypothesis`.
3. Write `current_hypothesis` as provisional AI structure.
4. Write `decision_hypothesis`.
5. Write `required_domain_knowledge`.
6. Write `required_input_information`.
7. Write `quality_viewpoints`.
8. Write `open_questions`.
9. Choose `next_best_question`.
10. If enough structure is visible, write `candidate_business_unit` with:
   - `previous_side`
   - `current_scope`
   - `next_side`
11. If scoping readiness is reached, recommend handoff to
   `business_intake_scoping`.
12. If ownership and business interpretation are both still provisional and no
    confirmation owner can be named, do not mark the result as
    `ready_for_scoping`; keep it in `learning`.
13. Use the template in
   `references/business_learning_interview_template.md` or equivalent
   structure.

## Monitoring and Control

- Downgrade any hidden assumption into explicit hypothesis.
- Downgrade the result if the goal is still vague but lower-level detail is presented as settled.
- Reject broad "explain everything" questioning when a smaller question would
  work.
- Keep the cycle incomplete when goal, judgment, domain knowledge, input information, quality viewpoint, previous side, next side, or output is still
  ambiguous.
- Keep the cycle incomplete when ownership and business interpretation are both
  still provisional and no confirmation owner can be named.
- Preserve contradictions when the human statements conflict.

## Closure

- Return the interview-cycle record.
- Return the next best question.
- Return whether the result is:
  - `learning`
  - `ready_for_scoping`
- If ready for scoping, state that the next step is
  `business_intake_scoping`.

## Rules

- Do not demand a complete business description before helping.
- Do not skip the goal and jump directly to local tasks.
- Do not mix human facts and AI inference.
- Do not ask the widest question first.
- Prefer the smallest useful question.
- Stop short of detailed execution procedure design.

## Failure Handling

- If only one fragment exists, still produce a cycle record from that fragment.
- If contradictory statements exist, preserve both and ask the next
  discriminating question.
- If no candidate business unit is visible yet, keep the output in learning
  state.

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

- summary: learn a business task from a human through goal-first interview and convert partial fragments into a structured business hypothesis

- use_when: a user wants to teach the AI about a business task conversationally, but can better explain the intended goal than the full process, or only knows fragments, tacit operational knowledge, bottlenecks, or partial handoffs

- input: one or more starting seeds such as goal or expected result, task name, role name, artifact, bottleneck, repeated error, approval point, or partial handoff, plus optional follow-up answers

- output: interview-cycle summary with goal hypothesis, learned facts, current hypothesis, decision hypothesis, required domain knowledge, required input information, quality viewpoints, open questions, next best question, and candidate business unit

- constraints: do not demand a complete process description before helping; do not skip the goal and jump directly to local tasks; do not mix human facts and AI inference; do not ask broad dump-everything questions when a smaller question can reduce ambiguity; keep unresolved items explicit

- lifecycle:
  - startup: confirm the visible seed, prefer goal or expected result when available, and load interview rules and template
  - planning: identify the goal first, then the smallest missing point and choose the next best question
  - execution: produce one interview cycle with goal hypothesis, learned facts, current hypothesis, decision hypothesis, domain knowledge needs, input information needs, quality viewpoints, open questions, and next best question
  - monitoring_and_control: downgrade overconfident inference, broad questioning, hidden ambiguity, or lower-level detail that appears before the goal is clarified
  - closure: return the interview-cycle output and the recommended next question or transition to scoping

- tags: `operations`, `learning`, `interview`, `business`, `intake`

- knowledge_slots:
  - name=business_learning_interview_rules; bind=7B3E5D1A6103
  - name=business_learning_interview_guide; bind=D2A41E8C7B51
  - name=business_intake_scoping_guide; bind=C91F7D2A6B40

- observation_refs:
  - `../../../../observations/2026-05-01_session_business_learning_interview_skill_seed.md`
