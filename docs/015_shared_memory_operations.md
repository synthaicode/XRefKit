<!-- xid: 4A423E72D2ED -->
<a id="xid-4A423E72D2ED"></a>

# Shared Memory Operations (AI-authored event logs)

This repository adopts a shared-memory model for AI collaboration.
The goal is to make past decisions and context reloadable across sessions.

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

## Related

- [Working area policy](014_working_area_policy.md#xid-111D282CA0EA)
- [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
- [Startup xref routing policy](011_startup_xref_routing.md#xid-6C0B62D6366A)
