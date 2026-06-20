<!-- xid: 5301B897BA41 -->
<a id="xid-5301B897BA41"></a>

# Structure-Analysis Determinism Tiers

This page classifies the [Dotnet change analysis viewpoints](120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)
by **how mechanically extractable each one is**, so the deterministic subset can
be served by Roslyn-backed tooling instead of LLM "principle" inference, and the
genuine judgment residue stays explicitly with the AI.

It is the structure-analysis counterpart of
[C# error-policy detection determinism tiers](131_csharp_error_policy_locator_tiers.md#xid-D1F4A7C3E209)
and reuses that page's tier legend and bindings unchanged. It does **not** add
new viewpoints; the viewpoints live in
[120](120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201) and the relation
substrate in [Structure graph as TM coverage backstop](160_structure_graph_tm_backstop.md#xid-163AD9936979).

## Tier Legend (reused from 131)

| Tier | Meaning | Implementation |
|---|---|---|
| **T1** | pure lexical / symbol match | regex / token grep |
| **T2** | structural / flow / cross-file analysis | Roslyn |
| **T3** | semantic / intent judgment | not mechanizable — stays with AI + per-case approval |

The same binding applies: **a tier rates finding the candidate; turning a
candidate into a finding is always judgment.** A deterministic extractor emits a
`file:line` / DocID candidate, never a verdict, and never an auto-fail gate
(see 131's *Boundary* and *Detected-range-only* rules). Coverage is reported
detected-range-only: an extractor states what it scanned and never reports
"no hits = compliant".

## Per-Viewpoint Classification

`Deterministic facts` is the part an extractor can produce; `T3 residue` is what
must stay judgment. Tooling: ✅ tooled · ◑ substrate present (graph/inventory) ·
○ extractable, not yet tooled.

| # | Viewpoint | Deterministic facts (tier) | Mechanism | T3 residue | Tooling |
|---|---|---|---|---|---|
| 1 | Solution/project structure | solutions, projects, assemblies, project refs, TFMs (T1/T2) | MSBuild workspace | "boundary as the unit of change" | ◑ |
| 2 | Responsibility split | call fan-in/out, field read/write ownership, type membership (T2) | call/ref edges | responsibility label, name-behavior mismatch, duplicated ownership | ◑ (call/`uses` fan-in/out + `writes` ownership; generic field-reads excluded by design — see note; label T3) |
| 3 | Entry points | base-type subclasses, route/`[ApiController]` attrs, `IHostedService` impls, `MapGet` sites, `Main` (T2) | inherits/implements + attrs + invocations | convention-named handlers, dynamic registration | ◑ |
| 4 | Dependency direction | project refs, type-reference edges, calls/inherits/implements (T1/T2) | edges | "is the direction intentional" | ✅ (`calls`/`inherits`/`implements`/`uses`/`uses-project`; intent T3) |
| 5 | DI registration & lifetimes | `Add{Singleton,Scoped,Transient}<,>` + type args + lifetime, captive deps (lifetime × ctor type), `new` bypass (T2) | invocation pattern + graph computation | custom/wrapped containers, intentional bypass | ✅ (registration/lifetime/captive/`new`-bypass; custom containers T3) |
| 6 | Pipeline structure & order | ordered `app.UseX()` / registration sequence (T2) | syntactic order | what the order controls, framework-semantics on custom pipelines | ✅ (Use* order; semantics T3) |
| 7 | Convention-based discovery | scan **call-site present** (`GetTypes()`, `Scan(...)`) (T2) | invocation locator | runtime resolution targets, rename sensitivity | ◑ (scan-site present; targets T3) |
| 8 | Security boundary placement | `[Authorize]`/`[AllowAnonymous]` enumeration, auth middleware, (entry ∖ protected = unprotected) (T2) | attrs + set difference | exposure intent, custom-convention enforcement | ◑ |
| 9 | Configuration boundary | literal config keys, `Bind`/`Configure<T>`/`IOptions<T>` sites (T2) | uses-name + invocations | dynamically built keys, env-switching intent | ✅ (keys + binding sites; dynamic keys T3) |
| 10 | Build-config behavior | `#if` directives, multi-TFM, MSBuild conditions (T1/T2) | trivia + csproj/XML | which configs the change must be verified against | ✅ (`#if` + active preproc symbols + declared TFMs; MSBuild conditions ○) |
| 11 | API/integration boundary | controller/endpoint, HttpClient/typed-client types, serialization config (`JsonNamingPolicy`, `[JsonPropertyName]`) (T2) | attrs + types + invocations | wire-compat rules | ◑ |
| 12 | Data boundary | `DbSet<T>`, `DbContext`/`Migration` subclasses, `[Table/Column/Key]`, transaction sites (T2) | types + attrs + invocations | dynamic SQL, mapping-contract meaning | ◑ (attrs + transaction + `DbSet` tooled; `DbContext`/migration via inherits ○) |
| 13 | Error handling contract | Exception hierarchy, catch/throw/wrap-throw sites (T2) | analyzer pipeline | contract meaning, what may cross a boundary | ✅ |
| 14 | Logging policy | `ILogger` call-sites + level, sink registration (T2) | invocation locator | PII / sensitive-data risk | ✅ (sites + level; PII T3) |
| 15 | Attribute usage | every attribute application + folded values (ctor/named/return/param/assembly) (T1/T2) | attribute inventory | which framework behavior activates, activation condition | ✅ |
| 16 | Concurrency & timing | async signatures, lock/`SemaphoreSlim`/`Interlocked` sites, static mutable fields, `CancellationToken` propagation, async-void (T2) | signatures + invocations | timing/ordering correctness, duplicate-execution risk | ✅ (async/CT/static-state/lock/`Interlocked`/`Monitor` via D, async-void via G; `SemaphoreSlim` ○) |
| 17 | Performance-sensitive paths | (weak) in-loop allocation, sync-over-async | — | hotness / frequency | ○ |
| 18 | Resource efficiency | `IDisposable`/`IAsyncDisposable` impls, `using` sites, dispose-throw, CA2000/2213 (T2) | implements + SARIF | ownership intent | ◑ |
| 19 | Test boundary | test methods (`[Fact]`/`[Test]`/`[TestMethod]`), test→SUT `calls`+`dispatches-to` reachability, no-reach = gap (T2) | attrs + graph traversal | edge-case adequacy; reach ≠ assertion; delegate/reflection invocation unseen | ◑ |
| 20 | Change impact & uncertainty | seed traversal candidates, fan-in/out/centrality, multi-seed convergence (T2) | graph traversal (160) | final inclusion verdict, non-mechanical ripple | ◑ |

**16 of 20 viewpoints carry a deterministic substrate.** Only #2 (responsibility)
and #17 (performance) are essentially T3; the rest are "candidate by machine,
disposition by judgment".

## Consolidation: the Deterministic Build Units

The same Roslyn primitive backs many viewpoints, so the build units are fewer
than the viewpoints. This is what to implement, not 20 separate extractors:

| Unit | Primitive | Backs viewpoints | Status |
|---|---|---|---|
| **A. Type-relation edges** | inherits/implements + type-reference `uses` + `uses-project` | 3, 4, 8, 12, 13, 18 | ✅ |
| **B. Attribute inventory** | `ISymbol.GetAttributes()`, constant-folded values | 3, 6, 8, 11, 12, 15, 19 | ✅ |
| **C. Invocation-pattern locators** | specific call shapes: DI `Add*<,>`, `ILogger.Log*`, config `Bind`/`GetSection`, `BeginTransaction`, scan-sites, builder `Use*` order | 5, 6, 7, 9, 11, 12, 14 | ✅ (DI, logging, config, pipeline, discovery, transaction) |
| **D. Signature/declaration facts** | async/`Task`, `CancellationToken`, static mutable fields, `DbSet<T>`, `#if` trivia, TFMs, lock/`Interlocked` sites | 10, 12, 16 | ✅ |
| **E. Literal coupling** | identifier-like string literals (config keys, topics, schema) | 9, 12 | ✅ (uses-name) |
| **F. Call-graph traversal & metrics** | fan-in/out/centrality, **test→SUT reachability**, seed TM | 2, 19, 20 | ◑ |
| **G. Analyzer SARIF** | catch/throw/async-void/dispose + CA rules | 13, 16 (part), 18 | ✅ |

## Do NOT Mechanize as Verdicts (T3)

Same idiom as 131's *Do NOT Mechanize* list — flagging these as violations is
pure noise:

- responsibility labels, name-behavior mismatch (#2)
- "is it intentional" for any bypass, exposure, or dependency direction
- runtime resolution targets of convention-based discovery (#7)
- dynamically built config keys and dynamic SQL (#9, #12 — see 160 limits)
- framework-semantics assumptions on custom / wrapped pipelines (#6)
- PII / sensitive-data risk (#14) and performance hotness (#17)
- the final TM inclusion verdict (#20)

The extractors raise recall and reproducibility; the disposition stays in the
skill with per-case proposal and approval (never bulk auto-apply), consistent
with [Roslyn analyzer quality-check applicability](150_roslyn_analyzer_quality_check_applicability.md#xid-A1B243BF7D5D)
and [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).

## Tooling Handoff

Deterministic extractors backing this classification:

- `tools/structure_graph` — relation graph including `contains` / `declares` /
  `calls` / `inherits` / `implements` / `dispatches-to` (interface & override
  dynamic dispatch) / `uses` (type-reference) / `uses-project` / `writes`
  (member→field state ownership) / `uses-name` edges (units A, E, F substrate)
  and, with `--attributes`, the attribute inventory (unit B). Same Roslyn front-end.
- `tools/structure_graph_report.py` — seedless coupling and dependency-direction
  views: call fan-in/out, name coupling, project dependencies, `uses`
  type-dependency fan-in/out, and `writes` field-ownership (units A, F metrics).
- `tools/where_seed_traversal.py` — per-change Where impacted-boundary traversal
  from a seed over `calls`/`uses`/`dispatches-to`, backward (impact) or forward
  (touches), with high-fan-in `transit` damping (unit F, viewpoint #20). The cut
  is computed per change, never stored; candidate-only.
- `tools/attribute_inventory_report.py` — on-demand attribute listing/filter (unit B).
- `tools/test_coverage_reach.py` — test→SUT reachability over `calls` +
  `dispatches-to` (so interface/virtual calls cross to their implementations);
  emits coverage-gap candidates for viewpoint #19 (unit F). Consumes the graph
  plus the attribute inventory; candidate-only (reflection / delegate invocation
  still unseen, and reach is not assertion).
- `tools/structure_graph --di` + `tools/di_registration_report.py` — DI
  registration inventory (service / implementation / lifetime / ctor deps),
  captive-dependency candidates, and (with `--graph`) container-bypass candidates
  for viewpoint #5 (unit C). Candidate-only (factory regs hide the impl; custom
  containers can differ).
- `tools/structure_graph --invocations` + `tools/invocation_facts_report.py` —
  logging / config-binding / pipeline / discovery / transaction invocation facts
  for viewpoints #14, #9, #6, #7, #12 (unit C). Pipeline order is reconstructed
  per enclosing member from source position. Candidate-only (no PII assessment, no
  dynamic-key resolution, written order ≠ runtime meaning, scan resolution target
  is spec-out).
- `tools/structure_graph --decl` + `tools/declaration_facts_report.py` — async /
  CancellationToken / static-mutable-state / `DbSet<T>` / lock-`Interlocked`-`Monitor`
  sites / `#if` / per-project preprocessor symbols and declared TFMs for viewpoints
  #16, #12, #10 (unit D). Candidate-only (missing CT is not a defect, static state
  is not automatically a race, `#if` symbols are variants not the target).
- `tools/collect_analyzer_sarif.py` → `sarif_to_locator.py` → `error_policy_audit.py`
  — the analyzer pipeline (unit G), per [131](131_csharp_error_policy_locator_tiers.md#xid-D1F4A7C3E209).

Units A, B, C, D, F, G are now tooled and validated against a real codebase
(Ksql.Linq, ~6.2k nodes / ~13.6k edges). The deterministic substrate is
essentially complete for its purpose.

## Scope ceiling: prior information for design, at member granularity

This substrate exists to serve as **prior information (briefing) for the design
step**, not as a conclusion. That role fixes its ceiling:

- **Granularity is member / boundary, not statement.** Design asks where a change
  goes, what the boundaries are, and where it ripples — all member/type-level
  questions. Intra-procedural **control flow (CFG) and statement-level program
  slicing are deliberately out of scope**: they are a finer granularity that
  serves verification and change-design *detail*, and are better read on demand
  by a human/LLM than materialized into this substrate.
- **`writes` is kept; a generic field-`reads` edge is deliberately not added.**
  The reads that matter for a design boundary are *boundary* reads — where data
  enters across a seam — and those are already captured: configuration via
  `uses-name` literal keys and the `config` invocation facts, and persistence via
  `DbSet<T>` and `transaction` facts. Internal method-reads-field edges are
  high-volume, low-design-signal noise; `writes` alone gives the state-ownership
  signal design needs.
- **The requirement layer is out of reach by nature.** The change requirement,
  intent, and difference are not in code (see [160](160_structure_graph_tm_backstop.md#xid-163AD9936979));
  no amount of extraction reaches them. The substrate is requirement-independent
  prior information; the seed/USDM mapping that activates it stays with the
  human/LLM.

Remaining residues are genuinely optional and small: `SemaphoreSlim` sites,
MSBuild-condition parsing and per-TFM `#if` variants (#10, bounded by the
one-compilation-per-csproj model), and `DbContext`/migration subclass surfacing
(#12, already derivable from `inherits`). Viewpoints #2 (responsibility label) and
#17 (performance) stay essentially T3 by nature — they are judgment, not extraction.

## Where-step decision: pack is not a standard backstop (A/B outcome)

A controlled A/B at two codebase scales
([2026-06-21 deterministic pack vs LLM](../../work/reports/2026-06-21_deterministic_pack_vs_llm_ab_test.md))
showed the pack gives **no token or accuracy gain** over an LLM using `grep`/`rg` for
**text-greppable impact discovery** (type names, method names, construction sites,
references). Cause: `grep` returns a type's full reference surface in one pass at any
scale, and an LLM classifies the impact pattern without reading most files; even the
pack-assisted arm fell back to `grep` for the authoritative set. Token cost was tie
(+4%) on the large codebase and worse (+49%) on the small one.

Decision: **do not run the structure pack as a standard Where backstop** in
`dotnet_change_analysis`. The standard Where path is grep-first → small representative
reads → LLM impact-pattern classification → review-boundary / must-change-boundary
split. The deterministic pack is retained for **semantic-inventory questions `grep`
answers poorly**: custom-attribute values (constant folding), DI lifetime /
captive-dependency, async-without-CancellationToken, `IDisposable` ownership,
reflection / convention binding, and transitive impact with no textual footprint
(the one impact case `grep` cannot follow). Whether the pack helps on those grep-weak
questions is not yet measured and is the open follow-up.
