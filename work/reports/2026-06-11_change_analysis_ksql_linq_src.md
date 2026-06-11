# .NET Change Analysis Note
<!-- skill: dotnet_change_analysis | xid-ref: D94E3B3A7C11 | viewpoints-ref: 2E7B5A1FD201 -->

## Request Summary

- request: Baseline structure analysis — extract local rules and de-facto responsibility split; no specific change request
- target path: work/external/Ksql.Linq/src
- scope: Single project (Ksql.Linq.csproj), all source directories under src/
- generated_at: 2026-06-11

## Scope Targets

| Item | State | Evidence | Notes |
|------|------|------|------|
| solution | done | `work/external/Ksql.Linq/Ksql.Linq.sln` | Single solution |
| project | done | `src/Ksql.Linq.csproj` — targets net8.0;net10.0 | Main library + CLI sub-project `src/Ksql.Linq.Cli/` compiled separately |
| feature/module | done | Directories: Application, Cache, Configuration, Context, Core, EntitySets, Events, Extensions, Incidents, Infrastructure, Mapping, Messaging, Query, Runtime, SchemaRegistryTools, SerDes, Window | Folders are module boundaries; namespace flattening documented (EntitySets README) |

---

## Structure And Responsibility Split

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| major layers and responsibilities are identified | done | See layer summary below | Any cross-layer addition risks displacing responsibility | — |
| de-facto responsibilities are derived from behavior evidence | done | `KsqlContext.Lifecycle.cs`, `EventSet.cs`, `SchemaRegistrar.cs`, `UnifiedPipelineOrchestrator.cs` | — | — |
| name-behavior mismatches are recorded | done | Finding 1: `KsqlContextBuilder` in `Application/` is a fluent builder for `KsqlContextOptions`, not a context factory proper — it can construct a context via reflection (`BuildContext<T>`), but its primary product is `KsqlContextOptions` | A rename or split would break calling code expecting `BuildContext<T>` | Implicit design — no design doc names this pattern |
| duplicated rule ownership is checked | done | Topic-name derivation rule exists in two places: `CoreExtensions.GetKafkaTopicName()` (type.Name.ToLowerInvariant()) and `ModelBuilder.CreateEntityModelFromType` which calls the same — consistent, single canonical call. DLQ-topic override in `KsqlContext.Lifecycle` and `KsqlContext.Model` — same `_dslOptions.DlqTopicName` source. No duplication found for the main naming rule. | — | — |
| dependency direction is identified | done | Application → Core (Abstractions, Modeling) → Infrastructure (Kafka, Ksql, KsqlDb, Admin) → Messaging (Producers, Consumers) → Mapping; Query namespace is standalone (Pipeline, Analysis, DSL); Context (KsqlContext partials) orchestrates all of these | Inversion risk: `EventSet.cs` in Ksql.Linq namespace reaches back into `KsqlContext` cast with `context is KsqlContext kctx` — tight coupling at this boundary | — |
| extension points are identified | done | `OnModelCreating(IModelBuilder)` virtual override; `CreateEntitySet<T>` virtual; `SkipSchemaRegistration` and `IsDesignTime` virtual booleans; `ISchemaRegistrar`, `IStartupFillService`, `IRowMonitorCoordinator`, `ITopicAdmin` injected via `ApplyDependencies(KsqlContextDependencies)` | Any change adding a new lifecycle hook needs to fit the `ApplyDependencies` pattern or add a new virtual | The `KsqlContextDependencies` injection point is partially populated (comment in code: "keep for later phases") — some dependency slots are not used yet |

**Layer summary (derived from behavior evidence):**

| Layer | De-facto responsibility | Files |
|------|------|------|
| Context (KsqlContext partials) | Lifecycle orchestration: model building, startup I/O sequencing, disposal; entity-set factory | `Context/KsqlContext.*.cs` |
| Query / Pipeline | KSQL DDL and DML generation, query model DSL, unified pipeline orchestration for tumbling/hopping windows | `Query/` |
| Schema / SchemaRegistrar | Startup: Avro schema registration to Schema Registry, DDL execution sequencing, ksqlDB warmup | `Runtime/Schema/SchemaRegistrar.cs` |
| Messaging | Kafka producer/consumer lifecycle; DLQ forwarding; manual commit management | `Messaging/` |
| Mapping | Avro <-> POCO schema mapping registry; specific record code generation | `Mapping/` |
| Core | Abstractions, attributes, modeling DSL, retry policy, DLQ client/guard, async helpers | `Core/` |
| Cache | Streamiz-backed table cache; cache registry and extensions | `Cache/` |
| Infrastructure | Low-level Kafka admin, ksqlDB HTTP client, executor, wait/polling helpers | `Infrastructure/` |
| Runtime | Row monitors, window aggregation, scheduling, startup fill, period/time-bucket helpers | `Runtime/`, `Window/` |
| Application | Public builder and options type for context construction | `Application/` |
| Configuration | Option classes binding from `appsettings.json` under `KsqlDsl` section | `Configuration/` |

---

## Entry Points And Dependency Direction

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| startup path is identified | done | `KsqlContext(IConfiguration, ...)` constructor chain → `InitializeCore()` → either blocking `RunStartupAsync(...).GetAwaiter().GetResult()` (default) or sets `_startupPending = true` when `DeferStartup = true` → `StartAsync()` for deferred path (`KsqlContext.Lifecycle.cs:327`) | Local rule: fail-fast is deliberately in the constructor (blocking init). `DeferStartup` is the opt-out. Both paths share `RunStartupAsync`. | IMPLICIT rule: Default path blocks constructor thread on async I/O; no compiler or analyzer enforcement prevents misuse of the deferred path |
| request, batch, and event entry points are identified | done | Consumer: `EventSet<T>.ForEachAsync(...)` → `ConsumeAsync()` → `KafkaConsumerManager.ConsumeAsync<T>`; Producer: `EventSet<T>.AddAsync()` → `SendEntityAsync()` → `KafkaProducerManager`; Pull query: `KsqlContext.PullRowsAsync()` / `QueryRowsAsync()`; Programmatic: `KsqlContext.ExecuteStatementAsync()` for raw DDL/DML | Any new entry point must respect `EnsureStarted()` guard before touching entity sets | — |
| main call chain is identified | done | `KsqlContext.Set<T>()` → `EnsureStarted()` guard → `GetOrCreateEntityModel<T>()` → `CreateEntitySet<T>(entityModel)` → returns `EventSetWithServices<T>` (or `ReadCachedEntitySet<T>` for tables with cache enabled) | Changing the entity-set factory path (e.g., adding a decorator) requires overriding `CreateEntitySet<T>` virtual | — |

**Local rule: fail-fast constructor (documented/implicit)**
- Status: **deliberate design, documented by `DeferStartup` XML comment** (`KsqlContext.Lifecycle.cs:24-30`)
- The default constructor blocks on `RunStartupAsync(CancellationToken.None).GetAwaiter().GetResult()` at line 327
- `DeferStartup = true` moves startup I/O to an explicit `StartAsync()` call
- `EnsureStarted()` guard at line 181 enforces that deferred startup completes before entity sets are accessed
- This is an **extracted local rule**: treat blocking constructor init as deliberate fail-fast, not as an async defect candidate

---

## DI Registration And Lifetimes

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| registration sites and lifetimes are identified | done | No DI container in the library itself. All services are constructed directly inside `KsqlContext.InitializeCore()` with `new` (e.g., `new KafkaProducerManager(...)`, `new KafkaConsumerManager(...)`, `new DlqProducer(...)`, `new KsqlDbClient(...)`, `new KafkaAdminService(...)`) — `KsqlContext` owns all lifetimes. `Lazy<ISchemaRegistryClient>` defers client creation until first schema use (`KsqlContext.Lifecycle.cs:55,275`) | A change adding a new service must be injected via `ApplyDependencies(KsqlContextDependencies)` or hard-wired inside `InitializeCore`. No container to register with. | — |
| captive-dependency risks are checked | done | Not applicable in the traditional DI sense — all dependencies are created by `KsqlContext` itself and share its lifetime. `ConcurrentDictionary` statics in `KsqlContextCacheExtensions` (lines 37-40) hold `KafkaStream` and store references at static scope; these outlive individual context instances. | Risk: static dictionaries in `KsqlContextCacheExtensions` are a shared singleton even when multiple `KsqlContext` instances exist (test isolation concern) | UNK-001 |
| hosted services and background registrations are identified | done | `_msRefreshTask` via `Task.Run()` in `StartDailyRefresh()` (`KsqlContext.Lifecycle.cs:852`); `HubStreamBridgeController.Start()` fires monitor task; `RowMonitorCoordinator` starts background monitoring; `WindowAggregator` runs `SweepLoopAsync` via `Task.Run()` (line 83). All are owned and cancelled by `KsqlContext._hubBridgeCts` or the respective `CancellationTokenSource`. | Any new background task must register with `_hubBridgeCts` to be cancelled on `StopAsync()` / `Dispose()` | IMPLICIT rule: no registry of background tasks; knowledge of all running tasks lives only in `KsqlContext` field declarations and `HubStreamBridgeController` dictionary |

---

## Pipeline Structure And Order

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| local pipelines and their stages are identified | done | (1) Startup pipeline: warmup → schema registration → simple DDL (with retry) → query DDL (with retry) → cache registration → Kafka connectivity check — code order in `SchemaRegistrar.RegisterAndMaterializeAsync()` (`Runtime/Schema/SchemaRegistrar.cs`). (2) Unified pipeline for tumbling/hopping: `UnifiedPipelineOrchestrator.ExecuteAsync()` → `DerivedTumblingPipeline.RunAsync()` → post-execution `IUnifiedPipelineStage` chain. (3) Consumer pipeline: `ForEachAsync` → `ConsumeAsync` → `RetryPolicy` → DLQ forwarding. | Stage insertion in startup pipeline requires editing `SchemaRegistrar.RegisterAndMaterializeAsync`. Unified pipeline stages are injectable via `IUnifiedPipelineStage` list. | — |
| the local ordering rule and its source (extracted or implicit) are recorded | done | Startup pipeline: **code order in `SchemaRegistrar.RegisterAndMaterializeAsync()`** — implicit, no comment or test enforces the sequence. Unified pipeline post-stages: **construction-order of `IUnifiedPipelineStage` list** passed to `UnifiedPipelineOrchestrator` ctor — implicit. Consumer error handling: error action checked before DLQ decision — code order in `EventSet.ForEachAsync`. | All three ordering rules are implicit (no test asserts sequence). A change reordering startup phases could silently break DDL → cache dependency. | UNK-002: No test or documentation asserts startup phase order |
| order-dependent behavior risks are checked | done | Startup pipeline: warmup (`SHOW TOPICS`) must precede DDL execution — if reordered, DDL will fail. Schema registration (Phase 1) must precede DDL (Phase 2) — Avro schema required before ksqlDB CREATE. Cache registration comes after DDL so ksqlDB table topics are known. | Any change touching startup sequence should verify all four phases remain in order | — |

---

## Convention-Based Discovery

| Check Item | State | Evidence | change impact | Unknown / Follow-up |
|------|------|------|------|------|
| convention-based wiring points are identified | done | (1) `EventSet<>` property scanning: `InitializeEventSetProperties()` in `KsqlContext.Model.cs:60-79` scans the concrete context subclass for public writable properties typed `EventSet<>` — reflection-based, no assembly scanning beyond the current type. (2) Topic name default: `CoreExtensions.GetKafkaTopicName()` returns `type.Name.ToLowerInvariant()` — a class rename silently changes the Kafka topic. (3) `_1s_rows` suffix convention: `IsRowsRole()` checks for `_1s_rows` suffix in topic/identifier — implicit naming convention governs row monitor wiring. | A rename of an entity POCO silently changes its Kafka topic name unless `[KsqlTopic("...")]` is applied. A rename of a property on the context subclass from `EventSet<T>` type drops automatic initialization. | — |
| the matching convention and scan scope are extracted | done | `EventSet<>` scan: single reflection call over concrete type's public instance properties; condition `p.CanWrite && p.PropertyType.IsGenericType && p.PropertyType.GetGenericTypeDefinition() == typeof(EventSet<>)`. Scan is NOT recursive into base types (only `GetType()`, not walking to `KsqlContext`). | Any property on a base class between the app context and `KsqlContext` will not be auto-discovered by this scan | IMPLICIT |
| rename-and-move sensitivity is recorded | done | (a) POCO class rename → topic name changes (no compiler error). (b) POCO property rename does not break topic, but may break Avro schema field mapping if the schema was already registered. (c) `EventSet<T>` context property rename has no runtime impact (only used for initialization). (d) Moving POCO to different namespace has no topic impact. | High: entity class renames carry silent Kafka topic change risk in deployments with existing data | — |

---

## Configuration Boundary

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| configuration sources are identified | done | `appsettings.json` (or any `IConfiguration`) bound via `configuration.GetSection(sectionName).Bind(_dslOptions)` in `KsqlContext.Lifecycle.cs:122`. Default section name: `KsqlDsl`. `DefaultValueBinder.ApplyDefaults(_dslOptions)` applies post-bind defaults. | Changing the section name requires passing the new name to the constructor overload taking `sectionName` | IMPLICIT: no validation that required keys (BootstrapServers, SchemaRegistry.Url) are present after binding — unset values silently get defaults |
| options binding and consumers are identified | done | `KsqlDslOptions` is the root options type (`Configuration/KsqlDslOptions.cs`). Sub-objects: `Common` (bootstrap servers, client ID), `SchemaRegistry`, `KsqlServer`, `Topics` (per-topic producer/consumer/creation), `Entities` (per-entity overrides), `DlqOptions`, `Fill`, `Decimals`. Consumed by: `KsqlContext` directly, `KafkaProducerManager`, `KafkaConsumerManager`, `DlqGuard`, `SchemaRegistrar` (via adapter methods). | A new configuration option must be added to `KsqlDslOptions` and threaded through adapter methods or injected directly into the constructing service | Options object mutated by `ResolveEntityConfigurations` (clears `_dslOptions.Entities` and re-populates) — options are not immutable after init |
| environment-dependent behavior and feature toggles are identified | done | `DeferStartup` (bool) — toggles blocking vs deferred init. `SkipSchemaRegistration` (virtual bool on context) — test/design-time toggle. `IsDesignTime` (virtual bool) — skips Kafka/ksqlDB wiring entirely. `AdjustReplicationFactorToBrokerCount` (bool) — dev cluster accommodation. No external feature-flag system observed; all toggles are in-process. | No runtime flag switching; all toggles are set at construction time | — |

---

## Build Configuration Behavior

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| conditional compilation symbols and gated behavior are identified | done | `Ksql.Linq.csproj` — no `#if` conditional compilation symbols found in source files examined. `StrictPublicApi` MSBuild property gates RS0016/RS0017 analyzer enforcement (csproj lines 72-75). `UseStreamizPackages` MSBuild property (default `true`) switches between NuGet packages and local project references for Streamiz. | A change that adds a public API must pass CI with `-p:StrictPublicApi=true` | Roslyn baseline: **baseline_unavailable** — build is out of scope for this read-only structure analysis (external snapshot) |
| multi-target and MSBuild-condition variants are identified | done | `TargetFrameworks: net8.0;net10.0`. Per-TFM implementation splits: not observed in source — no `#if NET8_0` blocks found in examined files. Streamiz package versions set via `StreamizCoreVersion` and `StreamizSerdesAvroVersion` properties. | A change must be verified against both net8.0 and net10.0 target frameworks | TFM-specific behavior differences (if any) from Streamiz library are not visible from source alone — unknown |
| configurations requiring verification for this change are recorded | done | For any change: (a) Release/net8.0 and Release/net10.0; (b) `UseStreamizPackages=true` (NuGet) and `=false` (local project reference) configurations; (c) `StrictPublicApi=true` if public API surface is modified | — | — |

---

## API, Database, And External Integration Boundary

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| API boundary is identified | done | Library API: `KsqlContext.Set<T>()`, `EventSet<T>.AddAsync()`, `ForEachAsync()`, `ToListAsync()`, `Commit()`. Pull query helpers: `PullRowsAsync()`, `PullCountAsync()`, `ExecuteStatementAsync()`. No HTTP server — this is a client library. `PublicAPI.Shipped.txt` / `PublicAPI.Unshipped.txt` files track public surface via RS0016/RS0017 analyzers | Any new public member must be declared in `PublicAPI.Unshipped.txt` under strict mode | — |
| database boundary is identified | done | No relational database. Data is in Kafka topics (Avro serialized). Streamiz-backed local RocksDB state store used for table cache (`TableCacheRegistry`, `KsqlContextCacheExtensions`). Schema Registry for Avro schema management. | A change adding a new serialization format must extend the Mapping layer and Avro schema registration | RocksDB state dir path configurable via `StoreName`/`BaseDirectory` in `KsqlDslOptions` entities settings |
| external service or messaging boundary is identified | done | (1) Kafka cluster — Confluent.Kafka v2.12.0, bootstrap servers from `KsqlDsl:Common:BootstrapServers`. (2) Confluent Schema Registry — `Confluent.SchemaRegistry` v2.12.0, URL from `KsqlDsl:SchemaRegistry:Url`. (3) ksqlDB HTTP API — REST client `KsqlDbClient` to URL from `KsqlDsl:KsqlDbUrl` or derived from SchemaRegistry host on port 8088. (4) Streamiz streaming engine (Kafka Streams for .NET) — local in-process. Wire format: Avro for key and value; tombstone-safe wrapper via `TombstoneSafeSerDes`. Windowed keys via `FixedTimeWindowedAvroSerDes` and `WindowedAvroKeyDeserializer`. | A change touching serialization (new type, new field) must align Avro schema registration, KSQL DDL, and Streamiz SerDes — three separate boundary points | UNK-003: `KsqlContextCacheExtensions` uses `GetAwaiter().GetResult()` when fetching schema metadata (`lines 1220, 1309`), which is a sync-over-async call inside the cache extension; risk depends on calling context |

**De-facto responsibility split for the three main rule kinds:**

| Rule kind | De-facto home | Files |
|------|------|------|
| Query building (KSQL DDL/DML generation) | `Query/Pipeline/` — `DDLQueryGenerator`, `DMLQueryGenerator`, `JoinQueryGenerator`; DSL in `Query/Dsl/KsqlQueryModel`; builders in `Query/Builders/` | `src/Query/` |
| Schema mapping | `Mapping/` — `MappingRegistry`, `KeyValueTypeMapping`, `SpecificRecordGenerator`; Avro schema utilities in `SchemaRegistryTools/` | `src/Mapping/`, `src/SchemaRegistryTools/` |
| Runtime/messaging | `Messaging/` (producers/consumers/DLQ) + `Infrastructure/` (admin, executor, wait clients) + `Runtime/` (monitors, scheduling, cache) | `src/Messaging/`, `src/Infrastructure/`, `src/Runtime/` |

---

## Error Handling Contract

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| error representation conventions are identified | done | Two parallel systems: (1) `ErrorHandlingPolicy` / `ErrorHandlingContext` in `Core/Abstractions/` — governs per-message consumer error handling (Skip, Retry, DLQ). (2) Direct exception propagation from `InitializeCore()` — startup errors throw to caller (fail-fast). No custom exception hierarchy beyond `WindowAggregationException` and `UnifiedPipelineException`. `KsqlDbResponse(bool IsSuccess, string Message)` as result type for DDL/DML responses. | A change adding error conditions must decide: throw (fail-fast path) or ErrorHandlingPolicy (runtime consumer path). Mixing the two channels without documentation creates a third implicit contract. | — |
| translation and propagation points are identified | done | Startup: exceptions logged and rethrown (`Lifecycle.cs:332-334`). DDL retry: `SchemaRegistrar.IsRetryableKsqlError()` classifies ksqlDB error messages by substring match — implicit list of retryable strings (`SchemaRegistrar.cs:274-284`). DLQ: `DlqGuard.ShouldSend()` decides per exception type. Consumer: handler exceptions trigger retry or DLQ based on policy and `DlqGuard`. | Adding a new retryable error condition requires editing `IsRetryableKsqlError` — string matching is the detection mechanism | IMPLICIT rule: retryable error classification is a hardcoded string-match list with no external configuration |
| retry and compensation conventions are identified | done | `Core/Retry/RetryPolicy` — Fixed/Linear/Exponential backoff; used by DDL execution (Exponential, max 5 attempts, initial 1s) and consumer error handling (Fixed, caller-configured). `DlqOptions.MaxPerSecond` via `SimpleRateLimiter` controls DLQ forwarding rate. No saga/compensation pattern observed. | A change raising a new retryable condition must supply an `IsRetryable` predicate or extend `IsRetryableKsqlError` | — |

---

## Security Boundary Placement

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| authentication and authorization enforcement points | not_applicable | Library is a Kafka/ksqlDB client; there is no HTTP server, no ASP.NET middleware, no auth schemes. Kafka SASL/SSL credentials are passed via `KsqlDsl:Common` configuration (SecurityProtocol, Sasl* keys per README). No authorization policy layer. | N/A for security boundary viewpoint in the traditional sense | — |
| unprotected entry paths | not_applicable | All entry points are local API calls by the consuming application; no externally exposed HTTP endpoint exists in this library | — | — |
| security-review handoff items | done | Schema Registry URL and Kafka bootstrap servers are read from `IConfiguration` without validation that they use TLS. Potential risk: misconfigured plaintext connections in production. Routing to security-review handoff list (not assessed here). | — | Security handoff: verify TLS enforcement for Schema Registry and Kafka connections is caller responsibility, not library-enforced |

---

## Logging Policy

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| logging points are identified | done | `ILogger` injected from `ILoggerFactory` parameter at construction (`KsqlContext.Lifecycle.cs:267`). Log sites: startup (`LogError` on init failure), DDL execution (`LogInformation` for each DDL statement), consumer events (`LogInformation` on each consumed record), hub bridge lifecycle, DLQ forwarding events. Total: 287 log call sites across 35 files (pattern search). | A new code path should emit at least one log event at the appropriate level at entry/exit points matching existing conventions | — |
| sensitive-data exposure risk is checked | done | `ConfigLoggingExtensions.cs` exists — suggests configuration values may be logged. Consumer logs include topic name, offset, timestamp — entity payload values are NOT logged in `ForEachAsync` (only metadata). DLQ envelope includes error message and stack trace fragments (length-limited by `ErrorMessageMaxLength`, `StackTraceMaxLength`). | A change adding payload logging must be reviewed for PII exposure | UNK-004: `ConfigLoggingExtensions.cs` not fully read — unknown whether it logs sensitive config values (bootstrap server credentials) |
| monitoring or operations impact | done | `RuntimeEventBus` / `IRuntimeEventSink` publish structured events (DDL phase, query.run, dlq.enqueue) — optional, only active when a sink is registered. `WindowAggregatorMetrics` tracks emitted/failed/late/duplicate counts via `Interlocked`. `IncidentBus`/`LoggerIncidentSink` for domain-level incidents. | A change to startup or DDL execution sequence should verify `RuntimeEventBus` events still fire in correct order | — |

---

## Attribute Usage

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| standard and custom attributes are identified | done | Custom attributes (all in `Core/Attributes/`): `[KsqlTopic(name, partitions, replicationFactor)]` on class — topic name and partition config; `[KsqlTable]` on class — marks entity as Table vs Stream; `[KsqlKey(order)]` on property — key column declaration; `[KsqlTimestamp]` on property — timestamp column; `[KsqlDecimal(precision, scale)]` on property — decimal precision override; `[KsqlIgnore]` on property — exclude from schema. | Any new metadata that must influence Avro schema or KSQL DDL must be expressed as a new attribute or extend an existing one | — |
| attribute definition origin is identified | done | All custom attributes are defined in `Ksql.Linq.Core.Attributes` namespace (`src/Core/Attributes/`). No external attribute sources observed (no DataAnnotations, no EF Core attributes consumed as behavior drivers). | — | — |
| consuming mechanism and activation condition | done | `[KsqlTopic]`: consumed in `KsqlContext.Model.cs:CreateEntityModelFromType()` via `entityType.GetCustomAttribute<KsqlTopicAttribute>()` — sets `model.TopicName`, `model.Partitions`, `model.ReplicationFactor`. `[KsqlTable]`: same method — calls `model.SetStreamTableType(Table)`. `[KsqlKey]`: filters properties ordered by `Attr.Order`, assigned to `model.KeyProperties`. `[KsqlTimestamp]`: sets `model.TimeKey`. `[KsqlDecimal]`: consumed in `DecimalPrecisionConfig.Configure()` during `InitializeCore`. `[KsqlIgnore]`: consumed in mapping/schema generation (consuming mechanism confirmed in `Mapping/` — not fully traced here). | Activation: all attributes are read once during model initialization in the constructor — no lazy re-evaluation | `[KsqlIgnore]` consuming mechanism not fully confirmed from examined files — marked unknown for this attribute only |

---

## Concurrency And Execution Timing

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| async and background execution paths are identified | done | Background: `_msRefreshTask` (daily market schedule refresh via `Task.Run`); `HubStreamBridgeController` monitors (via `IRowMonitorController.Start(token)`); `WindowAggregator.SweepLoopAsync` (via `Task.Run`). Blocking async: `RunStartupAsync.GetAwaiter().GetResult()` in constructor (default path); `ToListAsync().GetAwaiter().GetResult()` in `EventSet.Map()` sync overload; `GetAwaiter().GetResult()` in `KsqlContextCacheExtensions` (lines 1220, 1309); `MarketScheduleProvider.InitializeAsync.GetAwaiter().GetResult()` in `InitializeMarketScheduleIfNeededAdapter`. | Multiple sync-over-async call sites outside the constructor are candidates for deadlock under certain synchronization contexts (e.g., ASP.NET classic, WPF) — route to `csharp_review` handoff | UNK-005: `KsqlContext.Schema.cs:176-182` contains additional `GetAwaiter().GetResult()` calls in schema registration path — not fully traced for deadlock risk |
| shared state and locking points are identified | done | `_entityModels: ConcurrentDictionary<Type, EntityModel>` — thread-safe reads; writes gated by startup sequence. `_hubBridgeControllers: ConcurrentDictionary<string, HubStreamBridgeController>` — thread-safe add/remove. `_enforceEarliestTopics: ConcurrentDictionary<string, bool>`. `_startupGate: SemaphoreSlim(1,1)` — startup serialization. `volatile bool _startupPending`. Static `ConcurrentDictionary` in `KsqlContextCacheExtensions` — shared across all context instances. `WindowManager._sync: object` — lock-guarded append/sweep operations. `ManualCommitManager._lock: object`. | Changes adding per-entity state must use `ConcurrentDictionary` to match existing pattern; direct field writes are not safe after startup | — |
| transaction and retry boundaries are identified | done | No distributed transactions. Kafka offsets committed manually (when `autoCommit=false`) via `ManualCommitManager.Commit(entity)`. DLQ rate-limited by `SimpleRateLimiter`. DDL retry via `RetryPolicy` (exponential backoff, configurable attempts/delay). Consumer-level retry via `ErrorHandlingPolicy`. | A change to consumer flow must decide autocommit vs manual commit contract explicitly | — |

---

## Performance And Resource Efficiency

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| hot paths and heavy I/O are identified | done | Hot path: `EventSet<T>.ForEachAsync` continuous Kafka consumption loop — each message: deserialize Avro, invoke `RetryPolicy.ExecuteAsync`, optional DLQ send. `WindowAggregator.SweepLoopAsync` periodic sweep across all window managers. Schema Registry calls at startup (blocking `GetAwaiter().GetResult()` for cache warmup). | A change adding per-message work inside `ForEachAsync` multiplies cost by message volume | — |
| resource lifetime and ownership are identified | done | `KsqlContext` owns: `KafkaProducerManager` (IDisposable), `KafkaConsumerManager` (IDisposable), `KafkaAdminService` (IDisposable), `TableCacheRegistry` (IDisposable), `CachedSchemaRegistryClient` (IDisposable), `KsqlDbClient` (IDisposable), `SemaphoreSlim _startupGate` (IDisposable). All disposed in `Dispose(bool)` and `DisposeAsyncCore()`. `Lazy<ISchemaRegistryClient>` only disposed if value was created. `WindowAggregator<,,>` implements `IAsyncDisposable` — disposes `CancellationTokenSource` and awaits loop task. `ProducerHolder` (inner class) implements `IDisposable`. | Any new service requiring disposal must be added to both `Dispose(bool)` and `DisposeAsyncCore()` paths | — |
| avoidable overhead risk is identified | done | `SpecificRecordGenerator` uses `ConcurrentDictionary<string, Lazy<Type>>` — type cache. `KeyValueTypeMapping.PlanCache` caches compiled `Expression` lambdas — avoids repeated compilation. `EventSet.Map()` sync overload calls `ToListAsync().GetAwaiter().GetResult()` — loads entire table into memory before mapping; for large tables this is an allocation and blocking risk. | `EventSet.Map()` sync overload is a potential performance concern for large table entities | Route to `csharp_review` handoff: sync-over-async and full-collection-in-memory pattern in `EventSet.Map()` |

---

## Test Boundary

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| related tests are identified | done | Unit tests: `tests/Ksql.Linq.Tests.csproj` and `tests/Kafka.Ksql.Linq.Cache.Tests/`. Integration tests: `physicalTests/Ksql.Linq.Tests.Integration.csproj` (require live Kafka/ksqlDB). CLI tests: `tests/Ksql.Linq.Cli.Tests/`. `InternalsVisibleTo` grants: `Ksql.Linq.Tests`, `Ksql.Linq.Cache.Tests`, `Ksql.Linq.Tests.Integration`, `Kafka.*` variants, `DynamicProxyGenAssembly2` (mocking). | Changes to internal services accessible only via `internal` modifier depend on `InternalsVisibleTo` for unit test access | Test project content not examined in detail; coverage gaps unknown |
| missing regression coverage is identified | unknown | Test content not read. Integration tests need live infrastructure. The startup phase sequence (schema registration → DDL → cache) has no observable test asserting phase order from examined source. | A change to startup sequence should add a test asserting phase order | UNK-006: Unit test coverage of `SchemaRegistrar.RegisterAndMaterializeAsync` phase ordering is unknown |
| test isolation risks | done | Static `ConcurrentDictionary` fields in `KsqlContextCacheExtensions` (lines 37-40) are shared across test runs; tests creating multiple context instances may interfere. `DynamicProxyGenAssembly2` in `InternalsVisibleTo` confirms mock/proxy framework use. | Tests must call `ClearStreamizState()` or equivalent between context instances to avoid static state leakage | IMPLICIT: no documented test teardown requirement for static cache state |

---

## Change Placement Basis

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| de-facto home of the affected logic is identified | done | Query building logic (DDL/DML generation): `src/Query/Pipeline/` and `src/Query/Builders/`. Schema mapping logic: `src/Mapping/` and `src/SchemaRegistryTools/`. Runtime messaging logic (produce/consume/commit): `src/Messaging/`. Startup lifecycle orchestration: `KsqlContext.Lifecycle.cs` + `Runtime/Schema/SchemaRegistrar.cs`. Configuration binding: `src/Configuration/`. | Any change must be placed to avoid creating a second owner of an existing rule | — |
| placement options and their responsibility impact are recorded | done | **Option A: Add logic to `KsqlContext` partials** — follows current pattern for orchestration and lifecycle; creates risk of further bloating the context class (already 1050+ lines in Lifecycle partial alone). **Option B: Add a new `IUnifiedPipelineStage`** — follows extracted local rule for post-execution pipeline extension; avoids touching `KsqlContext`. **Option C: Extend `SchemaRegistrar`** — follows extracted local rule for startup I/O; appropriate for schema-related changes. **Option D: Extend `KsqlDslOptions` + `Configuration/`** — appropriate for configuration-driven behavior. **Option E: Add to `Core/Abstractions/`** — appropriate for new cross-cutting contract types. | Options B and C follow extracted local rules. Options A risks rule duplication; must be justified. | — |
| second-owner risks are checked | done | Topic-name derivation: one owner (`CoreExtensions.GetKafkaTopicName`) — safe. Startup sequence: one owner (`SchemaRegistrar.RegisterAndMaterializeAsync`) — safe. DDL generation: one owner per statement type (`DDLQueryGenerator`, `DMLQueryGenerator`). Error retryability classification: one owner (`IsRetryableKsqlError`) — adding substring matching elsewhere would create a second owner. | A change must not add topic-name derivation logic outside `CoreExtensions.GetKafkaTopicName()` | — |

---

## Impacted Targets

| Target | Impact Type | Evidence | Notes |
|------|------|------|------|
| `KsqlContext` partials (Lifecycle, Model, Schema, Execution) | Primary — any structural change touches this | `src/Context/KsqlContext.*.cs` | Partial class split is intentional design; changes must respect partial file boundaries |
| `SchemaRegistrar` | Primary — startup sequence | `src/Runtime/Schema/SchemaRegistrar.cs` | All startup I/O sequencing is here |
| `EventSet<T>` | Primary — consumer/producer entry points | `src/EntitySets/EventSet.cs` | Abstract base used by all entity sets |
| `KsqlDslOptions` | Configuration — any new option | `src/Configuration/KsqlDslOptions.cs` | Consumed by multiple constructors and services |
| `MappingRegistry` | Secondary — schema/type mapping | `src/Mapping/MappingRegistry.cs` | Avro schema registration is tied here |
| `Query/Pipeline/` generators | Secondary — DDL changes | `src/Query/Pipeline/DDLQueryGenerator.cs`, `DMLQueryGenerator.cs` | KSQL syntax changes go here |
| Integration tests (`physicalTests/`) | Test — any change must be regression-verified | `physicalTests/Ksql.Linq.Tests.Integration.csproj` | Requires live Kafka/ksqlDB infrastructure |
| `PublicAPI.Shipped.txt` / `PublicAPI.Unshipped.txt` | API surface gate — any public API addition | `src/PublicAPI.*.txt` | RS0016/RS0017 enforced under StrictPublicApi=true |

---

## Unresolved Items

| Item | Missing Evidence | Suggested Next Check |
|------|------|------|
| UNK-001: Static `ConcurrentDictionary` in `KsqlContextCacheExtensions` shared across context instances | Lines 37-40 `Cache/Extensions/KsqlContextCacheExtensions.cs` — full read; whether `Clear()` fully resets static state | `csharp_review`: examine static lifecycle and test isolation impact |
| UNK-002: Startup phase order has no test coverage from evidence seen | `tests/Ksql.Linq.Tests.csproj` not read | Read unit test project and search for tests asserting `RegisterAndMaterializeAsync` phase order |
| UNK-003: Sync-over-async in `KsqlContextCacheExtensions` lines 1220, 1309 | Not confirmed whether call site is inside a constructor (acceptable) or inside an async path | `csharp_review`: classify as defect candidate or deliberate design |
| UNK-004: `ConfigLoggingExtensions.cs` logging of potentially sensitive config values | File not fully read | Read and confirm what is logged; check for credential or URL logging |
| UNK-005: Additional `GetAwaiter().GetResult()` in `KsqlContext.Schema.cs:176-182` | Not fully traced for deadlock risk in async calling contexts | `csharp_review`: determine whether all sync-over-async sites are guarded to constructor context only |
| UNK-006: Unit test coverage of `SchemaRegistrar.RegisterAndMaterializeAsync` | Test project not read | Read `tests/Ksql.Linq.Tests.csproj` contents and search for `SchemaRegistrar` test coverage |
| Roslyn baseline | Build excluded (external snapshot, read-only structure analysis) | State: `baseline_unavailable`; acceptable per skill failure handling |
| `[KsqlIgnore]` consuming mechanism in Mapping layer | `Mapping/` not fully traced for this attribute | Grep `KsqlIgnoreAttribute` in Mapping files to confirm consuming mechanism |
| `KsqlContextCacheExtensions` full read | Large file (1300+ lines); only reference grep performed | Read in full if cache extension behavior is in scope of a future change |

---

## Security Handoff

| Item | Route | Notes |
|------|------|------|
| TLS enforcement for Kafka and Schema Registry connections | `skills/security_review/meta.md` | Library accepts URLs from config without enforcing TLS — caller responsibility; no local validation |
| `GetAwaiter().GetResult()` sync-over-async sites (UNK-003, UNK-005) | `skills/csharp_review/meta.md` | Potential deadlock risk under ASP.NET classic or WPF synchronization context |
| Static shared state in `KsqlContextCacheExtensions` (UNK-001) | `skills/csharp_review/meta.md` | Test isolation risk and potential multi-context state leakage |
| `EventSet.Map()` sync overload full-collection-in-memory pattern | `skills/csharp_review/meta.md` | Memory and blocking risk for large table entities |

---

## Summary

- key structure finding: `KsqlContext` is the central orchestrator owning all service lifetimes and the startup sequence; responsibility is split across four distinct rule homes — query building (`Query/Pipeline/`), schema mapping (`Mapping/`), runtime/messaging (`Messaging/` + `Infrastructure/`), startup orchestration (`SchemaRegistrar`). The context partials (Lifecycle, Model, Schema, Execution) are the integration layer.
- key change impact: Any structural change must determine which of the four rule homes it belongs to; placing logic in `KsqlContext` directly (Option A) is a high-risk default because the context class is already large and owns responsibilities that have better-targeted homes.
- highest risk: Blocking `GetAwaiter().GetResult()` on async I/O — present in the constructor (deliberate fail-fast), in cache extensions (lines 1220, 1309), in schema path (lines 176-182), and in `EventSet.Map()` sync overload — the constructor sites are deliberate design; the non-constructor sites are candidates for `csharp_review`.
- recommended next investigation: (1) Read `KsqlContextCacheExtensions.cs` in full to confirm static state lifecycle (UNK-001); (2) Read `ConfigLoggingExtensions.cs` to confirm no credential logging (UNK-004); (3) Confirm `[KsqlIgnore]` consuming mechanism in `Mapping/` files.
