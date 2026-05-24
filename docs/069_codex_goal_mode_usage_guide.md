<!-- xid: 3E7B4C11A8D2 -->
<a id="xid-3E7B4C11A8D2"></a>

# Codex Goal Mode Usage Guide

This page explains how to use repository-native `goal_mode` in day-to-day Codex work.

This page is a practical usage guide.
It is not a full operating model and not a system integration design.
For the boundary among operating models, usage guides, and design pages, see [Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583).

## Purpose

Use `goal_mode` when the main requirement is to keep the same work goal alive across Codex usage exhaustion.

In this repository, `goal_mode` means:

1. continue normal work while usage remains available
2. when usage remaining reaches `0%`, stop new substantive work
3. wait until the next 5-hour or weekly usage recovery point
4. resume the same goal from an explicit continuation packet instead of starting over

## When To Use Goal Mode

Use `goal_mode` in the following situations:

1. the task is long enough that usage exhaustion is realistic
2. losing current state would create avoidable reconstruction work
3. the user wants one goal pursued across multiple Codex quota windows
4. the work must preserve explicit next-step ownership, unresolved items, and artifact paths during the wait

Do not use `goal_mode` as a substitute for normal closure when the current task can simply finish inside the current window.

## What To Prepare

Prepare at least:

1. current goal:
   - the exact task that should continue after recovery
2. current state:
   - completed work
   - remaining work
   - artifact paths
   - exact next first action
3. unresolved items:
   - unknowns
   - risks
   - non-trivial judgments
4. quota-state evidence from Codex:
   - current usage remaining
   - next 5-hour reset indication when shown
   - next weekly reset indication when shown
5. continuation boundary:
   - what is still allowed to continue after recovery
   - which approvals or stop conditions would block resume

If the quota-state evidence is missing, keep that gap explicit as `unknown`.

## How To Request Goal Mode

Recommended request format:

```text
Goal:
- finish the current task without losing state across quota exhaustion

Current state:
- completed work: ...
- remaining work: ...
- artifact paths: ...
- next first action: ...

Quota evidence:
- usage remaining: ...
- next 5-hour reset shown by Codex: ...
- weekly reset shown by Codex: ...

Constraints:
- resume only within the same scope
- preserve unresolved items explicitly
```

## What Goal Mode Returns

`goal_mode` should always leave:

1. a continuation packet
2. an explicit wait condition
3. a resume checklist
4. unresolved items
5. current artifact paths

The continuation packet should be short but restart-ready.
It should let the next recovery window start from one concrete action instead of a full rediscovery pass.

## Wait And Resume Rule

The wait rule is:

1. keep working while usage remains above `0%`
2. when usage reaches `0%`, stop new substantive work
3. wait for the next usage recovery point shown by Codex
4. resume from the continuation packet after recovery

The preferred recovery interpretation is:

1. use the next 5-hour reset when that is the next visible recovery point
2. use the weekly reset when the weekly window is the next visible recovery point
3. mark the reset condition `unknown` when Codex does not show enough evidence

Do not guess reset times.

## Current Repository Boundary

The current repository implementation gives a reusable continuation procedure, not a proven background auto-resume mechanism.

That means:

1. state preservation is explicit
2. wait condition is explicit
3. resume logic is explicit
4. automatic wake-up, re-entry, or queue-triggered restart still requires a separate implemented mechanism

If future automatic resume is added, the preferred shape is:

1. external quota recovery is observed
2. repository state decides which goal may resume
3. only the session that acquires the goal lease may continue

This avoids making a central external scheduler the hidden source of resume truth.

For the target full-auto design, see [Codex goal mode auto resume design](070_codex_goal_mode_auto_resume_design.md#xid-6F4D2A18C9E7).

## Related

- [OR Team usage guide](049_or_team_usage_guide.md#xid-4E2F91A6B8C1)
- [Codex MCP job inbox design](050_codex_mcp_job_inbox_design.md#xid-77BCEAA247E3)
- [Codex goal mode auto resume design](070_codex_goal_mode_auto_resume_design.md#xid-6F4D2A18C9E7)
- [Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61)
