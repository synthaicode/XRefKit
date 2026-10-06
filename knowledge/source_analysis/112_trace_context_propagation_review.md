<!-- xid: 5F21C8A41110 -->
<a id="xid-5F21C8A41110"></a>

# Traceability And Context Propagation Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.

## Traceability And Context Propagation Review

Check whether execution context survives the boundaries that matter for
diagnosis, audit, replay, and cross-agent or cross-service handoff.

Check at least the following:

- trace id, correlation id, causality, tenant/user/source identity, request or
  job id, attempt count, and origin metadata propagate through async calls,
  background tasks, queues, timers, callbacks, and agent handoffs where needed
- structured logging context is attached at the boundary where failures can
  occur, not reconstructed from ambiguous display values later
- fire-and-forget work, detached tasks, event handlers, and scheduled work do
  not lose the context needed to attribute failures
- fan-out and retry paths preserve parent-child relationships and attempt
  metadata
- context propagation does not leak sensitive context to unrelated work or
  broader scopes than intended
- source identity remains stable enough to deduplicate, replay, compensate, or
  audit work after archival, acknowledgement, deletion, or state transition

Findings must name the broken propagation boundary and the operational,
audit, or handoff consequence of the missing context.

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
