---
schema_version: 1
skill_id: goal_mode
xid: E6A2C9F4B710
summary: preserve task state and resume the same goal after verified Codex usage recovery
applies_when:
- a user wants Codex work to continue toward the same goal even when usage remaining can reach `0%`, and the repository must preserve a restart-ready continuation packet instead of silently stopping
exclusions:
- Human authority, scope, and final decisions remain explicit
- Missing evidence or ambiguous objectives remain unknown rather than being guessed
inputs:
- current goal, current task state, changed artifacts or target paths, unresolved items, and actual quota-state evidence such as current remaining usage and the next reset indication shown by Codex
outputs:
- continuation packet for the current goal, explicit wait condition, resume checklist, updated artifacts or handoff pointers, and unresolved items that still block safe continuation
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
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs: []
control_refs: []
aliases:
- 8E17D4C2B6A5
- 5C2D7A91E4F3
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

## Additional bound references retained at repository cutover

These references were explicitly bound by the prior repository Skill. Apply them to the relevant method work; resolve their XIDs on demand.

- [Codex MCP Job Inbox Design](../../../docs/designs/050_codex_mcp_job_inbox_design.md#xid-77BCEAA247E3)
- [Codex Goal Mode Usage Guide](../../../docs/guides/069_codex_goal_mode_usage_guide.md#xid-3E7B4C11A8D2)
- [Codex Goal Mode Auto Resume Design](../../../docs/designs/070_codex_goal_mode_auto_resume_design.md#xid-6F4D2A18C9E7)

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

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

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: preserve task state, wait for Codex usage recovery, and resume the same goal after the next 5-hour or weekly reset

- use_when: a user wants Codex work to continue toward the same goal even when usage remaining can reach `0%`, and the repository must preserve a restart-ready continuation packet instead of silently stopping

- input: current goal, current task state, changed artifacts or target paths, unresolved items, and actual quota-state evidence such as current remaining usage and the next reset indication shown by Codex

- output: continuation packet for the current goal, explicit wait condition, resume checklist, updated artifacts or handoff pointers, and unresolved items that still block safe continuation

- constraints: do not invent quota-reset times; do not claim background wake-up or automatic resume unless a real hook or queue mechanism exists; do not lose unresolved items or next-step ownership during the wait; do not resume after a long wait without checking for drift in scope, branch state, or upstream instructions

- lifecycle:
  - startup: confirm the current goal, active boundary, quota-state evidence, and whether the run is still executable now or already needs wait preparation
  - planning: define the minimum continuation packet, resume trigger, drift-check points, and first action after recovery
  - execution: continue work while quota remains, stop new substantive work when usage reaches `0%`, record the continuation packet, wait for the next 5-hour or weekly recovery, and resume from the recorded packet
  - monitoring_and_control: keep quota-state evidence explicit, treat missing reset information as `unknown`, and re-check boundary drift before resume
  - closure: close only after the goal is completed or the continuation packet and handoff state are explicit enough for the next recovery window

- tags: `operations`, `continuation`, `quota`, `codex`, `control`

- knowledge_slots:
  - name=codex_mcp_job_inbox_design; bind=77BCEAA247E3
  - name=skill_operating_contract; bind=B7A2C94F0E61
  - name=codex_goal_mode_usage_guide; bind=3E7B4C11A8D2
  - name=codex_goal_mode_auto_resume_design; bind=6F4D2A18C9E7

- observation_refs:
  - `../../../observations/2026-05-24_session_goal_mode_skill_seed.md`
