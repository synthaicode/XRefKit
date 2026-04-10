<!-- xid: 2E7B5A1FD201 -->
<a id="xid-2E7B5A1FD201"></a>

# Dotnet Change Analysis Viewpoints

This page defines .NET-specific viewpoints for analyzing an existing application structure before change planning, design, or implementation.

## Core Viewpoints

| Viewpoint | What to confirm |
|------|------|
| Solution and project structure | which solutions, projects, assemblies, and module boundaries define the current unit of change |
| Entry points | where execution starts for web requests, background jobs, workers, scheduled tasks, functions, or message consumers |
| Dependency direction | how application, domain, infrastructure, shared libraries, and framework code depend on one another |
| Configuration boundary | where settings are loaded, bound, overridden, and consumed across environment-specific behavior |
| API and integration boundary | where controllers, endpoints, gRPC handlers, clients, queues, and external service adapters connect |
| Data boundary | where persistence, transactions, caching, mapping, and database migrations are controlled |
| Logging policy | where logs are emitted, which events are recorded, how levels are configured, and what sensitive information must not be emitted |
| Attribute usage | which standard and custom attributes affect routing, authorization, validation, serialization, transactions, DI, or custom framework behavior |
| Concurrency and execution timing | where async execution, background processing, retries, scheduling, shared state, cancellation, and transactional timing constraints exist |
| Performance-sensitive paths | where high-frequency paths, heavy I/O, expensive serialization, avoidable allocations, or repeated computation create risk |
| Resource efficiency | where disposable objects, connections, streams, buffers, threads, or singleton state require lifetime and ownership checks |
| Test boundary | which tests currently protect the target behavior and where additional regression coverage is needed |
| Change impact and uncertainty | which targets are directly or indirectly affected and which conclusions remain `unknown` because evidence is missing |

## Attribute Analysis Rule

- Extract attribute usage candidates from `[]` syntax.
- Exclude numeric tokens and syntax that is not an attribute.
- Resolve each candidate as both `Xxx` and `XxxAttribute`.
- Confirm namespace and definition origin.
- Record usage location, arguments, and target.
- Confirm the consuming code and the activation condition.
- Mark the attribute result as `unknown` when the consuming mechanism cannot be confirmed.

## Logging Policy Rule

- Confirm where logs are emitted in request paths, batch paths, and integration paths.
- Confirm logging level control, sinks, enrichment, and environment-specific overrides.
- Confirm whether business events, exceptions, audit events, and performance signals are intentionally recorded.
- Confirm whether personally identifiable information, credentials, secrets, or oversized payloads could be emitted.
- Confirm whether the intended change alters monitoring, alerting, or operational procedures.

## Concurrency Rule

- Confirm async call chains, background workers, schedulers, queue consumers, and retry handlers.
- Confirm shared mutable state in singleton services, static fields, caches, and in-memory coordination.
- Confirm locking, semaphore, and transaction boundaries.
- Confirm cancellation and timeout propagation.
- Confirm duplicate execution and ordering risks.

## Performance And Resource Rule

- Confirm high-frequency or heavy-I/O paths before proposing or evaluating a change.
- Confirm resource lifetime and ownership for `IDisposable` and `IAsyncDisposable` objects.
- Confirm whether the change increases allocation, serialization, logging, connection, or retry overhead.
- Confirm whether long-running or background processes can retain memory, threads, or connections unexpectedly.

## Output Rule

Produce a Markdown note that records, for each viewpoint:

- state (`done`, `unknown`, or `not_applicable`)
- evidence
- change impact
- unresolved follow-up
