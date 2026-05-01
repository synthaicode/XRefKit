<!-- xid: C91F7D2A6B40 -->
<a id="xid-C91F7D2A6B40"></a>

# Business Intake Scoping Guide

This page defines how to scope a business task before turning it into
AI-executable work in this repository.

The goal is not to write a complete procedure first.
The goal is to define a business unit that has visible boundaries, handoff, and
judgment points.

This guide does **not** assume that a human already knows the full material set
or the full business structure in advance.
The starting point may be partial:

- a task name
- a short complaint such as "this review always gets stuck"
- one file, one form, one email, or one spreadsheet
- one known owner or one known downstream side

## Core Principle

Do not start from a person's detailed work steps.

Start from the smallest business unit where the following are visible:

- what arrives from the previous side
- what must be judged
- what is returned to the next side
- where the work stops or is sent back

If those boundaries are missing, the result becomes a personal work memo rather
than a reusable business unit.

## Discovery-First Rule

Business intake should work even when the user only knows fragments.

The discovery order is:

1. find one repeated work situation
2. find one current owner or one current handoff
3. infer the immediate previous side and next side
4. identify what is still unknown
5. only then write the first scoped business unit

The human should not be required to prepare a complete business map before the
AI can help.

## Minimum Starting Seeds

The intake may start from any one of these:

- business task name
- current owner or team name
- one input artifact
- one output artifact
- one recurring trouble point
- one known rule or approval point

If only one seed exists, start from that seed and build outward.

## Where To Start

Start from one level above the current person's scope.

For example:

- overall flow: `request intake -> content check -> approval -> reflection`
- current responsibility: `content check`

Do not define `content check` only as local clicks and edits.
First define:

- what starts the check
- what is checked
- what result is returned
- what goes back for rework

If even that upper unit is unclear, start from one known recurring action and
ask:

- who gives this to you?
- what do you return?
- when do you send it back?
- who waits for your result?

## Three Levels

- business level
  - the cross-role progression where ownership may change
- responsibility level
  - the unit one role is responsible for
- work-step level
  - concrete operations such as screen checks, table updates, and message drafting

The normal order is:

1. business level
2. responsibility level
3. work-step level

## First 30-Minute Output

The first scoping pass should produce only these seven items:

1. start condition
2. inputs
3. judgment points
4. outputs
5. send-back conditions
6. reference rules
7. unresolved items

Do not wait for a perfect procedure before writing these items.

Before those seven items are complete, it is acceptable to first produce:

- `known_now`
- `assumed_boundary`
- `missing_for_confirmation`

Those discovery notes are valid intermediate output.

## Example

For `content check` in a request process:

- start condition
  - intake side sends a request for checking
- inputs
  - request form, attachments, target list
- judgment points
  - missing fields, rule fit, exception need
- outputs
  - check result, send-back reason
- send-back conditions
  - missing attachment, invalid field, unclear business rule
- reference rules
  - request criteria, exception rules
- unresolved items
  - who confirms when the rule is still ambiguous

## Next Operational Step

After the first pass:

1. pick one repeated business task
2. if the flow is unclear, start from one known owner, artifact, or trouble point
3. write `previous side / my scope / next side` as a first hypothesis
4. write the seven items only for `my scope`
5. run one cycle and observe where handoff or judgment fails
6. revise and only then expand to other tasks

## Related

- [Importing existing documents (human view)](003_import_for_humans.md#xid-0CF07930F2FA)
- [End-to-end flow (human view)](004_overall_flow_for_humans.md#xid-E01E6695A30A)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
