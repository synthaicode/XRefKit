<!-- xid: 6F4D2A18C9E7 -->
<a id="xid-6F4D2A18C9E7"></a>

# Codex Goal Mode Auto Resume Design

This page is a design document for fully automatic `goal_mode` resume.

It is not a usage guide.
It is not a team operating model.

## Purpose

This page defines how to extend repository-native `goal_mode` from explicit state preservation into fully automatic re-entry after external AI execution limits recover.

The design goal is not merely to save a note and ask the human to reissue the same request later.

The design goal is to:

1. persist a restart-ready continuation packet in XRefKit
2. keep restart arbitration inside repository-visible state instead of a hidden central scheduler
3. detect the next executable recovery window
4. re-enter the same goal automatically
5. preserve claim control, boundary control, and auditability across the wait

## Routing Position

This design must remain consistent with the repository's semantic-routing-first model.

That means:

1. the human or upstream agent expresses an intent such as:
   - continue this goal across quota exhaustion
   - preserve restart-ready state across session loss
   - keep working across time-limit, weekly-limit, or context-loss boundaries
2. semantic routing selects `goal_mode` from that intent
3. only after routing does the runtime envelope open and load the detailed continuation machinery

`goal_mode` must therefore be treated as an intent-selected Skill, not as a command-first feature.

Direct runtime commands, hook wiring, lease operations, or watcher events are execution details under the selected Skill boundary.

## Intent Shape

The intent that should route to `goal_mode` is not:

- "run this exact command"
- "open this exact meta file"
- "execute this specific hook"

The intent that should route to `goal_mode` is:

- keep one goal alive across execution-window limits
- preserve safe continuation across context compression or session discontinuity
- resume without reconstructing the whole task from memory
- continue under the same boundary after a later recovery window

This keeps the user-facing routing story aligned with:

- [Startup xref routing policy](../core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A)

## Problem Statement

`goal_mode` already preserves:

1. goal
2. current state
3. unresolved items
4. next first action
5. artifact paths

However, that alone does not create fully automatic continuation.

Without a resume-arbitration mechanism:

- no component waits for the reset window
- no component decides which session may resume
- no component reopens the goal after session loss
- no component ensures the same continuation packet is consumed exactly once

At the same time, a purely external deterministic controller causes problems when multiple goals or sessions coexist:

- central queue ordering becomes the hidden source of truth
- duplicate or conflicting resume attempts must be prevented outside the repository
- provider quota state and work-state arbitration become coupled
- simultaneous resume requests create scheduler contention that is hard to inspect from XRefKit alone

Therefore full auto-resume should not be modeled as "an external controller decides exactly when work resumes."

## Design Decision

Use `external observation + repository-native self-arbitration`.

The continuation packet remains the repository-side source of restart truth.
The external side may observe quota recovery and wake potential workers, but it must not be the sole arbiter of which session resumes which goal.

Resume authority is decided by repository-visible state:

1. append-only continuation packets
2. a single active goal lease
3. drift checks before resume
4. optional subgoal-level decomposition when one large goal would create contention

## Runtime Contract

After semantic routing selects `goal_mode`, the runtime contract for full auto-resume is:

1. the selected Skill preserves continuation state in repository-visible form
2. the repository becomes the source of restart truth
3. resume arbitration is decided inside repository-visible state
4. external systems may observe, wake, or expose discovery surfaces, but they do not become the hidden owner of resume truth

The rest of this page describes that runtime contract and implementation options.

## Architecture

The target architecture is:

1. XRefKit continuation packet registry in `work/`
2. XRefKit goal lease registry
3. optional subgoal or work-item decomposition registry
4. Codex client startup and stop hooks
5. external quota-state observation signal
6. optional MCP job inbox used only as wake or discovery surface

The interaction is:

1. Codex runs a goal in `goal_mode`
2. usage reaches `0%`
3. Codex appends a continuation packet and releases or expires its active lease
4. an external watcher records that quota may be available again
5. one or more Codex sessions wake and inspect resumable goals
6. each session attempts to acquire the goal lease
7. only the lease holder may resume
8. the lease holder reloads the latest valid continuation packet
9. the lease holder performs drift checks
10. the lease holder resumes the first recorded next action
11. the lease holder appends new state and eventually closes or releases the lease

## Responsibility Split

Keep the split explicit:

- XRefKit repository:
  - continuation packet schema and append-only history
  - lease state
  - judgment, unresolved, and artifact persistence
  - drift-check rules
  - resume procedure definition
- external observer:
  - quota recovery observation only
  - optional wake signal
- optional control plane:
  - discovery surface
  - non-authoritative wake or queue visibility
- Codex runtime:
  - executing only after lease acquisition
  - reload and drift check
  - result write-back
- provider-facing watcher:
  - detecting that usage may actually be recoverable

Do not collapse these responsibilities into one implied "auto-resume" statement.

## Core Repository Primitives

### 1. Append-Only Continuation Packet Registry

Each stop or handoff appends one continuation packet rather than rewriting one mutable master record.

Minimum fields:

- `goal_id`
- `packet_id`
- `created_at`
- `created_by`
- `continuation_log`
- `continuation_artifacts`
- `goal_state_summary`
- `next_first_action`
- `stop_conditions`
- `drift_check_points`
- `packet_status`
- `source_run_key`
- `trace_id`

Recommended additional fields:

- `parent_packet_id`
- `subgoal_id`
- `resume_blockers`
- `expiry_hint`

Rules:

- packets are appended, not overwritten
- later sessions consume the latest valid packet
- invalid or superseded packets remain visible for audit

### 2. Goal Lease

Each resumable goal may have at most one active lease.

Minimum fields:

- `goal_id`
- `lease_owner`
- `lease_acquired_at`
- `lease_expires_at`
- `lease_status`
- `source_packet_id`
- `attempt_count`

Rules:

- only one active lease may exist per goal
- lease acquisition must be atomic
- only the lease owner may mark active resume progress
- expired leases may be reclaimed
- a session without the lease must not resume substantive work

### 3. Optional Subgoal Decomposition

Large goals should not always be resumed as one monolith.

When concurrency pressure is high, decompose the goal into subgoals or work items:

- each subgoal gets its own continuation packet lineage
- each subgoal may carry its own lease
- the parent goal tracks dependency and completion conditions

This reduces collision surfaces when multiple resumable goals or agents coexist.

## Resume State Model

The state machine should be:

1. `waiting_for_quota`
2. `wakeup_observed`
3. `lease_pending`
4. `leased`
5. `running`
6. `completed`
7. `failed`
8. `cancelled`

State rules:

- only `waiting_for_quota` goals may become `wakeup_observed`
- `wakeup_observed` means "resume may now be attempted," not "resume is already authorized"
- lease acquisition must happen after wakeup observation
- only the lease owner may mark `running`, `completed`, or `failed`
- drift-check failure must return the goal to `failed`, `cancelled`, or back to `waiting_for_quota`, not silently continue

## Required Resume Packet Content

The continuation packet must be strong enough that a later session can resume without human reconstruction.

Minimum contents:

1. goal statement
2. current boundary
3. completed work summary
4. remaining work summary
5. exact next first action
6. changed artifact paths
7. unresolved unknowns
8. unresolved risks
9. non-trivial judgments and their references
10. stop conditions
11. drift-check points before resume

If any of these are missing, automatic resume should not acquire or keep the lease.

## Quota Recovery Detection

This repository does not itself own provider quota state.

Therefore auto-resume requires one explicit watcher mechanism such as:

1. provider-supported hook or API poller
2. local scheduler that checks trusted provider-visible usage state
3. dashboard-side quota-state updater

The watcher must write explicit recovery evidence into repository-visible wake state or an equivalent observable surface.

Do not guess recovery time from an old human note when a machine-visible signal is required.

## Implementation Options

The following mechanisms are implementation options under the `goal_mode` runtime contract.

They are not the routing surface seen by the human.

### Hook Strategy

The preferred hook model is:

1. session start hook:
   - inspect resumable goals with wakeup observed
   - try to acquire one allowed lease
   - inject the continuation packet path into the startup context
2. stop hook:
   - if work stopped because of quota exhaustion, finalize and append the continuation packet, then release or expire the lease
3. failure hook:
   - append failure reason
   - release the lease or mark the goal failed explicitly

This preserves auditable state transitions rather than hidden prompt replay.

### Drift Check Before Resume

Automatic resume must not skip drift checks.

Before substantive work resumes, Codex must confirm:

1. no newer user instruction invalidates the goal
2. branch state is still acceptable
3. required artifacts still exist
4. approvals and boundary conditions still hold
5. unresolved blockers were not promoted into stop conditions

If the drift check fails, the session must stop and surface the blocker explicitly. It must not retain the lease unless the design explicitly allows a remediation hold.

### Failure Cases

The design must handle at least:

1. quota recovered but branch drifted
2. quota recovered but required artifact disappeared
3. provider signaled recovery incorrectly
4. lease owner died after lease acquisition
5. multiple sessions attempt to resume the same goal
6. the continuation packet is incomplete

Required responses include:

- lease release or expiry
- explicit drift blocker note
- operator-visible wake and lease state

## Minimal Implementation Plan

Phase 1:

- define continuation packet requirements in `goal_mode`
- add append-only continuation packet rules
- add goal lease rules
- add waiting and wakeup-observed states

Phase 2:

- implement quota watcher integration
- implement session-start lease acquisition and resume logic
- implement stop-hook append and lease release

Phase 3:

- add drift-check enforcement before resume
- add duplicate-resume prevention through lease enforcement
- add optional subgoal decomposition rules
- add OR Team visibility for resume failures and recurrence

## Why This Design Is Preferred

This design is preferred because it keeps full auto-resume explicit, state-based, and auditable.

It avoids pretending that one long prompt or one local note can safely carry cross-session continuity by itself.
It also avoids making an external deterministic scheduler the hidden owner of resume truth.

It also preserves the repository's existing control model:

- explicit runtime envelope
- explicit handoff
- explicit unresolved items
- explicit claim ownership
- explicit closure or failure

## Related

- [Codex goal mode usage guide](../guides/069_codex_goal_mode_usage_guide.md#xid-3E7B4C11A8D2)
- [Codex MCP job inbox design](050_codex_mcp_job_inbox_design.md#xid-77BCEAA247E3)
- [Skill operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
