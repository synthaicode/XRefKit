<!-- xid: 5F21C8A41105 -->
<a id="xid-5F21C8A41105"></a>

# Error Handling And Exception Path Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.

## Error Handling And Exception Path Review

Check at least the following:

- swallowed failures and catch/log-and-continue paths that can lose data or
  leave state inconsistent
- rethrow/wrap patterns that discard original failure context
- unobserved asynchronous, event-handler, callback, or background worker
  failures
- retry loops without backoff, jitter, budget, idempotency guarantee, or stop
  condition
- transaction and compensation boundaries where a failure between two effects
  leaves no compensation path
- error paths that bypass cleanup, release, acknowledgement, quarantine,
  rollback, or failure-state recording

Findings must name the failure path concretely: which failure, raised where,
and what state, work item, resource, or external side effect is left behind.

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
