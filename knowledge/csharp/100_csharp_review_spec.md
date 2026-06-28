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
