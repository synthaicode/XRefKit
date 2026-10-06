---
schema_version: 1
skill_id: business_learning_interview
xid: B6C4E9A2D781
aliases:
  - 4D8E1A7C5B92
  - 2B6D4F18A3C1
summary: learn a business task through goal-first interview cycles and turn partial fragments into a structured provisional hypothesis
applies_when:
  - the person can describe a goal, task, role, artifact, bottleneck, approval point, or partial handoff but cannot yet describe the full business process
exclusions:
  - detailed execution procedure design before the business boundary is explicit
  - treating one anecdote or an AI inference as an established business rule
inputs:
  - one or more starting seeds such as a goal, expected result, task, role, artifact, bottleneck, repeated error, approval point, or partial handoff
  - optional human follow-up answers
outputs:
  - one interview-cycle record with human facts separated from AI inference
  - goal, decision, domain-knowledge, input-information, and quality hypotheses
  - one next-best question and a candidate business unit when visible
  - learning or ready_for_scoping status with any handoff recommendation
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
knowledge_needs:
  - id: business_learning_interview_rules
    query: canonical business learning interview rules for goal-first learning, fact and inference separation, and readiness for scoping
    required_when: Required for every interview cycle unless the parent records why the rules do not apply.
    seed_xids:
      - 7B3E5D1A6103
control_refs: []
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
