<!-- xid: C0DBC37E2A13 -->
<a id="xid-C0DBC37E2A13"></a>

# CSharp Error Policy Detection Patterns

This page defines the detection patterns, record schema, category taxonomy,
and disposition taxonomy for extracting the existing de-facto error policy
from C# source. It is the factual basis for the
`csharp_error_policy_extraction` Skill.

The target of extraction is policy as implemented behavior, not policy as
documented intent. Where the two disagree, the implemented behavior is the
finding.

## Explicit Error Handling: Inventory Targets

### Throw Sites

| Pattern | What to record |
|------|------|
| `throw new <Exception>(...)` | thrown type, message/data construction, guard condition that triggers it |
| `throw;` (bare rethrow) | stack trace preserved — record as `rethrow_preserving` |
| `throw ex;` (variable rethrow) | stack trace reset — record as `rethrow_resetting`; the distinction is part of the de-facto policy, not a style note |
| `ExceptionDispatchInfo.Capture(...).Throw()` | stack trace preserved across context boundaries — typically marshaling from sync-over-async or deferred rethrow |

### Catch Blocks

| Pattern | What to record |
|------|------|
| `catch (Exception)` / bare `catch` | catch-all; record what escapes it (nothing, or rethrow) |
| typed catch (`catch (IOException)`) | caught type set and ordering |
| exception filter (`catch (X e) when (...)`) | filter condition; filters that never observe (logging filters returning false) are policy-relevant |
| empty catch body | swallow; record whether intentional marker (comment, suppression) exists |
| log-only catch | swallow with trace; record log level and whether error detail survives |
| catch + wrap + throw | translation point; record source type, target type, inner-exception preservation, and the local rule that decides the target type |

### Custom Exception Types

- Enumerate custom exception definitions and their inheritance hierarchy.
- Record which layers throw each type and which layers catch it; a custom
  type thrown but never caught anywhere in the codebase is a finding (its
  consumer is external or missing).
- Record constructor conventions (error codes, context payloads) as the
  representation convention.

### Global Handlers

- ASP.NET Core: exception-handling middleware (`UseExceptionHandler`,
  `IExceptionHandler`, exception filters in MVC), problem-details mapping.
- `AppDomain.CurrentDomain.UnhandledException`: observer only — the process
  still dies; record whether code treats it as recovery (it is not).
- `TaskScheduler.UnobservedTaskException`: last-chance observer for
  fire-and-forget failures; record whether `SetObserved()` is called
  (suppression) and whether anything is logged.
- Generic host: `IHostApplicationLifetime` usage on fatal paths.

## C#/.NET-Specific Detection Paths

### async void

- Exceptions escape to the `SynchronizationContext` (or crash the process
  without one); they bypass every caller-side catch.
- Record every `async void` method that is not a UI event handler; for UI
  event handlers, record whether a top-level try/catch exists inside.

### Fire-and-Forget Tasks

- Unawaited `Task` results (`_ = SomethingAsync()`, bare invocation
  statements, `Task.Run` without await/continuation): the exception is
  unobserved until finalization, then surfaces only via
  `TaskScheduler.UnobservedTaskException`.
- Record the launch site, whether any continuation observes faults
  (`ContinueWith` with fault handling, a wrapper like `SafeFireAndForget`),
  and the consequence of silent loss.

### Sync-over-Async Blocking

- `.Result`, `.Wait()`: exceptions arrive wrapped in `AggregateException`;
  catch blocks typed for the original exception silently stop matching.
- `GetAwaiter().GetResult()`: no AggregateException wrapping — record the
  two forms separately because their catch compatibility differs.
- Record each site and whether downstream catches expect the wrapped or
  unwrapped form.

### DI Container Construction (Composition Root)

- Throws in `Program.cs` / `Startup` / `ServiceCollection` registration code.
- Throws inside factory delegates (`AddSingleton(sp => ...)`): these fire at
  first resolution, not at startup — the timing difference is policy.
- `IOptions` validation: `ValidateDataAnnotations` / `Validate(...)` with or
  without `ValidateOnStart()`. Without `ValidateOnStart`, invalid
  configuration surfaces at first options access in steady state, not at
  startup.
- `IHostedService.StartAsync` failure: default host behavior aborts startup.
  For `BackgroundService.ExecuteAsync`, behavior depends on
  `BackgroundServiceExceptionBehavior` (since .NET 6 the default `StopHost`
  stops the host; earlier behavior was silent task failure) — record which
  runtime and setting actually apply; mark `unknown` if not determinable.

### Dispose Paths

- Exception handling inside `Dispose` / `DisposeAsync`: throws here can mask
  the original exception when triggered during stack unwinding.
- Record empty catches and intentional suppression inside disposal, and
  `using` patterns around resources whose disposal can throw.

## Omission Policies (Error Absorbed by Convention)

These represent errors without exceptions. They are part of the de-facto
policy and must be inventoried where detectable:

| Pattern | What to record |
|------|------|
| null return on failure | caller-side null handling; whether failure cause is recoverable from the call site |
| `Try*` pattern (`bool` + `out`) | whether failure detail is available anywhere; call sites that ignore the bool |
| default-value / empty-collection fallback | the fallback site, the masked failure, and downstream behavior on the fallback value |
| bool-only success flag | where failure detail is discarded; whether any log compensates |

### Non-Exhaustiveness Rule

Omission policies are behavioral conventions, not syntactic markers. A
static throw/catch scan cannot enumerate them completely:

- Record the search patterns actually used and the scope they covered.
- Never claim exhaustive coverage of omission policies; the report must
  state detected-range-only explicitly and connect it to the coverage-limits
  section.

## Per-Item Record Schema

Every inventory item carries:

- file path and line number
- owning module / namespace
- error kind (what condition triggers it)
- behavior (what happens: throw type, swallow, fallback value, log)
- propagation terminus (how far it travels, what stops it: a catch, a
  middleware, process exit, silent loss)
- logging presence (level, content, whether the cause survives)
- intent status: `confirmed` (explicit evidence of intent: comment, test,
  doc) / `inferred` (consistent with surrounding convention) /
  `contradictory` (conflicts with nearby evidence)
- basis for the intent status (the evidence path)

## Error Category Taxonomy

| Category | Definition |
|------|------|
| configuration | missing/invalid settings, DI resolution failure, unsatisfied startup precondition |
| transient | network, external service, resource failures that a retry could recover |
| invariant_violation | internal bug, must-not-reach state, programming error |
| external_input | validity violation in user input or data from external systems |
| unclassified | does not fit above — keep with the judgment material attached; do not force-fit |

## Disposition Taxonomy

| Disposition | Definition |
|------|------|
| fail-fast | stop the process (or refuse startup) |
| propagate | let it travel to a higher layer unchanged |
| translate | wrap/convert and rethrow as a different type |
| retry | reattempt, with or without backoff |
| degrade | continue with reduced function (fallback value, skip feature) |
| swallow | absorb with no trace |
| log-only | absorb with a log record only |

## Category x Disposition Matrix Rule

- Build the matrix: rows = categories, columns = dispositions.
- Each cell carries the item count and at least one representative example
  (file:line).
- The majority disposition per category is presented as the de-facto policy
  candidate — a candidate, not a verdict; minority cells feed contradiction
  detection.

## DI Startup Throw Triage Axes

Throws in DI setup must additionally be classified on three axes:

| Axis | Values |
|------|------|
| occurrence time | startup / first-resolution / steady-state |
| recovery responsibility | process itself (retry/degrade) / orchestrator (restart policy) / operator (manual fix) |
| blast radius | single process / co-hosted components dragged down |

A startup fail-fast under an orchestrator restart policy and a steady-state
fail-fast in a shared host are different policies even when the code shape
is identical.

## Contradiction Record Schema

For each same-category, different-disposition group:

- (a) the involved item pair or group (file:line each)
- (b) each item's observed behavior
- (c) whether placement or processing characteristics explain the difference
  (entry point vs core, batch vs request path, hot path) — if explainable,
  note as a possible conditional rule rather than a contradiction
- (d) the judgment material a human arbiter would need (intended SLA,
  operational ownership, restart policy, data-loss tolerance)

## Minimum Coverage Limits

The report must declare at least these undetectable areas:

- omission policies are non-exhaustive (see Non-Exhaustiveness Rule)
- dynamic exception paths: reflection invocation (`TargetInvocationException`
  wrapping), delegate/event indirection, expression-tree or generated code
- third-party library internal swallowing: behavior inside packages without
  source is invisible; only the boundary behavior is observable
- additional limits found during the run are appended, never silently dropped
