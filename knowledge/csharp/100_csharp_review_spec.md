<!-- xid: 30E6A4F6F3AA -->
<a id="xid-30E6A4F6F3AA"></a>

# C# Review Spec (Manual, non-Roslyn scope)

This fragment defines the canonical review scope for manual C# checks.

## Scope Boundary

- Primary boundary: exclude concerns that Roslyn diagnostics already detect.
- This spec covers review signals that are often semantic, environment-dependent, or cross-file/project.
- Security-scope findings (injection paths, hardcoded secrets, disabled
  certificate validation) belong to the security review skill; design-assumption
  findings belong to the constraint-derivation pack. Record them for handoff
  instead of deep-diving them under this spec.

## Attribute Value Misuse Rule

Apply this sequence per attribute usage under review:

1. Determine attribute origin (library/package/framework).
2. Determine functional preconditions required by that attribute.
3. Verify those preconditions in the current project.
4. Report when preconditions are not satisfied.

### Classification

- `origin_unresolved`: attribute source cannot be resolved.
- `precondition_unmet`: source resolved but required precondition is not met.
- `needs_confirmation`: static evidence is insufficient to decide.

### Policy

- Do not rely on fixed whitelists of attribute values.
- Treat unknown/new values as `needs_confirmation` unless there is concrete proof of violation.
- Findings must include concrete evidence:
  - attribute location
  - expected precondition
  - missing or contradictory project evidence

## Resource Efficiency Checks

Check at least the following:

- disposable lifetimes are bounded and ownership is clear
- avoidable allocations in hot paths (strings, buffers, LINQ chains, boxing)
- inefficient I/O and data access patterns (chatty calls, repeated serialization, redundant buffering)
- cache and pooling opportunities where repeated expensive creation is observed

## Synchronization Checks

Check at least the following:

- deadlock-prone lock ordering and nested locking risks
- race-prone shared mutable state
- blocking waits (`.Result`, `.Wait()`) in async flows
- missing cancellation and timeout propagation
- synchronization-context capture concerns where relevant
- time-controlled or test-controlled async wait paths that cannot wake on the
  state transition they are waiting for

### Time-Controlled Wait Review

When code uses a virtual clock, fake clock, polling delay, or scheduler-driven
wait loop, verify whether the awaited state change also has a direct wake-up
path.

Check at least the following:

- whether a waiter is blocked only on time progression (`Delay`, timer tick, or
  scheduler advance) even though another actor can satisfy the waited
  condition immediately
- whether the producer-side state transition also emits a signal, notification,
  channel write, task completion, or semaphore release that wakes waiters
- whether tests using a fake or manually advanced clock can hang forever
  because no one advances time after the required state transition already
  happened
- whether polling-only retry loops should be converted to `time or signal`
  waiting so timeout behavior and immediate wake-up behavior both remain
  testable

## Error Handling and Exception Path Checks

Check at least the following:

- swallowed exceptions: empty `catch`, catch-and-log-only paths where the
  failure can silently lose data or leave state inconsistent
- rethrow patterns that discard the original context (`throw ex;` beyond
  analyzer coverage, wrapping that drops the inner exception)
- `async void` outside event handlers, and event handlers whose exceptions
  escape unobserved
- retry loops without backoff/jitter, and retries around non-idempotent
  operations
- transaction and compensation boundaries: partial-commit windows where a
  failure between two writes leaves no compensation path
- error paths that bypass cleanup (`Dispose` not reached on the exception
  path, missing `finally`/`await using` on failure routes)

Findings must name the failure path concretely: which exception, raised
where, and what state or resource is left behind.

## Time and Culture Checks

Check at least the following:

- `DateTime.Now` / `DateTime.UtcNow` mixing in the same comparison, storage,
  or scheduling flow, and `DateTimeKind` inconsistency across boundaries
- timezone and DST assumptions: local-time arithmetic across DST transitions,
  server-timezone dependence in stored timestamps
- culture-sensitive `ToString()` / `Parse()` / string comparison used in
  protocol, persistence, serialization, or interchange contexts that require
  the invariant culture
- format strings and decimal separators that change meaning under a
  non-default culture

Classify as `needs_confirmation` when the execution environment's timezone or
culture configuration cannot be established from local evidence.

## Support Lifecycle Checks

Check at least the following:

- target framework support status (supported, out of support, near end of support)
- critical package/runtime dependencies with expired support windows

### Lifecycle source URLs

Use these sources when judging support status:

- .NET and .NET Core support policy:
  - https://dotnet.microsoft.com/en-us/platform/support/policy
  - https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core
- .NET release lifecycle table:
  - https://learn.microsoft.com/en-us/lifecycle/products/microsoft-net-and-net-core
- .NET Framework lifecycle table:
  - https://learn.microsoft.com/en-us/lifecycle/products/microsoft-net-framework

### Reporting minimum

For lifecycle findings, include:

- current version/TFM detected
- support status and key date(s)
- upgrade/remediation direction
