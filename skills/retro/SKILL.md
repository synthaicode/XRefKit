<!-- xid: C17B52E8F4A3 -->
<a id="xid-C17B52E8F4A3"></a>

# Skill: retro

## Purpose

Review current session evidence and determine what should remain in `work/` versus what should be promoted into canonical repository assets.

## Required Knowledge (XID)

- [Working area policy](../../docs/014_working_area_policy.md#xid-111D282CA0EA)
- [Shared memory operations](../../docs/015_shared_memory_operations.md#xid-4A423E72D2ED)
- [System quality feedback register](../../docs/044_system_quality_feedback_register.md#xid-8B31F02A4013)

## Inputs

- current task goal
- relevant `work/sessions/` and `work/retrospectives/` files
- changed files from the current task
- optional conversation history
- optional expected target area supplied by the user

## Outputs

- promotion candidate report
- target location per candidate:
  - `docs/`
  - `knowledge/`
  - `skills/` or `skills_private/`
  - `agent/`
  - `stay_in_work`
- evidence reference for each candidate
- duplication or already-promoted check result
- optional update plan for approved promotions

## Startup

- Confirm that the current task has a `work/sessions/` entry.
- Identify the session logs and retrospectives relevant to the current task.
- Identify the changed files and the surrounding canonical area.
- Load the working area and shared memory rules before classifying candidates.

## Planning

- Extract from `work/` only the items that look reusable beyond the current session:
  - stable operational rules
  - stable domain facts
  - repeated procedures
  - recurring structural quality issues
  - missing role or routing definitions
- Define the target class for each candidate:
  - `docs/` for stable operational or design policy
  - `knowledge/` for stable domain facts or review knowledge
  - `skills/` or `skills_private/` for reusable procedures
  - `agent/` for stable agent contract, routing, or role definitions
  - `stay_in_work` for transient logs, unresolved items, and single-session notes

## Execution

- Read the relevant `work/` files.
- For each candidate item, check:
  - whether it is reused or likely to be reused
  - whether the decision or fact is stable
  - whether later sessions should reload it
  - whether equivalent canonical content already exists
- Classify each candidate as one of:
  - `promote_to_docs`
  - `promote_to_knowledge`
  - `promote_to_skill`
  - `promote_to_agent`
  - `stay_in_work`
  - `already_promoted`
- When the item is a structural quality issue that remains relevant beyond one session, prepare a summary row candidate for the system quality feedback register.
- When the item is a new reusable procedure, prefer a narrowly scoped skill over a broad generic skill.

## Monitoring and Control

- Downgrade any weakly supported or still-changing item to `stay_in_work`.
- Mark any item already reflected in canonical files as `already_promoted`.
- Do not copy large factual blocks into a skill; send facts to `knowledge/`.
- Do not create a canonical update when the item is only a local execution detail.

## Closure

- Produce a promotion report for the current task.
- For each promoted or proposed item, include:
  - item name
  - target location
  - candidate target file
  - reason
  - evidence path
  - status
- If the user approves implementation:
  - update the target canonical files
  - run `python -m fm xref init` when new managed files are added
  - run `python -m fm xref fix`
  - keep a short pointer in the `work/` record showing the moved-to path and date

## Rules

- Never treat `work/` as canonical source of truth.
- Never promote a single-session note without checking whether it has become stable.
- Never duplicate existing canonical content without confirming the gap first.
- Prefer the smallest canonical destination that preserves reuse.
- Keep the promotion decision evidence-backed and path-specific.
