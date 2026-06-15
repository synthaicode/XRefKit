<!-- xid: C7A1E94D3B62 -->
<a id="xid-C7A1E94D3B62"></a>

# CSharp Error-Policy: External Analyzer Rule Map

This page maps existing C# Roslyn analyzer diagnostics to the locator taxonomy
in
[Determinism Tiers (Locator Extraction)](131_csharp_error_policy_locator_tiers.md#xid-D1F4A7C3E209)
and the detection spec in
[CSharp Error Policy Detection Patterns](130_csharp_error_policy_detection_patterns.md#xid-C0DBC37E2A13).

It exists because most of the 131 First Batch is already implemented by mature,
Roslyn-semantic analyzers. Rather than hand-build heuristics, the locator layer
should **delegate detection to these analyzers where coverage is verified, and
normalize their output into the 131 Output Contract**. This table is the
canonical map the normalizer reads.

## Boundary (binding, inherited from 131)

- **Mapping does not change verdict semantics.** A mapped analyzer diagnostic
  becomes a 131 *candidate*, never a finding. The normalizer must drop analyzer
  `severity` and set `confidence: candidate`, `judgment_status: unset`.
- **No auto-fail gate.** A mapped hit never fails the build on its own.
- **Scope must still be declared.** The normalizer attaches the 131 scan-scope
  declaration (included/excluded generated/test, enabled rules) around the run.
- **`partial` / `context-limited` rules are not grounds to delete a custom
  locator.** A backing rule replaces a custom locator only when its coverage is
  verified `full` against the exact 131 shape.
- **A locator id may have several backing rules.** The normalizer deduplicates
  by `(file, line, locator_id)` and records which `external_rule_id`s fired.

## Verification Legend

- `verified` — ID and behavior confirmed from a primary source on 2026-06-15
  (see Sources).
- `name-known` — ID/title known but the rule page was not fetched this session;
  confirm exact trigger before relying on it.

As of 2026-06-15 all First Batch backing rules are `verified`. Residual
sub-arm uncertainties are noted inline (e.g. S4462's `GetAwaiter().GetResult()`
arm is unconfirmed; CA1849 covers it instead).

## Locator → Spec Reference

| locator_id | source_pattern_id | tier |
|---|---|---|
| `cs.err.throw_variable_rethrow` | `130:throw-sites/variable-rethrow` | T2 |
| `cs.err.empty_catch` | `130:catch-blocks/empty-catch` | T2 |
| `cs.err.async_void_non_event` | `130:dotnet-specific/async-void` | T2 |
| `cs.err.sync_wait_result` | `130:dotnet-specific/sync-wait` | T1/T2 |
| `cs.err.sync_wait_getawaiter_getresult` | `130:dotnet-specific/sync-wait` | T1 |
| `cs.err.fire_and_forget` | `130:dotnet-specific/fire-and-forget` | T2 |

## First Batch Rule Map

| locator_id | external_tool | external_rule_id | coverage | verification | normalizer_action |
|---|---|---|---|---|---|
| `cs.err.throw_variable_rethrow` | .NET NetAnalyzers | **CA2200** | full | verified | map directly |
| `cs.err.throw_variable_rethrow` | SonarAnalyzer.CSharp | **S3445** | full | verified | map directly (dedupe with CA2200) |
| `cs.err.empty_catch` | SonarAnalyzer.CSharp | S2486 | partial (generic `Exception` only; comment exempts) | verified | signal only; do not suppress custom locator |
| `cs.err.empty_catch` | SonarAnalyzer.CSharp | S108 | partial (empty block; comment exempts) | verified | signal only; do not suppress custom locator |
| `cs.err.empty_catch` | Roslynator | RCS1075 | partial (`System.Exception` only; flags comment-only) | verified | signal only; closest on comment-only, still not 131 shape |
| `cs.err.async_void_non_event` | AsyncFixer | **AsyncFixer03** | near-full | verified | map; verify event-handler exclusion vs target frameworks |
| `cs.err.async_void_non_event` | SonarAnalyzer.CSharp | S3168 | near-full | verified | map; known event-handler FP gaps (UWP args, TimerCallback) |
| `cs.err.sync_wait_result` | AsyncFixer | **AsyncFixer02** | context-limited full | verified | map; keep external rule note |
| `cs.err.sync_wait_result` | Meziantou.Analyzer | **MA0042** / **MA0045** | context-limited full | verified | map; keep external rule note |
| `cs.err.sync_wait_result` | SonarAnalyzer.CSharp | S4462 | partial (`.Result`/`.Wait()`; `GetResult()` unconfirmed) | verified | map; keep external rule note |
| `cs.err.sync_wait_result` | .NET NetAnalyzers | CA1849 | context-limited (async context; default-off in .NET 10) | verified | map; explicit profile required |
| `cs.err.sync_wait_getawaiter_getresult` | .NET NetAnalyzers | **CA1849** | context-limited (async context) | verified | map; CA1849 explicitly covers `GetAwaiter().GetResult()` |
| `cs.err.fire_and_forget` | C# compiler | **CS4014** | partial (in-async only) | verified | map only when compiler diagnostics are collected |
| `cs.err.fire_and_forget` | AsyncFixer | **AsyncFixer04** | narrow partial: unawaited async call inside `using` block | verified | map; narrow — do not treat as general fire-and-forget |
| `cs.err.fire_and_forget` | VS Threading | **VSTHRD110** | partial (unobserved async result; broader contexts than CS4014) | verified | map; advisory/warning |

Note: `AsyncFixer03` covers `async void` methods/delegates and is mapped to
`cs.err.async_void_non_event`, **not** to `cs.err.fire_and_forget`. The two are
distinct locator ids in 131; do not merge them even though an `async void` is a
common fire-and-forget accident.

## Coverage Notes

- **`cs.err.throw_variable_rethrow` is fully delegated to CA2200.** CA2200 is a
  built-in .NET analyzer rule that confirms the thrown symbol is the caught
  exception via semantic analysis. Its default enablement depends on the target
  SDK / analysis level, so the normalizer should not rely on default severity
  and should explicitly enable or collect it when needed. **The hand-built
  `python_scrub_scope_heuristic` locator for #1 is redundant and should be
  retired in favor of CA2200** (it is a strictly weaker lexical approximation).
  The normalizer must run analyzers with an explicit ruleset / `.editorconfig`
  profile for locator collection, instead of relying on SDK default analyzer
  enablement.
- **`cs.err.empty_catch` remains a custom locator** (verified). No backing rule
  matches the 131 shape: **S108 and S2486 exempt comment-only blocks** (a
  comment makes the block "non-empty"), and **S2486 only fires on a generic
  `Exception` catch**. Roslynator **RCS1075 does flag comment-only** catches —
  the closest match — but only for `catch (System.Exception)`, missing bare
  `catch {}` and other typed empty catches, and emits no intentional-marker
  note. So external rules are additional signals only; the custom locator stays
  until a rule is verified `full` against golden samples.
- **`async_void_non_event` is near-full.** AsyncFixer03 already excludes event
  handlers (the exemption 131 listed as a custom requirement), but
  event-handler detection depends on type / naming / UI-framework conventions,
  so verify the exclusion against the target frameworks before treating it as
  complete. Sonar S3168 (verified) targets the same pattern with the same
  event-handler exemption and has documented event-handler false positives
  (UWP event args, `TimerCallback`), which is why this stays near-full.
- **`sync_wait_*` is context-limited full.** MA0042 reports a blocking call when
  the enclosing method is already async or can become async without changing its
  return type; MA0045 extends this to cases requiring a signature change. This
  is "full within an async-migration policy", **not necessarily all synchronous
  waits** — if 131 wants every blocking `.Result`/`.Wait()` as a candidate
  regardless of context, MA0042/MA0045 alone will miss some. For
  `GetAwaiter().GetResult()`, **CA1849 is the verified backing rule** — its
  cause text explicitly lists `Task.Wait()`, `Task<T>.Result`, and
  `Task.GetAwaiter().GetResult()` — but it only fires inside a Task-returning
  (async) method and is default-off in .NET 10, so it must be enabled via the
  collection profile. S4462 was confirmed for `.Result`/`.Wait()` but its
  `GetResult()` arm is unconfirmed.
- **`fire_and_forget`**: CS4014 covers unawaited tasks *inside async methods*
  only; AsyncFixer04 is narrow (unawaited async call in a `using` block);
  VSTHRD110 extends to more contexts. Treat as partial until context coverage is
  confirmed against the target codebase.

## Not Covered — Genuine Custom Residual

These 130 patterns have weak or no coverage in the mapped tools and remain
candidates for a small custom Roslyn locator (build only on demand):

- `cs.err.empty_catch` to the exact 131 shape (comment-only + marker note)
- custom exception **thrown but never caught anywhere** (cross-reference)
- `IOptions` validation **without `ValidateOnStart()`**
- `ExceptionDispatchInfo.Capture(...).Throw()` **inventory** (a policy record,
  not a defect)

## Normalized Record (analyzer hit -> 131 Output Contract)

```json
{
  "external_tool": "Meziantou.Analyzer",
  "external_rule_id": "MA0042",
  "locator_id": "cs.err.sync_wait_result",
  "source_pattern_id": "130:dotnet-specific/sync-wait",
  "tier": "T1/T2",
  "file": "src/Foo.cs",
  "line": 42,
  "column": 13,
  "detection_method": "roslyn:Meziantou.Analyzer",
  "confidence": "candidate",
  "judgment_status": "unset",
  "scope_id": "scan-...",
  "notes": "context-limited: async-migration policy"
}
```

`severity` from the analyzer is intentionally dropped. `detection_method`
records the backing analyzer so a downstream consumer can distinguish a real
Roslyn-semantic hit from any remaining heuristic locator.

## Integration Dependency

These analyzers run inside a Roslyn compilation, so this path adds a
`dotnet build` (+ analyzer NuGet) dependency the pure-Python locator did not
have; the target repository must build. The normalizer consumes analyzer output
via SARIF or MSBuild diagnostics.

Licensing / distribution must be checked per analyzer:

- **Meziantou.Analyzer**: MIT
- **AsyncFixer**: Apache-2.0
- **.NET NetAnalyzers**: built into the .NET analyzer ecosystem
- **SonarAnalyzer.CSharp**: available as a NuGet analyzer package, but **not
  treated as permissive**; review SonarSource license terms before
  redistribution or bundling. Running it against the user's own project is one
  thing; bundling it into `fm audit` is a separate licensing question.

## Analyzer Collection Profile

The normalizer should not rely on a repository's existing analyzer severity
configuration. For locator collection it should run with an explicit profile
that enables the mapped rules needed for candidate extraction.

The profile is separate from the user's build policy:

- Build severity is ignored.
- Suppressed diagnostics may be recorded separately if available.
- Analyzer hits are normalized to `confidence: candidate`.
- Missing analyzer execution is reported as a scope / collection error, not as
  "no hits".

## Conclusion / Policy

- Actively use the verified rules — **CA2200, AsyncFixer03, MA0042/MA0045** (and
  AsyncFixer02) — as the primary detection for their locator ids.
- **External analyzer rules are not a complete substitute for the locator
  contract.** The normalizer drops `severity`, converts every hit to a
  `candidate`, and attaches scope.
- A rule whose coverage is `partial` or `context-limited` is **not** grounds to
  delete the corresponding custom locator; it is an additional signal only.
- `cs.err.empty_catch` and the items under "Not Covered" stay custom until a
  backing rule is verified `full` against golden samples.

## Sources

- CA2200 — Microsoft Learn: `learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca2200`
- AsyncFixer diagnostics — `github.com/semihokur/AsyncFixer`
- Meziantou MA0042 / MA0045 — `github.com/meziantou/Meziantou.Analyzer/blob/main/docs/Rules/`
- SonarAnalyzer C# (S3445 / S4462 / S3168) — `github.com/SonarSource/sonar-dotnet`

Verified 2026-06-15.
