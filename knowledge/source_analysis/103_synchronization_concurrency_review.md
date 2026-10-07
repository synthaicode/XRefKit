<!-- xid: 5F21C8A41103 -->
<a id="xid-5F21C8A41103"></a>

# Synchronization And Concurrency Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.

## Synchronization And Concurrency Review

Check at least the following:

- lock ordering, deadlock-prone nested locking, and mutually waiting workers
- race-prone shared mutable state
- blocking waits inside asynchronous, event-driven, or cooperative execution
  paths
- missing cancellation and timeout propagation
- context capture, scheduler affinity, event-loop, or runtime-dispatcher
  assumptions where relevant
- time-controlled, polling, or scheduler-driven wait loops that cannot wake on
  the state transition they are waiting for

When code uses a virtual clock, fake clock, polling delay, timer, or scheduler
controlled wait loop, verify whether the awaited state change also has a
direct wake-up path.

Check at least the following:

- whether a waiter is blocked only on time progression even though another
  actor can satisfy the waited condition immediately
- whether the producer-side state transition also emits a signal,
  notification, channel write, task completion, event, or semaphore release
  that wakes waiters
- whether tests using fake or manually advanced time can hang because no one
  advances time after the required state transition already happened
- whether polling-only retry loops should become `time or signal` waiting so
  timeout behavior and immediate wake-up behavior both remain testable

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
