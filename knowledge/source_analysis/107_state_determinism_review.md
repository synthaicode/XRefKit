<!-- xid: 5F21C8A41107 -->
<a id="xid-5F21C8A41107"></a>

# State And Determinism Boundary Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.

## State And Determinism Boundary Review

Check whether state transitions are deterministic enough for the system's
execution model, especially across asynchronous paths, background jobs,
message handlers, and agent-to-agent coordination.

Check at least the following:

- mutable state is scoped to a clear owner, request, job, session, actor, or
  transaction boundary
- state transitions are represented explicitly enough to replay, audit, retry,
  or compensate the work when required
- pure decision logic is separated from side effects where the surrounding
  workflow relies on deterministic judgment
- thread-local, async-local, process-global, singleton, cache, or static state
  does not leak decisions, credentials, user context, or partial progress
  across unrelated work
- retries, replays, duplicate messages, restarts, or parallel workers cannot
  apply non-idempotent state transitions silently
- hidden side effects are not buried inside helpers that appear to be pure
  classification, parsing, validation, or mapping functions

Findings must name the state owner, the transition, and the path where
non-determinism, state leakage, or hidden side effects can change the outcome.

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
