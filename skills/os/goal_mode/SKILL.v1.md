---
schema_version: 1
skill_id: goal_mode
xid: E6A2C9F4B710
aliases:
  - 8E17D4C2B6A5
  - 5C2D7A91E4F3
summary: preserve task state and resume the same goal after verified Codex usage recovery
applies_when:
  - a user wants the same goal to continue across verified Codex usage exhaustion using a restart-ready continuation packet
exclusions:
  - Human authority, scope, and final decisions remain explicit
  - Missing evidence or ambiguous objectives remain unknown rather than being guessed
inputs:
  - current goal, task state, changed artifacts or target paths, unresolved items, and current usage/reset evidence
outputs:
  - continuation packet, explicit wait condition, resume checklist, artifact or handoff pointers, unresolved blockers
criteria:
  - id: boundary_preservation
    statement: The Skill preserves its human decision boundary and keeps missing evidence or ambiguity explicit
    verification: Inspect the method output, unknowns, and handoff for unsupported closure
  - id: evidence_traceability
    statement: Non-trivial conclusions retain source or state evidence
    verification: Check the result for source pointers and recorded evidence
  - id: output_closure
    statement: The declared artifact and next action or handoff are returned
    verification: Check output paths, unresolved items, and ownership before closure
knowledge_needs: []
control_refs: []
---
<!-- xid: E6A2C9F4B710 -->
<a id="xid-E6A2C9F4B710"></a>

# Skill: goal_mode

## Purpose

Continue toward one goal across Codex quota exhaustion by preserving restart-ready state, waiting for usage recovery, and resuming with the same boundary and next action.

## Inputs

- current goal or work request
- current task state:
  - completed work
  - in-progress work
  - current artifacts
  - exact next action
- unresolved items:
  - unknowns
  - risks
  - non-trivial judgments
- quota-state evidence from Codex:
  - current usage remaining
  - next 5-hour reset indication when shown
  - next weekly reset indication when shown
- allowed continuation boundary

## Outputs

- continuation packet for the same goal:
  - goal summary
  - completed work summary
  - artifact paths
  - unresolved items
  - exact next first action
- explicit wait condition:
  - `wait_for_next_5h_reset`
  - `wait_for_weekly_reset`
  - `unknown`
- resume checklist
- explicit handoff or reopen pointer when the same agent cannot stay active

## Startup

- Confirm the goal that must continue after quota recovery.
- Confirm the current execution boundary and stop conditions.
- Confirm the latest quota-state evidence from Codex.
- If quota-state evidence is missing, record that as `unknown` instead of guessing.
- Confirm whether the current session can still execute now or must switch to wait preparation.

## Planning

- Define the smallest continuation packet that allows safe resume without rereading the whole task.
- Define the expected resume trigger:
  - next 5-hour reset if Codex shows that as the next recovery point
  - weekly reset if the 5-hour window is unavailable or the weekly reset is the next shown recovery point
  - `unknown` if neither is shown
- Define drift-check points for resume:
  - new user instructions
  - branch or file changes
  - upstream artifact or requirement changes
  - unresolved approval or boundary issues
- Define the first concrete action to take immediately after recovery.

## Execution

### 1. Continue While Usage Remains

- Continue normal work while usage remains above `0%`.
- Keep concrete work items, artifacts, and concerns current so the wait boundary is not reconstructive.

### 2. Switch To Wait Preparation At `0%`

- When usage reaches `0%`, stop new substantive work.
- Record a continuation packet that includes:
  - the goal
  - what is already done
  - what remains
  - exact artifact paths
  - unresolved items
  - exact first action after recovery
- Record which reset signal the continuation depends on:
  - next 5-hour reset
  - weekly reset
  - `unknown`

### 3. Wait

- Wait until Codex usage becomes available again.
- Do not claim background wake-up or automatic restart unless a real scheduler, hook, or job queue exists.
- If the wait crosses a handoff boundary, preserve the continuation packet in the run log and handoff artifacts.

### 4. Resume

- Re-open the goal from the continuation packet after usage recovery.
- Re-check drift before resuming substantive work.
- Start from the recorded first action instead of recomputing the task from scratch unless drift invalidates the packet.

## Monitoring and Control

- Keep quota-state evidence factual and source-based.
- Treat missing or ambiguous reset timing as `unknown`.
- If waiting is no longer enough because scope, approval, or boundary changed, stop and escalate instead of blindly resuming.
- If the session cannot remain active, preserve enough state for a later startup to continue safely.

## Closure

- Close only when one of the following is true:
  - the goal is completed and checked
  - a restart-ready continuation packet is recorded with explicit wait condition and next-step ownership
- Return:
  - current goal state
  - wait condition
  - resume checklist
  - unresolved items
  - artifact paths

## Rules

- Do not guess reset times.
- Do not let usage exhaustion erase the next action.
- Do not hide unresolved items during the wait transition.
- Do not resume after a long wait without a drift check.
- Do not describe the mode as fully automatic unless real automation was implemented and verified.
