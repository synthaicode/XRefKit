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

1. start from the business goal or expected result
2. trace backward from that goal
3. identify the judgment needed to reach the goal
4. identify the domain knowledge and inputs needed for that judgment
5. identify the quality viewpoints that define acceptable output
6. ask the next best question
7. update the structure

## Valid Starting Seeds

The interview may start from any one of the following:

- one goal or expected result
- one task name
- one complaint or bottleneck
- one role name
- one file, form, or spreadsheet
- one approval point
- one repeated error
- one known upstream or downstream side

## Interview Output Model

Each cycle should produce:

- goal hypothesis
- what is known now
- current business hypothesis
- decision hypothesis
- required domain knowledge hypothesis
- required input-information hypothesis
- quality viewpoint hypothesis
- unresolved points
- next confirmation question
- candidate scoped business unit if one is already visible

This keeps the learning process inspectable.

## Question Strategy

Ask the smallest question that most reduces ambiguity.

Prefer questions in this order:

1. goal or expected result
2. acceptance condition for that goal
3. judgment needed to produce that result
4. domain knowledge needed for that judgment
5. input information needed for that judgment
6. quality viewpoint for checking the result
7. ownership boundary and handoff
8. exception and escalation

Do not ask broad "please explain the whole process" questions unless the user
explicitly wants that.

## Good Question Examples

- What is the result you want to obtain at the end?
- How do you know that result is good enough?
- What do you have to judge before you can produce that result?
- What knowledge or rules do you refer to for that judgment?
- What information has to be present before you can judge?
- What quality points matter when you check the result?

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

- goal
- at least one key judgment
- at least one required domain-knowledge area
- at least one required input-information area
- at least one quality viewpoint
- previous side
- current responsibility
- next side
- output

the result is ready to hand off to business intake scoping.

## Related

- [Business intake scoping guide](060_business_intake_scoping_guide.md#xid-C91F7D2A6B40)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
