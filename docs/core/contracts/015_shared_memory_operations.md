<!-- xid: 4A423E72D2ED -->
<a id="xid-4A423E72D2ED"></a>

# Shared Memory Operations (AI-authored event logs)

This repository adopts a shared-memory model for AI collaboration.
The goal is to make past decisions and context reloadable across sessions.

This page defines the session/event-log pattern only.
For the full split across session logs, judgment logs, and structural feedback records, see [Work record types](../../reference/019_work_record_types.md#xid-4F8C21B7D4A2).

## Core Idea

- AI has no persistent time sense across sessions.
- Shared memory is built with AI-authored event logs.
- Logs record facts about what happened, not AI interpretation.

## Logging Rules

Log events only:

- what was discussed
- what was decided
- what the human explicitly stated (as stated fact)
- what was deferred
- what remains open

Do not log:

- AI judgment about whether a decision is good
- retrospective analysis in the event log body
- speculative conclusions not stated by humans

## Write Policy

- AI MUST write logs automatically after significant discussions, decisions, or work sessions.
- AI MUST ensure the current task has a `work/sessions/` entry before final response.
- AI MUST ensure logs are updated before `git commit` or `git push`.
- Humans review logs for accuracy; humans do not need to author these logs.
- Log location: `work/sessions/` and `work/retrospectives/`.
- AI MUST promote stabilized decisions/facts from `work/` to canonical docs (`docs/`, `knowledge/`).
- Filename MUST be date-prefixed: `YYYY-MM-DD_<type>_<topic>.md`.

## Event Log Format

```md
## <YYYY-MM-DD>: <event title>

### Event
<what happened>

### Decision
<decision made>

### Human Stated Reason
<quoted/paraphrased statement by human>

### Deferred
<items explicitly deferred>

### Open
<unresolved items>
```

## Session Reload Pattern

When starting a new session:

1. Load current plan/goal.
2. Load relevant event logs from `work/`.
3. Load required canonical docs (`docs/`, `knowledge/`) by XID.
4. Continue from current focus only.

## Context Rollback Pattern

When rolling back direction, align all artifacts to the same point:

- code state
- log state
- document state
- plan state

Do not mix states from different points in time.

## Prompt Flow Trace

When one user prompt spans a generic workflow and one or more delegated Skill
Runs, initialize one Prompt Flow for the prompt and preserve the same
`flow_id` and `root_run_id` across all related runs. A child run MUST also
record `parent_run_id`, `work_item_id`, and `node_id` when applicable.

The main AI or orchestrator owns semantic routing and may start a child Skill
for a work item. Runtime reconciliation is deterministic: it verifies the
recorded correlation and child `Closure Gate` before projecting `done` or
`escalated` to the linked parent work item. Reconciliation is report-only by
default; status projection requires an explicit operation and does not execute
work, recovery, quality review, or parent closure.

If correlation, completion evidence, recovery confirmation, or work-item
mapping is uncertain, do not project status. Record the finding and escalate
for human confirmation. The parent Flow is eligible for completion only when
all work items are `done` or `escalated` and the normal verification and
closure gates pass.

## Related

- [Work record types](../../reference/019_work_record_types.md#xid-4F8C21B7D4A2)
- [Working area policy](../../policies/014_working_area_policy.md#xid-111D282CA0EA)
- [Agent Entry](../../../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
- [Startup xref routing policy](011_startup_xref_routing.md#xid-6C0B62D6366A)
