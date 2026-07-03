<!-- xid: 8E17D4C2B6A5 -->
<a id="xid-8E17D4C2B6A5"></a>

# Skill: goal_mode

## Purpose

Continue toward one goal across Codex quota exhaustion by preserving restart-ready state, waiting for usage recovery, and resuming with the same boundary and next action.

## Required Knowledge (XID)

- [Codex MCP job inbox design](../../../docs/designs/050_codex_mcp_job_inbox_design.md#xid-77BCEAA247E3)
- [Skill operating contract](../../../docs/core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Codex goal mode usage guide](../../../docs/guides/069_codex_goal_mode_usage_guide.md#xid-3E7B4C11A8D2)
- [Codex goal mode auto resume design](../../../docs/designs/070_codex_goal_mode_auto_resume_design.md#xid-6F4D2A18C9E7)

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
