<!-- xid: 5F21C8A41001 -->
<a id="xid-5F21C8A41001"></a>

# Common Source Analysis Criteria

This page defines language-neutral viewpoints for analyzing an existing codebase before planning, design, or review.

## Core Viewpoints

| Viewpoint | What to confirm |
|------|------|
| Entry points | where execution starts and how requests, jobs, or events enter the system |
| Responsibility split | how behavior is divided across layers, modules, services, or components |
| Dependency direction | which components depend on which others, and whether the direction is intentional |
| Extension points | where new behavior is naturally added without violating the current structure |
| Data boundary | where input, output, persistence, and mapping boundaries exist |
| Configuration boundary | where settings are loaded, overridden, and consumed |
| Error boundary | where failures are handled, translated, retried, or surfaced |
| Security boundary | where authentication, authorization, secret handling, and sensitive-data controls apply |
| Performance-sensitive paths | where expensive or high-frequency execution occurs |
| Operational hazard paths | where source-visible execution can amplify load, partially commit across boundaries, lose work ownership, hide failures, or expand blast radius |
| Test boundary | how unit, integration, regression, and edge-case tests are organized |
| Application/framework boundary | what belongs to reusable framework mechanisms versus application-specific code |

## Operational Hazard Taxonomy

Operational hazard analysis is language-neutral. Apply it to loops, batch
workers, queue consumers, import/export jobs, retry paths, request fan-out,
external I/O, and other code paths where normal code behavior can become an
incident under volume, backlog, failure, restart, or multi-worker execution.

Use these families as review lenses, not as an automatic severity table. A
finding still needs local evidence, an affected boundary, and a plausible
failure path.

1. Shared resource exhaustion:
   - TCP sockets
   - ephemeral ports
   - DB connection pools
   - thread or worker-pool capacity
   - file handles
   - memory and large-object allocation pressure
   - DB transaction log growth
   - CPU, queue capacity, request slots, process ids, cache capacity, and
     garbage-collection or runtime housekeeping capacity
2. Retry amplification:
   - infinite retry
   - immediate retry
   - no jitter
   - no retry budget
   - nested retry
   - no circuit breaker or equivalent stop condition
3. Backlog drain spike:
   - large unbounded reads such as `TOP 50000`
   - full backlog enumeration such as listing all pending files or queue items
   - high fan-out parallel dispatch
   - restart after outage causing a burst against downstream systems
4. Boundary partial commit:
   - DB update plus external send
   - DB insert plus file delete/archive
   - API call plus local state update
   - missing idempotency key or replay-safe operation identity
5. Missing claim, lease, or state transition:
   - queue rows read without a claim
   - files read without atomic move, rename, lock, or equivalent ownership
     marker
   - multi-worker race on the same work item
   - missing processing, retry, or dead-letter state
6. Observability failure:
   - empty catch or swallowed failure
   - no failure state
   - no attempt count
   - no correlation id
   - no metric
   - no phase-specific error
7. Blast-radius failure:
   - batch and online service share host or runtime
   - shared connection pool
   - shared DB dependency without workload isolation
   - shared worker pool saturation path
   - no bulkhead, isolation, or workload-specific limit

## Overload And Resource-Control Source Basis

Use these source-backed lenses when reviewing resource consumption and
operational resilience:

- Google SRE Book, [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/):
  overload can spread when failed or unhealthy capacity shifts load to the
  remaining capacity; CPU, memory, threads, file descriptors, queues, health
  checks, deadlines, retries, and dependency cache misses can feed one another.
- Google SRE Book, [Handling Overload](https://sre.google/sre-book/handling-overload/):
  retries need per-request and per-client budgets, and overloaded downstreams
  need a way to signal "do not retry" so retry work does not multiply across
  layers.
- MITRE [CWE-400: Uncontrolled Resource Consumption](https://cwe.mitre.org/data/definitions/400.html):
  review whether external input, unauthenticated callers, malformed payloads,
  large length/count fields, recursion, many connections, or large request
  bodies can consume unbounded CPU, memory, stack, file descriptors, sessions,
  queues, or connection state.

## Resource Efficiency Review

Resource efficiency covers waste, cost, and local performance. Do not stop at
this category when the same pattern creates an operational failure path.

Check at least the following:

- disposable or closeable resource lifetimes are bounded and ownership is clear
- avoidable allocations and buffering in hot paths
- inefficient I/O and data access patterns, including chatty calls, repeated
  serialization, and redundant buffering
- cache and pooling opportunities where repeated expensive creation is observed
- external-input-controlled allocation, parsing, buffering, recursion,
  expansion, fan-out, or connection/session creation without an explicit bound
- post-limit behavior: whether the code stops reading/processing, closes or
  drains safely, releases resources, and records a controlled failure

## Operational Resilience Review

Operational resilience covers failure paths, blast radius, and incident
diagnosability. It sits above resource efficiency: a wasteful pattern becomes
an operational-resilience finding when it can exhaust shared resources or make
production failures difficult to attribute.

Check at least the following:

- the operational hazard taxonomy above
- OS, process, runtime, service-host, and downstream shared resource
  exhaustion
- useful-work collapse: overload paths where latency, retries, queueing, cache
  misses, health-check failure, or crash/restart loops reduce successful work
  faster than incoming work decreases
- resource dependency chains, such as CPU pressure increasing latency,
  latency increasing in-flight work, in-flight work increasing memory, memory
  pressure reducing cache hit rate, and cache misses overloading dependencies
- TCP connection churn, socket exhaustion, connection-pool misuse, backlog
  drain spikes, retry storms, queue accumulation, and resend loops
- missing rate limits, throttles, backpressure, leases, or bounded batches on
  external I/O loops
- missing overload admission control, load shedding, graceful degradation, or
  cheap early rejection at the layer that can still protect shared resources
- queue sizing that stores too much doomed work, hides overload latency, or
  consumes memory instead of rejecting work early
- request, job, or RPC processing that continues after its caller-visible
  deadline or cancellation makes the work no longer useful
- missing deadline and cancellation propagation across fan-out, callbacks,
  stages, or downstream calls
- blast radius to unrelated workloads on the same host, runtime, process, DB,
  queue, connection pool, or downstream service
- missing logs, metrics, failure persistence, or correlation that would prevent
  operators from identifying the causal component during an incident
- discovery/enumeration failures that occur outside the observed failure
  boundary, such as directory traversal, file listing, queue discovery, source
  enumeration, or backlog selection before per-item error handling starts
- loss of source identity or correlation across import, queue, file, message,
  or external-boundary processing, especially when later delete/archive/update
  removes original evidence

### Operational Escalation Rule

If a loop or worker repeatedly creates, opens, or disposes a client,
session, connection, handle, or execution slot backed by shared resources,
review the path as an operational failure scenario, not only as resource
efficiency.

Classify by resource ownership, lifecycle, scope, volume, and observability
evidence instead of by matching a named API or library.

Escalate to `major` or higher when all or most of the following are visible:

- scarce resource creation occurs inside a loop, batch, queue consumer, retry
  path, import/export job, or request fan-out
- the resource is shared at OS, process, runtime, service-host, DB, queue, or
  downstream-service level
- close or disposal likely releases or churns physical/shared capacity
- batch size, backlog size, retry count, or fan-out is unbounded or large
- no rate limit, throttle, backpressure, retry budget, lease, or bulkhead is
  visible
- retry is immediate, nested, cross-layer, or lacks a per-request/per-client
  budget or "do not retry" overload signal
- failures are swallowed, not persisted, or lack correlation
- the code may run alongside unrelated workloads

When this pattern is visible, name the concrete path from backlog, retry, or
fan-out volume to resource churn, shared-resource exhaustion, blast radius,
and loss of diagnosability.

### Deadline And Cancellation Review

For request trees, jobs split into stages, callbacks, RPCs, and fan-out, check
whether the remaining useful time is evaluated before performing more work.

Check at least the following:

- incoming deadline or cancellation is propagated to downstream calls, worker
  stages, and fan-out children
- each stage checks whether enough useful time remains before expensive work
  or downstream calls
- hardcoded downstream timeouts do not extend work past the original caller's
  deadline
- canceled or superseded hedged/fallback work is stopped throughout the stack
- exceptions are intentional and checkpointed, such as catch-up work that must
  complete a durable checkpoint before honoring cancellation

### Retry And Overload Signal Review

For retrying callers and overloaded callees, check whether retry work is
bounded and whether overload information travels across the boundary.

Check at least the following:

- per-request retry budget
- per-client or caller retry budget / retry ratio
- jittered backoff and retry budget shared across nested calls where needed
- attempt count or retry metadata propagated to downstreams
- overloaded callee can return a "do not retry" or equivalent terminal
  overload response
- only the layer immediately above the rejecting dependency retries, avoiding
  combinatorial retry explosion across deep stacks
- failed retries have an observable disposition instead of being hidden as
  normal traffic

### Load Shedding And Degradation Review

For services, jobs, and shared components under overload, check whether the
code has a controlled way to shed or reduce work before shared resources fail.

Check at least the following:

- overload decisions are based on relevant signals such as CPU, memory, queue
  length, in-flight work, thread/worker usage, latency, dependency saturation,
  or health state
- rejection is early and cheap compared with accepting and later failing work
- degraded responses reduce work while keeping the mode simple, observable,
  and regularly exercised
- load shedding and degradation controls cannot easily enter feedback loops,
  synchronized failure, or accidental permanent degradation
- operators can observe and alert when too many instances enter degraded or
  shedding mode

### Source And Import Worker Review

For file import, directory import, queue import, message import, and similar
source-to-sink workers, review discovery separately from per-item processing.

Check whether source discovery runs inside an observed failure boundary:

- directory traversal and file listing
- recursive enumeration
- queue reads, source listing, or backlog selection before item-level
  processing begins
- permission, missing path/source, locked/offline source, path length,
  malformed input, unavailable queue, or transient storage failure

If discovery failure can stop the whole run before per-item handling starts,
report it as an error-boundary and operational-resilience finding.

Check whether the imported record preserves enough source identity and
correlation to diagnose, deduplicate, replay, audit, and compensate:

- full path, message id, queue key, or normalized relative identity when policy
  permits
- source root or source system id
- content hash, size, timestamp, and attempt id where useful
- correlation between source read, sink write, delete/archive/quarantine, and
  logged failure records

If code reduces identity to a non-unique display value while importing,
deleting, archiving, acknowledging, or updating the source, report the loss as
operational resilience or data-boundary risk. Escalate to `major` when
duplicate names, replay/audit, or incident correlation can be lost.

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

## Required Input Integrity Review

When code derives billing, authorization, routing, eligibility, tax, rate,
limit, entitlement, compliance, or other decision-critical behavior from
external configuration, cache state, file/message content, DB rows, or an API,
review both visible failures and silent fallbacks.

Check paired paths for the same required input class:

- lookup that throws on missing input
- `try get`, `contains`, optional, nullable, or missing-key paths that return a
  default value
- zero, false, empty collection/string, default enum/status, null, or skipped
  branch fallback
- catch-and-default behavior after config/API/cache/file/message/DB failure

If the value is required to decide whether processing may continue, a missing
input must become a controlled outcome such as blocked, failed, needs
configuration, dead-letter, retry, quarantine, or explicit handoff. Do not
treat a syntactically valid fallback as safe merely because it does not throw.

Escalate to `major` or higher when a silent fallback can cause billing,
payment, entitlement, tax, authorization, routing, eligibility, limit, or
compliance behavior to proceed with an invented value.

Report at least:

- required input name and business decision it gates
- input source, such as cache, API, DB, file, message, or config
- missing-input behavior: throw, default substitution, catch-and-default,
  optional/default fallback, default enum/status/null/empty value, or skipped
  branch
- whether the default value is explicitly configured or invented by code
- controlled disposition that should replace the missing-input path

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

## Time And Culture Review

Check at least the following:

- mixing local and UTC time in the same comparison, storage, scheduling, or
  retention flow
- missing or inconsistent timezone metadata across boundaries
- timezone and DST assumptions, including local-time arithmetic across DST
  transitions and server-timezone dependence in stored timestamps
- culture-sensitive formatting, parsing, comparison, collation, decimal, or
  calendar behavior used in protocol, persistence, serialization, or
  interchange contexts where invariant or explicitly configured behavior is
  required

Classify as `needs_confirmation` when the execution environment's timezone,
culture, collation, or calendar configuration cannot be established from local
evidence.

## Planning Rule

Planning should use these viewpoints to produce a modification policy that follows the current codebase structure by default.

## Unknown Rule

- If a core viewpoint cannot be confirmed, record `unknown`.
- Do not invent a cleaner target structure unless the current structure and deviation reason are both explicit.
