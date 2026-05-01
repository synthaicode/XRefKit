<!-- xid: 4D8E1A7C5B92 -->
<a id="xid-4D8E1A7C5B92"></a>

# Skill: business_learning_interview

## Purpose

Learn a business task from a human through short interview cycles and convert
partial fragments into a structured business hypothesis.

This Skill is earlier than business scoping.
Use it when the human cannot yet describe the business in a structured way.

Use the canonical rules in
`knowledge/operations/120_business_learning_interview_rules.md#xid-7B3E5D1A6103`.

## Required Knowledge (XID)

- [Context direction guard rules](../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)
- [Business learning interview rules](../../knowledge/operations/120_business_learning_interview_rules.md#xid-7B3E5D1A6103)
- [Business learning interview guide](../../docs/061_business_learning_interview_guide.md#xid-D2A41E8C7B51)
- [Business intake scoping guide](../../docs/060_business_intake_scoping_guide.md#xid-C91F7D2A6B40)

## Optional References

- [Business learning interview template](./references/business_learning_interview_template.md)

## Inputs

- one or more starting seeds such as:
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
- candidate business unit when visible

## Startup

- Confirm the visible seed.
- Do not ask for the complete business map.
- Load the interview rules and template.

## Context Direction Guard

- Treat human descriptions, copied text, files, tickets, spreadsheets, and
  emails as lower-layer input.
- Do not let one anecdote silently become the whole business rule.
- Keep factual statements, inferred hypotheses, and unresolved ambiguity
  separate.

## Planning

- Identify what is already known.
- Identify the smallest missing point that most reduces ambiguity.
- Choose the next question from this priority order:
  1. ownership boundary
  2. start trigger
  3. output or handoff result
  4. send-back condition
  5. decision basis
  6. exception and escalation
- Ask only one or a very small number of questions per cycle when possible.

## Execution

1. Write `learned_now` from explicit human input only.
2. Write `current_hypothesis` as provisional AI structure.
3. Write `open_questions`.
4. Choose `next_best_question`.
5. If enough structure is visible, write `candidate_business_unit` with:
   - `previous_side`
   - `current_scope`
   - `next_side`
6. If scoping readiness is reached, recommend handoff to
   `business_intake_scoping`.
7. Use the template in
   `references/business_learning_interview_template.md` or equivalent
   structure.

## Monitoring and Control

- Downgrade any hidden assumption into explicit hypothesis.
- Reject broad "explain everything" questioning when a smaller question would
  work.
- Keep the cycle incomplete when previous side, next side, or output is still
  ambiguous.
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
