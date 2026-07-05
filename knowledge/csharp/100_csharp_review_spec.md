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

## Category Evaluation Rule

Evaluate each review category by its own rule, not by whether it explains the
user's headline review purpose. A synchronization-focused run still evaluates
attribute activation, lifecycle, error handling, and other active categories by
their own axes.

Use `not_applicable` only when the reviewed scope has no construct belonging to
that category's review axis. If constructs exist and no violation is found,
mark the category `pass`. If constructs exist but required evidence is
insufficient, mark it `needs_confirmation`.

## Attribute Activation Preconditions Rule

This category checks whether each reviewed attribute can actually function in
the current project. It is not a string-value preference check.

Apply this sequence per attribute usage under review:

1. Determine attribute origin (library/package/framework).
2. Determine the runtime or build-time mechanism that consumes the attribute.
3. Determine functional preconditions required for the attribute to take
   effect, such as middleware, endpoint routing, model binding, validation,
   serialization, authorization policy/role/claim mapping, source generation,
   reflection scanning, DI registration, or custom framework bootstrap.
4. Verify those preconditions in the current project.
5. Report when the attribute is present but its consuming mechanism or required
   preconditions are absent, contradictory, or unverified.

### Classification

- `origin_unresolved`: attribute source cannot be resolved.
- `consumer_unresolved`: attribute source is resolved but the mechanism that
  consumes the attribute cannot be identified in local evidence.
- `precondition_unmet`: source and consumer are resolved but a required
  precondition is not met.
- `needs_confirmation`: static evidence is insufficient to decide.

### Policy

- Do not rely on fixed whitelists of attribute values.
- Treat unknown/new values as evidence that the consuming mechanism and
  preconditions must be checked; do not report a finding merely because a value
  is unfamiliar.
- Attribute values matter only through the preconditions of the consuming
  mechanism. For example, a role, policy, route name, header name, JSON name, or
  custom key is reviewed by asking whether the configured runtime can consume
  that value as intended.
- Findings must include evidence:
  - attribute location
  - attribute origin and consuming mechanism
  - required precondition
  - missing or contradictory project evidence

## Resource Efficiency Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral resource efficiency review.

For C#, also check common allocation and lifetime patterns such as strings,
buffers, LINQ chains, boxing, `IDisposable`/`IAsyncDisposable` ownership, and
unnecessary repeated serialization.

Do not stop at resource efficiency when the same pattern creates an
operational failure path.

## Operational Resilience Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral operational resilience review, including the operational
hazard taxonomy, operational escalation rule, and source/import worker review.

For C#, also check at least the following:

- per-operation or per-item creation/disposal of .NET outbound clients,
  sessions, database connections, file handles, timers, or similar wrappers
  that own shared host, runtime, or downstream resources
- .NET ThreadPool saturation, worker-queue pressure, connection-pool misuse,
  memory/LOH pressure, TCP connection churn, `TIME_WAIT`, socket exhaustion,
  and ephemeral port exhaustion
- retry, backlog, and import/export paths where .NET runtime behavior can
  amplify the language-neutral operational hazard

## Synchronization Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral synchronization and concurrency review.

For C#, also check at least the following:

- blocking waits (`.Result`, `.Wait()`) in async flows
- synchronization-context capture concerns where relevant
- time-controlled or test-controlled async wait paths that cannot wake on the
  state transition they are waiting for

### Time-Controlled Wait Review

For C# time-controlled waits, use the common time-or-signal rule and the
adopted patterns in
[C# test synchronization patterns](120_csharp_test_synchronization_patterns.md#xid-4314A1A73CAF).

## Required Business Input Integrity Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral required input integrity review.

For C#, common silent fallback forms include `return 0`, `false`, empty
collection/string, default enum, null, `??` fallback, `TryGet` fallback, and
catch-and-default behavior. For tax and pricing code, distinguish a configured
zero value from absent configuration; missing tax/rate inputs must stop
charge/payment until disposition is explicit.

When emitting detector facts for this category, preserve the report-ready
fields defined in
[Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001):
input/candidate, decision gated, source, missing/invalid behavior, default
provenance, disposition, and status. The human-facing report shape is owned by
`review_report_composition`.

## Error Handling and Exception Path Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral error handling and exception path review.

For C#, also check at least the following:

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

## Time and Culture Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral time and culture review.

For C#, also check at least the following:

- `DateTime.Now` / `DateTime.UtcNow` mixing in the same comparison, storage,
  or scheduling flow, and `DateTimeKind` inconsistency across boundaries
- culture-sensitive `ToString()` / `Parse()` / string comparison used in
  protocol, persistence, serialization, or interchange contexts that require
  the invariant culture
- format strings and decimal separators that change meaning under a
  non-default culture

## State and Determinism Boundary Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral state and determinism boundary review.

For C#, also check at least the following:

- mutable state in `static`, singleton, cached, `ThreadLocal<T>`,
  `AsyncLocal<T>`, scoped-service, or background-worker storage that can leak
  across unrelated requests, jobs, tests, tenants, or agents
- state machines whose transition order is not explicit enough for retry,
  replay, compensation, or deterministic test execution
- helper methods that look like pure validation, classification, parsing, or
  mapping but mutate shared state, emit messages, write storage, or update
  process-global context
- non-idempotent transition methods called from retry, replay, duplicate
  message, or parallel-worker paths without visible guards

## Uncertainty and Escalation Path Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral uncertainty and escalation path review.

For C#, also check at least the following:

- `TryParse`, `TryGet`, classifier, matcher, rules-engine, and model-output
  branches whose failure or low-confidence path silently returns a normal
  default
- nullable, optional, default enum, empty-string, empty-collection, or
  fallback-object paths that hide an unknown result instead of surfacing
  `needs_confirmation`, controlled rejection, or handoff
- LLM or external-decision outputs represented as plain DTOs without an
  explicit confidence, status, or unsupported-value disposition when the
  downstream decision requires it
- exception-to-default paths around parsing, classification, model-output
  handling, or schema conversion

## Contract and Schema Resilience Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral contract and schema resilience review.

For C#, also check at least the following:

- `System.Text.Json`, Newtonsoft.Json, MessagePack, protobuf, or custom
  serializer settings for unknown members, missing members, enum values,
  nullability, polymorphism, and versioned DTOs
- deserialization exceptions that crash work outside a controlled boundary
  instead of producing reject, quarantine, retry, `unknown`, or handoff
  outcomes
- lenient deserialization that ignores fields required for routing,
  authorization, idempotency, audit, billing, or compliance
- mapping layers that lose original payload, schema version, source identity,
  or unsupported-field evidence needed for diagnostics

## Traceability and Context Propagation Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral traceability and context propagation review.

For C#, also check at least the following:

- `Activity.Current`, logging scopes, correlation ids, `AsyncLocal<T>`,
  `CancellationToken`, tenant/user/source identity, and attempt metadata across
  async calls, background tasks, timers, queue handlers, and fire-and-forget
  work
- detached `Task.Run`, event handlers, hosted services, channels, and callback
  paths that lose source context or failure attribution
- propagation that leaks sensitive context across unrelated requests, workers,
  agents, tests, or tenants
- structured logging and telemetry that cannot connect source read, state
  transition, external call, retry, failure, and final disposition

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
