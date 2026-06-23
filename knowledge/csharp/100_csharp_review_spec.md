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

Resource efficiency covers waste, cost, and local performance. Do not stop at
this category when the same pattern creates an operational failure path.

## Operational Resilience Checks

Operational resilience covers failure paths, blast radius, and incident
diagnosability. It sits above resource efficiency: a wasteful pattern becomes
an operational-resilience finding when it can exhaust shared resources or make
production failures difficult to attribute.

Check at least the following:

- OS-shared resource exhaustion, including ephemeral ports, sockets, file
  handles, threads, and worker queues
- TCP connection churn, `TIME_WAIT` accumulation, ephemeral port exhaustion,
  and socket exhaustion
- connection-pool misuse, including per-operation client creation where the
  client owns outbound TCP connections
- backlog-drain spikes, retry storms, queue accumulation, and resend loops
- missing rate limits, throttles, backpressure, leases, or bounded batches on
  external I/O loops
- blast radius to unrelated workloads on the same OS, process, runtime, or
  service host
- missing logs, metrics, failure persistence, or correlation that would prevent
  operators from identifying the causal component during an incident
- discovery/enumeration failures that occur outside the observed failure
  boundary, such as directory traversal, file listing, queue discovery, or
  source enumeration before per-item error handling starts
- loss of source identity or correlation across import, queue, file, or
  external-boundary processing, especially when a later delete/archive/update
  removes the original evidence

### Operational Escalation Rule

If a loop or batch worker repeatedly creates, opens, or disposes network
clients or outbound TCP connections, review the path as an operational failure
scenario, not only as resource efficiency.

Check whether the pattern can exhaust host-level shared resources such as
ephemeral ports, sockets, connection pools, file handles, threads, or worker
queues.

If the exhausted resource is shared at OS, process, runtime, or service-host
level, assess whether unrelated workloads on the same host can be affected.

Escalate to `major` or higher when all or most of the following are visible:

- network client creation occurs inside a batch loop
- the client owns outbound TCP connections
- disposal or close likely terminates physical connections
- batch size is unbounded or large
- no rate limit, throttle, or backpressure is visible
- failures are swallowed or not persisted
- the code may run on a shared host or service VM

For SMTP queue senders, do not stop at "repeated expensive setup" when a
per-message SMTP/TCP lifecycle is visible. Name the risk path through
backlog-drain connection churn, `TIME_WAIT`, Windows dynamic-port exhaustion,
host-level blast radius, and loss of diagnosability when the evidence supports
that path.

### File and Import Worker Review

For file import, directory import, queue import, and similar source-to-sink
workers, review the discovery phase separately from per-item processing.

Check whether source discovery runs inside an observed failure boundary:

- directory traversal and file listing
- recursive enumeration
- queue reads or source listing before item-level processing begins
- permission, missing path, locked/offline share, path length, malformed input,
  or transient storage failures

If discovery failure can stop the whole run before per-item handling starts,
report it as an error-boundary and operational-resilience finding.

Check whether the imported record preserves enough source identity and
correlation to diagnose, deduplicate, replay, audit, and compensate:

- full path or normalized relative path when policy permits
- source root or source system id
- content hash, file size, timestamp, and import attempt id where useful
- correlation between source read, sink write, delete/archive/quarantine, and
  logged failure records

If code reduces identity to a non-unique display name, such as only
`Path.GetFileName(file)`, while recursively importing or deleting the source,
report the loss as operational resilience or data-boundary risk. Escalate to
`major` when duplicate names, replay/audit, or incident correlation can be
lost.

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
