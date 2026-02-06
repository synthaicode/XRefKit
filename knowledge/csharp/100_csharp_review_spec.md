<!-- xid: 30E6A4F6F3AA -->
<a id="xid-30E6A4F6F3AA"></a>

# C# Review Spec (Manual, non-Roslyn scope)

This fragment defines the canonical review scope for manual C# checks.

## Scope Boundary

- Primary boundary: exclude concerns that Roslyn diagnostics already detect.
- This spec covers review signals that are often semantic, environment-dependent, or cross-file/project.

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
