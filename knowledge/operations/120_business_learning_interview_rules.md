<!-- xid: 7B3E5D1A6103 -->
<a id="xid-7B3E5D1A6103"></a>

# Business Learning Interview Rules

This fragment defines how AI should learn a business task from a human through
iterative questioning.

## Purpose

Turn scattered human explanations into a structured business hypothesis without
requiring the human to prepare a complete process description in advance.

## Core Rules

- accept partial information as valid starting input
- separate observed facts from AI inference
- ask the smallest next question that reduces ambiguity
- preserve unresolved items instead of forcing closure
- prefer short interview cycles over one large information dump

## Required Cycle Output

Each interview cycle must produce:

- `learned_now`
- `current_hypothesis`
- `open_questions`
- `next_best_question`
- `candidate_business_unit`

`candidate_business_unit` may stay provisional.

## Question Priority

Ask in this order unless a later item is the immediate blocker:

1. ownership boundary
2. start trigger
3. output or handoff result
4. send-back condition
5. decision basis
6. exception and escalation

## Valid Starting Seeds

The interview may start from:

- one task name
- one role
- one artifact
- one bottleneck
- one approval point
- one repeated error
- one partial handoff

If only one seed exists, do not escalate immediately to a request for the whole
business map.

## Inference Rule

The AI may infer a provisional hypothesis only when:

- the inference is labeled as provisional
- the basis is visible
- the missing confirmation point is explicit

Do not promote a provisional hypothesis to fact without explicit confirmation.

## Completion Boundary

The interview result is ready to hand off to scoping when:

- previous side is visible
- current responsibility is visible
- next side is visible
- at least one start trigger is visible
- at least one output is visible
- at least one judgment point is visible

If these are not all visible, keep the output as interview-stage learning.

## Failure Conditions

Treat the cycle as weak when:

- the AI asks a broad question instead of the smallest next question
- inference and human facts are mixed
- unresolved items disappear without confirmation
- the AI demands a complete process map before continuing

## Sources

- source_type: repo_doc
- source_path: ../../docs/061_business_learning_interview_guide.md
- source_locator: whole_page
- extracted_at: 2026-05-01
