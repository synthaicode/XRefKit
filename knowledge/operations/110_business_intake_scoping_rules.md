<!-- xid: 7B3E5D1A6102 -->
<a id="xid-7B3E5D1A6102"></a>

# Business Intake Scoping Rules

This fragment defines the operational rules an AI should follow when scoping a
business task for repository use.

## Purpose

Scope the task into a reusable business unit before trying to write a complete
execution procedure.

## Core Rules

- do not start from local screen operations or a person's private habits
- start from a boundary-visible business unit
- keep previous side, current responsibility, and next side explicit
- keep uncertainty explicit instead of silently completing missing business rules
- do not treat unresolved business interpretation as completed knowledge

## Discovery-First Intake

Do not require the user to provide the full business map in advance.

The Skill may start from partial seeds such as:

- one task name
- one current owner
- one input or output artifact
- one approval point
- one repeated failure or bottleneck

When only partial seeds exist, expand outward in this order:

1. current visible point
2. immediate previous side
3. immediate next side
4. minimum business boundary
5. unresolved items

Produce a partial but usable scoping result instead of blocking on missing
global structure.

## Boundary Test

A candidate business unit is acceptable only when all of the following are
visible:

- start trigger
- incoming inputs
- judgment point
- outgoing result
- send-back or stop condition
- next owner or next side

If any of these are missing, downgrade the result to partial scoping and mark
the missing point as unresolved.

Partial scoping is a valid intermediate result.
Do not reject the intake only because the whole business architecture is not yet
known.

## Three Scoping Levels

- business level
  - cross-role progression such as `intake -> check -> approval -> reflection`
- responsibility level
  - one role's accountable unit inside the business flow
- work-step level
  - concrete local actions such as screen checks, updates, or message drafting

Required order:

1. business level
2. responsibility level
3. work-step level

Do not begin from level 3 unless levels 1 and 2 are already explicit.

If levels 1 and 2 are not explicit, the Skill must first build a provisional
level-1 and level-2 hypothesis from the available seed.

## Required First-Pass Fields

The first pass must produce these seven fields:

1. `start_condition`
2. `inputs`
3. `judgment_points`
4. `outputs`
5. `send_back_conditions`
6. `reference_rules`
7. `unresolved_items`

If the first pass is still incomplete, prepend a discovery block:

- `known_now`
- `assumed_boundary`
- `missing_for_confirmation`

## Example Pattern

Example business flow:

- request intake
- content check
- approval
- reflection

Example scoped responsibility: `content check`

- `start_condition`
  - intake side sends the request for checking
- `inputs`
  - request form, attachments, target list
- `judgment_points`
  - missing fields, rule fit, exception need
- `outputs`
  - check result, send-back reason
- `send_back_conditions`
  - missing attachment, invalid field, unclear business rule
- `reference_rules`
  - request criteria, exception rules
- `unresolved_items`
  - confirmation owner when the rule is still ambiguous

## Failure Conditions

Treat the scoping result as incomplete when:

- it describes only local work steps
- previous side or next side is missing
- output is vague such as `process it` or `handle it`
- send-back conditions are absent
- unresolved business rules are hidden as normal completion

Do not treat incompleteness itself as failure if the result still makes the
missing boundary explicit.

## Sources

- source_type: repo_doc
- source_path: ../../docs/060_business_intake_scoping_guide.md
- source_locator: whole_page
- extracted_at: 2026-05-01
