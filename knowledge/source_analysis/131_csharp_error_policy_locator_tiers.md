<!-- xid: D1F4A7C3E209 -->
<a id="xid-D1F4A7C3E209"></a>

# CSharp Error-Policy Detection: Determinism Tiers (Locator Extraction)

This page classifies the "what to detect" patterns in
[CSharp Error Policy Detection Patterns](130_csharp_error_policy_detection_patterns.md#xid-C0DBC37E2A13)
by **how mechanically detectable they are**, so that the deterministically
detectable subset can be implemented as a locator pass (a future `fm audit`
layer or a pre-pass that feeds `csharp_error_policy_extraction` /
`csharp_review`).

It is the bridge between a prose detection spec and an executable check. It
does **not** add new detection criteria; the criteria live in
[130](130_csharp_error_policy_detection_patterns.md#xid-C0DBC37E2A13) and the
[C# review spec](../csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA).

## ID Conventions

Two id namespaces are kept separate so spec and implementation can evolve
independently:

- **source pattern** — the detection criterion, owned by 130 (spec-derived).
- **locator id** (`cs.err.*`) — a concrete deterministic detector, owned by
  this page / the locator implementation. One source pattern may produce
  several locator ids (for example a broad catch splits into bare,
  `Exception`-typed, and filtered variants so reviewers can triage them
  apart).

A locator id is stable output contract: once emitted, downstream consumers key
on it, so rename via deprecation, not edit-in-place.

## Boundary (binding)

- **Locator, not verdict.** A deterministic match produces a `file:line`
  *candidate*, never a confirmed finding. The disposition (130 category x
  disposition matrix, intent status `confirmed`/`inferred`/`contradictory`)
  stays in the judgment layer.
- **No auto-fix, no auto-fail gate.** The locator surfaces candidates only.
  Confirmation and any change follow the existing per-case proposal and
  approval rule (never bulk auto-apply) — same idiom as
  [test synchronization patterns](../csharp/120_csharp_test_synchronization_patterns.md#xid-4314A1A73CAF).
- **Detected-range-only.** A locator pass must declare the patterns and scope
  it covered and must never report "no hits = compliant". This carries 130's
  Non-Exhaustiveness Rule forward: omission policies are behavioral, not
  syntactic, and are out of scope for mechanical detection.
- **Scope must be declared, not assumed.** Error-policy results change meaning
  with scope; the locator must emit a scope declaration (see the Scan Scope
  Declaration section below). "What was scanned" is as much part of the audit
  result as "what was found".
- **Grow from past pain, not from the catalog.** The catalog is the menu.
  Mechanize the patterns that have produced a real verified finding first;
  do not point-fire every theoretical pattern at once (false-positive noise
  is the failure mode).

## Tier Legend

| Tier | Meaning | Implementation | Role |
|---|---|---|---|
| **T1** | pure lexical / symbol match; the syntactic shape is unambiguous | regex / token grep | deterministic locator |
| **T1 locate / T2 refine** | a lexical match finds candidates but over-matches; a semantic pass is needed to suppress false positives | regex first, Roslyn confirms | deterministic locator, two-stage |
| **T2** | needs structural, flow, or cross-file analysis | Roslyn analyzer | deterministic locator (higher build cost) |
| **T3** | requires semantic / intent judgment | not mechanizable | stays with AI + per-case approval |

"Tier" rates **finding the candidate**. Turning a candidate into a finding is
always judgment, regardless of tier.

### T1 lexical-match limitations (binding for any regex/token locator)

A T1 regex over C# source is lossy and must be treated as candidate-only:

- **comments and string literals must be excluded** — `// throw new ...` and
  `var s = "throw new Exception"` are not throw sites; a raw line grep will
  flag them.
- **multi-line forms are missed unless tokenized** — `throw new MyException(\n
  message);` will not match a single-line pattern.
- **qualified and generic names widen the pattern** — `throw new
  System.InvalidOperationException()`, `throw new global::MyException()`,
  `throw new MyException<T>()` are missed by `throw new \w+`.
- **the matched line is the candidate, not the verdict** — column/snippet are
  reported for the judgment layer, never auto-classified.

When a T1 locator would need to grow toward handling these cases, that is the
signal to promote it to T2 (Roslyn) instead of escalating the regex. A wider
throw-new regex such as
`throw\s+new\s+([A-Za-z_]\w*::)?([A-Za-z_]\w*\.)*[A-Za-z_]\w*(<[^>]+>)?\s*\(`
is acceptable as an interim T1-locate, but at that complexity Roslyn is the
safer home.

## Throw Sites

| Locator ID | 130 pattern | Tier | Locator method | What stays judgment (T3) |
|---|---|---|---|---|
| `cs.err.throw_new` | `throw new <Exception>(...)` | T1 locate (lossy) | regex; misses qualified/generic names — candidate to promote to T2 | guard condition, message/data construction, whether the policy is correct |
| `cs.err.throw_bare_rethrow` | `throw;` (bare rethrow) | T1 | regex `throw\s*;` | classification is mechanical (`rethrow_preserving`); none |
| `cs.err.throw_variable_rethrow` | `throw ex;` (variable rethrow) | T2 | **delegated to CA2200** (see [132](132_csharp_error_policy_analyzer_rule_map.md#xid-C7A1E94D3B62)); custom heuristic retired | the reset itself is the finding; confirm the thrown symbol is the catch variable |
| `cs.err.throw_edi_capture` | `ExceptionDispatchInfo.Capture(...).Throw()` | T1 | symbol match | marshaling reason / context |

## Catch Blocks

Broad catch is split into separate locator ids; the shapes mean slightly
different things and reviewers triage them apart.

| Locator ID | 130 pattern | Tier | Locator method | What stays judgment (T3) |
|---|---|---|---|---|
| `cs.err.catch_bare` | bare `catch` (catch-all) | T1 | regex `catch\s*\{` | what actually escapes it |
| `cs.err.catch_system_exception` | `catch (Exception)` / `catch (System.Exception ex)` | T1 locate | regex; Roslyn confirms the type binds to `System.Exception` | whether the broad catch is justified here |
| `cs.err.catch_broad_with_filter` | `catch (Exception ...) when (...)` | T1 locate | regex for filter presence on a broad catch | "never observes" (logging filter returning false) — needs expression evaluation |
| `cs.err.catch_typed_ordering` | typed catch ordering | T2 | Roslyn: catch-clause order | broad-before-narrow significance |
| `cs.err.empty_catch` | empty catch body | T2 | Roslyn: empty block | presence/absence of intentional marker, whether the swallow is acceptable |
| `cs.err.catch_log_only` | log-only catch | T2 | Roslyn: body is a single log call | whether error detail survives, continuation acceptability |
| `cs.err.catch_wrap_throw` | catch + wrap + throw | T2 | Roslyn: `throw new` inside catch | inner-exception preservation, the local rule that picks the target type |

## Custom Exception Types

| Locator ID | 130 pattern | Tier | Locator method | What stays judgment (T3) |
|---|---|---|---|---|
| `cs.err.custom_exception_def` | custom exception definitions + hierarchy | T2 | Roslyn: types deriving from `Exception` | — (inventory) |
| `cs.err.custom_exception_unhandled` | thrown but never caught anywhere | T2 (project-wide) | Roslyn cross-reference / symbol search | "consumer external or missing" interpretation |
| — | constructor conventions (codes, payloads) | T3 | — | representation-convention judgment |

## C#/.NET-Specific Paths

| Locator ID | 130 pattern | Tier | Locator method | What stays judgment (T3) |
|---|---|---|---|---|
| `cs.err.async_void_non_event` | `async void` (non-UI-handler) | T2 | Roslyn: `async void` methods minus event-handler signatures | UI-handler exclusion, top-level try/catch presence |
| `cs.err.fire_and_forget` | fire-and-forget (`_ = FooAsync()`, bare invocation, `Task.Run` without await) | T2 | Roslyn: unawaited Task flow | whether a continuation observes faults |
| `cs.err.sync_wait_result` | `.Result`, `.Wait()` | T1 locate / T2 refine | regex first; Roslyn confirms the receiver is `Task`/`Task<T>` (`.Result` also matches non-Task `Result` properties) | `AggregateException`-wrap catch compatibility |
| `cs.err.sync_wait_getawaiter_getresult` | `GetAwaiter().GetResult()` | T1 | symbol/chain match | unwrapped-form catch compatibility |
| `cs.err.ioptions_no_validateonstart` | `IOptions` validation without `ValidateOnStart()` | T2 | Roslyn: `Validate*`/`ValidateDataAnnotations` present and `ValidateOnStart` absent on the same chain | timing-policy meaning |
| `cs.err.di_composition_root_throw` | DI throws in `Program.cs`/`Startup`/factory delegates | T2 locate | locate throws in composition-root files and factory lambdas | occurrence-time / recovery-responsibility / blast-radius triage (130 DI axes) |
| `cs.err.hosted_service_startasync` | `IHostedService.StartAsync` / `BackgroundServiceExceptionBehavior` | T3 | — | runtime- and setting-dependent; 130 says record actual setting or mark `unknown` |
| `cs.err.dispose_throw` | Dispose / DisposeAsync throws, empty catch in disposal | T2 | Roslyn: within disposal methods | mask-original-exception risk |

## Do NOT Mechanize As Verdicts

These are deliberately left to the judgment layer; a locator that flags them
as violations is pure noise.

- **Omission policies** (null-return-on-failure, default/empty-collection
  fallback, bool-only success flag): 130 marks them behavioral conventions,
  not syntactic markers, and explicitly non-exhaustive. `Try*` signatures are
  T2-locatable (`cs.err.try_pattern`), but "call sites that ignore the bool"
  and "failure detail availability" remain judgment.
- **Derivation-style signals** from
  [code constraint derivation](../packs/constraint-derivation/190_code_constraint_derivation_catalog.md#xid-A1D4E8C93B71)
  such as `Single()` / `FirstOrDefault()` / magic values: the code shape is
  deterministic but the *derived concern* is a confirmation hypothesis, not a
  violation. Mechanizing them as gates drowns the signal.

## Scan Scope Declaration

Error-policy locator output is only usable as an audit result if it states
where it looked. Every run must declare:

- included projects / files
- excluded generated files (`*.g.cs`, `*.Designer.cs`, generated folders,
  EF migrations) and whether the exclusion was applied
- whether test / sample / benchmark projects were included
- which locator ids were enabled
- unresolved parser / semantic-analysis errors that left regions unscanned

Generated and test code change the meaning of a hit (a broad catch in a
benchmark harness is not the same finding as one on a request path). The scope
decision is made and recorded before the scan, not inferred afterward.

## Locator Output Contract

Each locator hit emits:

- `locator_id`
- `source_pattern_id` (the 130 criterion)
- `file`
- `line`
- `column`
- `snippet`
- `tier`
- `detection_method` (e.g. `regex`, `roslyn`)
- `confidence: candidate` (always — there is no other value)
- `judgment_status: unset` (filled by the judgment layer)
- `scope_id` / `scan_id`
- `notes` — present when a T1/locate match is lossy (e.g. "regex match, Task
  receiver not confirmed")

The locator must NOT emit:

- final severity
- a violation verdict
- a remediation instruction
- an auto-fix patch

This shape lets the locator emit the 130 per-item record skeleton with
`intent status` left unset, so `csharp_error_policy_extraction` /
`csharp_review` fill the judgment fields without reformatting.

## First Batch (recommended implementation order)

Mechanize in this order. The ordering is by **review value per unit of
false-positive noise**, not by raw usefulness:

1. ~~`cs.err.throw_variable_rethrow` (`throw ex;`)~~ — **retired**: delegated to
   the built-in analyzer CA2200, which does true semantic rethrow analysis. The
   custom lexical heuristic was removed from `tools/error_policy_locator.py`;
   the throw path now runs through the SARIF pipeline. See
   [132](132_csharp_error_policy_analyzer_rule_map.md#xid-C7A1E94D3B62).
2. `cs.err.empty_catch` — high value, low count, unambiguous; **stays custom**
   (no analyzer matches the comment-only + marker-note shape). T2.
3. `cs.err.async_void_non_event` — high value; the event-handler exclusion is
   the only tuning needed. T2.
4. `cs.err.sync_wait_result` + `cs.err.sync_wait_getawaiter_getresult` —
   high value; `.Result` needs the T2 receiver refinement to stay clean.
5. `cs.err.fire_and_forget` — useful but highest implementation difficulty and
   false-positive tuning; doing it first would muddy the locator's own
   evaluation with noise, so it lands last.

`throw ex;` and empty catch first because their candidate sets are small and
self-explanatory, which makes them ideal for validating the locator pipeline
and the output contract before noisier patterns are added.

## Handoff

- Consumer: `csharp_error_policy_extraction` (today) and a future `fm audit`
  locator pass.
- Open question for the owner: whether the locator runs as a `csharp_review`
  pre-pass (raises recall, judgment stays in the AI skill) or as a standalone
  `fm audit` candidate report. Either way it never auto-fails the build.
