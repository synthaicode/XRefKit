<!-- xid: D2A41E8C7B51 -->
<a id="xid-D2A41E8C7B51"></a>

# Business Learning Interview Guide

This page defines how AI should learn a business task from a human through
iterative interview rather than requiring a complete process description in
advance.

## Purpose

Use conversation to discover business structure when the human only knows
fragments, local pain points, or partial responsibility boundaries.

The goal is not to ask the human to explain everything at once.
The goal is to help the human externalize tacit operational knowledge while the
AI turns it into structured hypotheses.

## Core Principle

The AI should not ask for the full business map as a startup condition.

Instead, the AI should:

1. accept partial fragments
2. build a provisional business hypothesis
3. identify the smallest missing point that blocks confidence
4. ask the next best question
5. update the structure

## Valid Starting Seeds

The interview may start from any one of the following:

- one task name
- one complaint or bottleneck
- one role name
- one file, form, or spreadsheet
- one approval point
- one repeated error
- one known upstream or downstream side

## Interview Output Model

Each cycle should produce:

- what is known now
- current business hypothesis
- unresolved points
- next confirmation question
- candidate scoped business unit if one is already visible

This keeps the learning process inspectable.

## Question Strategy

Ask the smallest question that most reduces ambiguity.

Prefer questions in this order:

1. ownership boundary
2. start trigger
3. output or return point
4. send-back condition
5. decision basis
6. exception and escalation

Do not ask broad "please explain the whole process" questions unless the user
explicitly wants that.

## Good Question Examples

- Who gives this work to you?
- What do you return when you finish?
- When do you send it back without finishing?
- Who waits for your result next?
- What makes the case easy versus hard?
- When you cannot decide, who confirms it?

## Bad Question Examples

- Explain the whole business from start to finish.
- List every rule and every actor first.
- Give the complete organizational structure before we start.

## Learning Boundary

The AI may form hypotheses, but it must not silently convert hypotheses into
facts.

Every cycle should keep these separate:

- observed from the human
- inferred by the AI
- still unresolved

## Transition To Scoping

Once the interview reveals:

- previous side
- current responsibility
- next side
- start trigger
- output
- key judgment point

the result is ready to hand off to business intake scoping.

## Related

- [Business intake scoping guide](060_business_intake_scoping_guide.md#xid-C91F7D2A6B40)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
