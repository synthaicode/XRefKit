<!-- xid: 5F21C8A41102 -->
<a id="xid-5F21C8A41102"></a>

# Operational Resilience Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.
Also apply the shared [Overload and resource-control source basis](113_overload_resource_source_basis.md#xid-5F21C8A41111) for this axis;
its source-backed lenses are required even without a confirmed incident.

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

### Usage-Dependent Resource Exhaustion Uncertainty

Treat OS and shared-resource exhaustion that depends on caller volume,
deployment limits, host quotas, runtime configuration, or installed package
behavior as a common uncertainty category when static analysis cannot confirm
or rule it out.

Use `needs_confirmation` instead of `pass` when source review finds no direct
unbounded resource creation, but the safety of the path still depends on
operational evidence such as:

- production concurrency, request rate, batch size, backlog size, or retry
  volume
- host or container limits for CPU, memory, process ids, file descriptors,
  sockets, ephemeral ports, temp storage, or cache directories
- service-host, worker-pool, thread-pool, connection-pool, queue, or
  downstream dependency capacity
- deployment-specific timeout, cancellation, rate-limit, throttle,
  backpressure, load-shedding, or bulkhead configuration
- installed package, plugin, extension, or entry-point behavior that is not
  visible in the reviewed source tree
- filesystem, temp/cache, permission, quota, antivirus, lock, or cleanup policy
  that can change resource availability outside source control

Do not report this category as a confirmed defect unless a source-visible path
connects volume or failure to unbounded allocation, handle/socket/process
creation, pool saturation, backlog growth, retry amplification, or missing
release/cleanup. When that path is not source-visible, record the missing
runtime or deployment evidence explicitly in the review matrix and uncertainty
section.

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

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
