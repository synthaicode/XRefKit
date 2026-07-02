# Error Policy Report: MailKit.Pooling

- date: `2026-06-12`
- target: `C:\dev\MailKit.Pooling` — solution `MailKit.Pooling.sln`, projects `src/MailKit.Pooling` and `src/MailKit.Pooling.DependencyInjection`
- scope filters: `src/**/*.cs` excluding `obj/` and `bin/` (36 files); `tests/` consulted only as intent evidence
- seed input: no prior `dotnet_change_analysis` note; `work/judgments/2026-06-06_judgment_mailkit_pooling_stale_semaphore_permits.md` loaded as known-risk seed
- run log: `work/sessions/2026-06-12_skill_run_csharp_error_policy_extraction.md`

## 1. Search Pattern Set

| # | Pattern / command | Bucket | Added during run? |
|---|---|---|---|
| 1 | `throw ` | throw sites | no |
| 2 | `throw;\|throw \w+;\|ExceptionDispatchInfo` | rethrow forms | no |
| 3 | `catch` | catch blocks | no |
| 4 | `class \w+Exception` | custom exception types | no |
| 5 | `async void\|\.Result\|\.Wait\(\|GetAwaiter\(\)\.GetResult\|Task\.Run\|ContinueWith\|UnhandledException\|UnobservedTaskException` | dotnet-specific paths | no |
| 6 | `ValidateOnStart\|IValidateOptions\|ValidateDataAnnotations\|AddOptions\|IHostedService\|BackgroundService` | DI / options validation | no |
| 7 | `Try[A-Z]\w*\|return null\|return default\|Array\.Empty\|Enumerable\.Empty` | omission policies | no |
| 8 | `ILogger\|LoggerFactory\|Console\.\|Trace\.\|Debug\.Write\|EventSource` | logging presence | no |
| 9 | `new SmtpStageAwareException` (whole repo incl. tests) | intent evidence | yes — custom type appeared throw-less in src |
| 10 | full-file reads: SmtpPool, SmtpSender, TimeoutExecution, DefaultSmtpErrorClassifier, MailKitSmtpConnectionFactory, MailKitSmtpClientAdapter, SmtpConnectionLease, ServiceCollectionExtensions, SmtpPoolOptions, SmtpSendResult, SystemDiagnosticsSmtpPoolMetrics, MailKitSecureSocketOptionsParser, all Errors/* | all | no |

## 2. Inventory (Phase 1)

Paths below are relative to `C:\dev\MailKit.Pooling\src\`.

### 2.1 Throw Sites

| file:line | module | error kind | behavior | propagation terminus | logging | intent | basis |
|---|---|---|---|---|---|---|---|
| MailKit.Pooling.DependencyInjection/ServiceCollectionExtensions.cs:54,59,64,69 | DI | invalid pool config (hosts empty / Host blank / Weight<=0 / JitterRatio range) | `ArgumentException` at `AddMailKitPooling` registration time (configure delegate runs eagerly) | consumer's composition root; aborts startup | none | confirmed | eager `Validate(options)` call at :33 is deliberate structure |
| MailKit.Pooling/Pooling/SmtpPool.cs:32-33,42,47,52,57,62,67 | Pooling | null deps / invalid option ranges | `ArgumentNullException` / `ArgumentOutOfRangeException` / `ArgumentException` in ctor | first DI resolution of singleton `SmtpPool` | none | confirmed | duplicate of DI-level validation plus pool-only rules (MaxPoolSize, MinPoolSize, AcquireTimeout) |
| MailKit.Pooling/Sending/SmtpSender.cs:29-31 | Sending | null deps | `ArgumentNullException` in ctor | first DI resolution | none | confirmed | standard guard convention |
| MailKit.Pooling/MailKit/MailKitSmtpConnectionFactory.cs:16-17 | MailKit | null deps | `ArgumentNullException` in ctor | first DI resolution | none | confirmed | same convention |
| MailKit.Pooling/Sending/SmtpSender.cs:38 | Sending | null message argument | `ArgumentNullException.ThrowIfNull` | caller of `SendAsync` | none | confirmed | public API guard |
| MailKit.Pooling/Sending/SmtpSender.cs:158 | Sending | any send failure after classification, retry budget exhausted or retry not allowed | `throw new SmtpSendFailedException(...)` wrapping original as inner, carrying `Classification` + `Attempts` | caller of `SendAsync` | metrics (SendFailedCount, SendAmbiguousCount / SendDefinitelyNotAcceptedCount, SendClassificationCount) | confirmed | central translation point; classification reason strings document each branch |
| MailKit.Pooling/Internal/TimeoutExecution.cs:21 | Internal | non-positive timeout (config-derived) | `ArgumentOutOfRangeException` at operation time | send/connect/auth call path | none | confirmed | guard |
| MailKit.Pooling/Internal/TimeoutExecution.cs:34 | Internal | operation exceeded timeout | translate `OperationCanceledException` -> `TimeoutException` with inner, only when caller token not cancelled (filter at :32) | classifier via SmtpSender catch-all | none | confirmed | filter distinguishes timeout from caller cancel |
| MailKit.Pooling/MailKit/MailKitSecureSocketOptionsParser.cs:14 | MailKit | invalid `SecureSocketOptions` config string | `ArgumentOutOfRangeException` at first connection creation, not at startup | pool create-failure handling (cooldown + failover), eventually acquire caller | metrics (PoolConnectionCreateFailures) | contradictory | other config rules validate eagerly; this one surfaces in steady state — see contradiction C-1 |
| MailKit.Pooling/Pooling/SmtpPool.cs:96 | Pooling | acquire deadline exceeded | `throw new SmtpPoolExhaustedException` (`: TimeoutException`) | `SendAsync` catch-all -> classified `PoolExhausted`, no retry, wrapped into `SmtpSendFailedException` | metrics (PoolAcquireExhaustedCount, wait-time histogram) | confirmed | explicit deadline handling |
| MailKit.Pooling/Pooling/SmtpPool.cs:923 | Pooling | use after dispose | `ObjectDisposedException` | acquire/warmup caller | none | confirmed | standard dispose guard |
| MailKit.Pooling/MailKit/MailKitSmtpClientAdapter.cs:18,20,50 | MailKit | bad internal wiring / non-MimeMessage payload | `ArgumentNullException` / `ArgumentException` | internal callers | none | confirmed | adapter contract guards |
| MailKit.Pooling/MailKit/MailKitSmtpClientAdapter.cs:33,38 | MailKit | misuse of adapter seam | `NotSupportedException` (Connect/Authenticate must go through factory) | internal callers | none | confirmed | message names the correct path |
| MailKit.Pooling/Metrics/SystemDiagnosticsSmtpPoolMetrics.cs:19,34 | Metrics | null event / unknown enum value | `ArgumentNullException` / `ArgumentOutOfRangeException` | metric Record caller (send/pool paths) | none | confirmed | exhaustive-switch guard |
| MailKit.Pooling/Errors/DefaultSmtpErrorClassifier.cs:13 | Errors | null exception argument | `ArgumentNullException.ThrowIfNull` | SmtpSender catch-all | none | confirmed | guard |
| MailKit.Pooling/Retry/RetryDelayCalculator.cs:13,18,23 | Retry | non-positive attempt (internal counter) / negative baseDelay, jitter (config-derived) | `ArgumentOutOfRangeException` at retry-delay computation (steady state) | SmtpSender catch-all -> classified `ConnectionCorrupted` | none | inferred | guards consistent with convention, but config-derived values reaching here bypass eager validation (JitterRatio is eagerly validated; RetryBaseDelay is not) — see C-1 |

Rethrow forms: 6 bare rethrows, all `rethrow_preserving` (`throw;`) — SmtpSender.cs:80, SmtpPool.cs:223, 251, 395, 478, MailKitSmtpConnectionFactory.cs:64. Zero `throw ex;` (`rethrow_resetting`). Zero `ExceptionDispatchInfo`.

### 2.2 Catch Blocks

| file:line | kind | behavior | propagation terminus | logging | intent | basis |
|---|---|---|---|---|---|---|
| Internal/TimeoutExecution.cs:31 | filtered (`when` timeout-not-caller-cancel) | translate to `TimeoutException` with inner | classifier | none | confirmed | filter expression |
| Sending/SmtpSender.cs:73 | filtered OCE (caller cancelled) | discard lease best-effort, then `throw;` | `SendAsync` caller | none | confirmed | cancellation honored after cleanup |
| Sending/SmtpSender.cs:82 | catch-all (`Exception`) | classify -> retry (budget + `IsRetryAllowed`) or translate to `SmtpSendFailedException`; lease returned or discarded per `ShouldDiscardConnection` | caller | metrics per branch | confirmed | the central policy point of the codebase |
| Sending/SmtpSender.cs:185 | bare catch (lease cleanup beyond 1s budget) | swallow; abandoned task observed via `ContinueWith(OnlyOnFaulted)` reading `task.Exception` | nothing escapes | none (no metric) | confirmed | comment: "Preserve the original send outcome... never becomes unobserved" |
| Pooling/SmtpPool.cs:216 | filtered OCE (caller cancelled during create) | decrement pending, `throw;` | acquire caller | none | confirmed | counter hygiene before rethrow |
| Pooling/SmtpPool.cs:225 | bare catch (connection create failure) | host cooldown + failover: `continue` if another host eligible; `throw;` if no live connections; else swallow and keep waiting | conditional | metrics (PoolConnectionCreateFailures) | confirmed | comments at :254, :357 document the design |
| Pooling/SmtpPool.cs:331 | typed `SemaphoreFullException` | swallow, empty body, no comment | nothing | none | inferred | guard for wake-burst over semaphore max; interacts with known stale-permit risk (handoff H-1) |
| Pooling/SmtpPool.cs:393 | filtered OCE (caller cancelled) | `throw;` | caller | none | confirmed | — |
| Pooling/SmtpPool.cs:397 | bare catch (warm refill failure) | swallow | nothing | metrics already recorded inside refill | confirmed | comment: "Warm refill is best-effort..." |
| Pooling/SmtpPool.cs:464 | bare catch (min-pool create failure) | cooldown + metric + `throw;` | `WarmupAsync` caller propagates; `TryEnsure...` wrapper swallows | metrics | confirmed | explicit Try*-wrapper split — conditional rule, not contradiction |
| Pooling/SmtpPool.cs:495 | bare catch (keepalive NoOp failure) | drop connection (`isReusable:false`), return false, acquire loop continues | nothing escapes | metrics (dropped + keepalive failure) | confirmed | degrade by design |
| Pooling/SmtpPool.cs:632 | typed `ObjectDisposedException` (semaphore wait vs dispose race) | return; next loop iteration surfaces `ObjectDisposedException(SmtpPool)` | acquire caller (as pool-level ODE) | none | confirmed | comment at :634 |
| Pooling/SmtpPool.cs:647 | filtered OCE (internal wait-cts only) | swallow (await cleanup of timer/signal tasks) | nothing | none | confirmed | filter excludes caller cancellation |
| Pooling/SmtpPool.cs:680 | bare catch (DisconnectAsync during connection dispose) | swallow, empty body, no comment; `DisposeAsync` at :684 NOT guarded | nothing (disconnect); a throwing `DisposeAsync` would escape the dispose loop | metrics (dropped, recorded after) | inferred | best-effort disconnect shape, but unmarked; asymmetric with guarded disconnect |
| MailKit/MailKitSmtpConnectionFactory.cs:61 | bare catch (connect/auth failure) | dispose raw client, `throw;` | pool create-failure handling | none | confirmed | compensation-then-rethrow |

### 2.3 Custom Exception Types

| type | base | thrown by | caught by | representation convention |
|---|---|---|---|---|
| `SmtpSendFailedException` (public) | `Exception` | SmtpSender.cs:158 | nobody in src — public API contract | carries `SmtpFailureClassification` + `Attempts`; inner always preserved |
| `SmtpPoolExhaustedException` (internal) | `TimeoutException` | SmtpPool.cs:96 | type-tested in DefaultSmtpErrorClassifier.cs:15 | internal type escaping the public API — external callers can only catch it as `TimeoutException` |
| `SmtpStageAwareException` (internal) + `ISmtpStageAwareException` (internal) | `Exception` | **nowhere in production src** — only constructed in tests (SmtpSenderTests.cs:48 et al.) | type-tested in SmtpSender.cs:204,233 | stage-marking seam; because the interface is `internal`, no external adapter can implement it — currently a test-only seam |

### 2.4 Global Handlers

| handler | file:line | behavior | covers |
|---|---|---|---|
| none | — | library ships no `AppDomain.UnhandledException` / `TaskScheduler.UnobservedTaskException` / host middleware | consumer-owned; the only fire-and-forget site self-observes faults so nothing reaches `UnobservedTaskException` by design |

### 2.5 Dotnet-Specific Paths

| path | findings |
|---|---|
| `async void` | none found |
| fire-and-forget | exactly 1: SmtpSender.cs:189 `_ = completionTask.ContinueWith(... OnlyOnFaulted ...)` — deliberately observes the abandoned cleanup task's exception; intent confirmed by comment |
| sync-over-async | none (`.Result`, `.Wait(`, `GetAwaiter().GetResult()` absent) |
| DI composition root | all-singleton registration (ServiceCollectionExtensions.cs:35-44); options validated eagerly at registration (:33), not via `IOptions`/`ValidateOnStart` (Options pattern unused); factory delegates contain no throw logic; no `IHostedService`/`BackgroundService` — `WarmupAsync` exists (SmtpPool.cs:268) but nothing in the library calls it at startup |
| Dispose paths | `SmtpPool.DisposeAsync` (:292) idempotent under lock, disposes all connections with `CancellationToken.None`, wakes waiters, then disposes the semaphore (waiter race handled at :632); `DisposeConnectionAsync` (:671) swallows disconnect failure but leaves `client.DisposeAsync()` (:684) unguarded; `SmtpConnectionLease` completion idempotent via `Interlocked.Exchange` (:48); lease `DisposeAsync` = invalidate (safe default: not reusable) |

### 2.6 Omission Policies (detected range only)

| file:line | pattern | behavior | intent | basis |
|---|---|---|---|---|
| Pooling/SmtpPool.cs:347-350 | silent no-op | `ReturnLeaseAsync` with unknown connectionId returns without effect or trace | inferred | idempotency convention consistent with lease double-completion guard, but unmarked |
| Pooling/SmtpPool.cs:764 | `Try*` (bool + out) | `TrySelectHostForCreation` false = all hosts cooling down; reason detail not in return value | confirmed | `PoolReconnectSuppressed` metric compensates on the acquire path (:149) |
| Pooling/SmtpPool.cs:387 | `Try*` wrapper | `TryEnsureMinimumPoolSizeAsync` converts refill failures to silence (except cancellation) | confirmed | comment :399; metrics recorded at failure site |
| Pooling/SmtpPool.cs:483 | bool-only | `ValidateLeasedConnectionAsync` returns false; failure detail goes to metrics only | confirmed | metric pair at :497-507 |
| MailKit/MailKitSmtpConnectionFactory.cs:52 | fallback `?? string.Empty` | missing `Password` with configured `UserName` becomes empty-string authentication — config omission surfaces as runtime auth failure (`PermanentFailure`) instead of startup validation error | contradictory | eager validation checks Host/Weight but not Password presence — see C-1 |
| MailKit/MailKitSecureSocketOptionsParser.cs:9 | `TryParse` -> throw | omission converted to exception (not an omission policy; listed for completeness) | confirmed | — |

Logging presence (all buckets): **zero logging infrastructure in src** (pattern #8 returned no matches). The de-facto observability policy is metrics-only; error detail survives only in exception messages and `SmtpFailureClassification.Reason`.

### Bucket States

| bucket | state | reason |
|---|---|---|
| explicit handling (throw/catch/custom/global) | done | all hits inventoried; all 15 catch sites read in context |
| dotnet-specific paths | done | all pattern hits read in context; absences recorded as findings |
| omission policies | done (non-exhaustive by definition) | detected range = patterns #7/#8 plus full reads of the 13 core files |

## 3. Category x Disposition Matrix (Phase 2)

Counts are inventory items (a multi-line guard block = 1 item per distinct rule).

| category \ disposition | fail-fast | propagate | translate | retry | degrade | swallow | log-only |
|---|---|---|---|---|---|---|---|
| configuration | **17** (SCE:54-69 ×4; SmtpPool ctor ×8; SmtpSender ctor ×3 *(grouped as 1 site each below)*; Factory ctor; TimeoutExecution:21; Parser:14) | — | — | — | **1** (Factory:52 password fallback) | — | — |
| transient | — | **2** (SmtpPool:96 exhausted; :464/478 warmup rethrow) | **2** (TimeoutExecution:34; SmtpSender:158) | **1** (SmtpSender:82 via classifier budget) | **4** (SmtpPool:225 cooldown+failover; :397 refill; :495 keepalive; :680 disconnect) | — | — |
| invariant_violation | — | **9** (ThrowIfNull guards ×4; adapter contract ×3 sites; SmtpPool:923; Metrics:34) | **1** (SmtpSender:82 catch-all absorbs unknown exception types as `ConnectionCorrupted` — see C-3) | — | — | — | — |
| external_input | — | **1** (SmtpSender:38 null message) | **2** (server permanent rejections -> `SmtpSendFailedException(PermanentFailure)`; ambiguous post-DATA -> `UnknownAfterData`) | **1** (server temporary rejections, classifier `RetryableTemporaryFailure`) | — | — | — |
| unclassified | — | **3** (cancellation rethrows SmtpSender:73, SmtpPool:216, :393 — cancellation is caller intent, not an error; kept unclassified rather than force-fit) | — | — | — | **4** (SmtpPool:331 semaphore-full; :347 unknown-id return; :647 wait cleanup; SmtpSender:185 lease cleanup) | — |

`log-only` column is structurally empty: the codebase has no logger.

### De-Facto Policy Candidates

| category | majority disposition | share | candidate statement |
|---|---|---|---|
| configuration | fail-fast | 17/18 | configuration errors fail fast **before steady state** (registration time or first resolution); two timing deviations exist (C-1) |
| transient | classify-then-{retry\|translate}, degrade at pool layer | 7/9 send-path; 4/4 pool-internal | send-path transients are classified (`DefaultSmtpErrorClassifier`), retried within `MaxRetryAttempts` when `IsRetryAllowed`, otherwise translated into `SmtpSendFailedException` with classification and inner; pool-internal transients degrade (cooldown, failover, drop, keep waiting) and are visible via metrics, never via logs |
| invariant_violation | propagate raw | 9/10 | programming errors propagate undecorated — except inside `SendAsync`, where the catch-all converts them into `ConnectionCorrupted` send failures (C-3) |
| external_input | translate via classification | 3/4 | server-side rejections are normalized into `SmtpFailureKind` with explicit retry/no-retry semantics; SMTP DATA ambiguity is modeled as its own kind (`UnknownAfterData`), never guessed |
| cross-cutting | — | — | rethrow is always `throw;` (6/6); translation always preserves the inner exception (3/3); cancellation is always honored and distinguished from timeout by `when` filters (4/4); every swallow/degrade site is metric-visible or comment-marked **except** SmtpPool:331, :347, :680 (C-4) |

(candidates, not verdicts)

### Unclassified Items

| file:line | why unclassifiable | judgment material |
|---|---|---|
| SmtpPool.cs:331 | swallowing `SemaphoreFullException` is a synchronization-design artifact, not an error category | intended signal semantics (edge vs level triggered) — same open question as the 2026-06-06 judgment log |
| SmtpPool.cs:347 | silent no-op on unknown connection return — idempotency convention vs masked caller bug | whether double-return / foreign-id return should be observable |
| cancellation rethrows | caller intent, not failure | none needed — convention is uniform |

## 4. Contradictions (Phase 3)

### C-1: configuration validation timing is split

- group: ServiceCollectionExtensions.cs:49-71 + SmtpPool.cs:40-68 (eager) vs MailKitSecureSocketOptionsParser.cs:14, MailKitSmtpConnectionFactory.cs:52 (`Password ?? string.Empty`), RetryDelayCalculator.cs:18 (`RetryBaseDelay` unvalidated eagerly)
- behaviors: hosts/weights/JitterRatio/pool sizes throw at registration or construction (process never starts wrong); `SecureSocketOptions` string and missing `Password` surface only at **first connection attempt** in steady state, where the create-failure path applies a reconnect cooldown and failover — a pure config typo presents operationally as a repeating transient connection failure (metrics: `PoolConnectionCreateFailures` cycling, eventually `SmtpSendFailedException`)
- placement explanation: **not explainable** — these are the same kind of static configuration data validated in the same options object; nothing about their processing characteristics requires lazy validation
- adjudication material: whether `Validate(options)` should also parse `SecureSocketOptions` and require `Password` when `UserName` is set; who owns config-error UX (startup crash vs runtime metric cycling)

### C-2: duplicated config-rule ownership with diverging exception types

- group: ServiceCollectionExtensions.cs:67-70 (`ArgumentException` for JitterRatio) vs SmtpPool.cs:55-58 (`ArgumentOutOfRangeException` for the same rule); hosts-nonempty and weight rules also live in both places (:52-65 vs :60-68)
- behaviors: same invalid value produces a different exception type depending on whether the pool is built via DI or constructed directly
- placement explanation: **partially explainable** — `SmtpPool` is constructible without the DI package, so ctor-level defense is a deliberate second line; the exception-type divergence within the same rule is not explained
- adjudication material: which layer is the canonical owner of each rule; whether the DI validator should delegate to one shared validator to keep messages and types aligned

### C-3: invariant violations are absorbed inside the send path

- group: library-wide propagate-raw convention (ObjectDisposedException SmtpPool.cs:923, NotSupportedException adapter:33/38, ArgumentOutOfRangeException Metrics:34) vs SmtpSender.cs:82 catch-all + DefaultSmtpErrorClassifier.cs:50-56 fallback
- behaviors: outside `SendAsync`, a programming error surfaces raw; inside `SendAsync`, any unrecognized exception (including a hypothetical `NullReferenceException` from a custom `ISmtpClientAdapter`) is classified `ConnectionCorrupted`, the connection is discarded, and the caller receives `SmtpSendFailedException` — the bug signature survives only as `InnerException`
- placement explanation: **partially explainable** — the catch-all guarantees lease bookkeeping and pool integrity on every exit path, and the classifier's reason string ("Unhandled SMTP failure type ... treated as a broken connection") shows the fallback is deliberate for *unknown SMTP failures*; whether it is also intended for *non-SMTP programming errors* is not evidenced
- adjudication material: whether bug-class exceptions should bypass classification (e.g., filter to known exception families) at the cost of a more fragile cleanup path

### C-4: intentional-swallow marking is inconsistent

- group: marked swallows (SmtpSender.cs:185 comment + fault observation; SmtpPool.cs:397 comment; :632 comment; :647 self-documenting filter) vs unmarked swallows (SmtpPool.cs:331 `SemaphoreFullException` empty body; :347-350 unknown-id no-op; :680 disconnect empty body)
- behaviors: identical disposition (swallow), inconsistent evidence of intent; the unmarked ones are exactly where the known synchronization risk lives
- placement explanation: not a behavioral contradiction — a convention-consistency gap; recorded because the de-facto rule "swallows are marked and observable" fails at 3 sites
- adjudication material: none beyond a style decision; the SemaphoreFullException site additionally depends on the H-1 arbitration

## 5. DI Startup-Throw Triage

| site | occurrence time | recovery responsibility | blast radius | note |
|---|---|---|---|---|
| ServiceCollectionExtensions.Validate (:54-69) | startup (registration; configure delegate runs eagerly) | operator (fix config) | single process, refuses to start | earliest possible failure point; deliberate |
| SmtpPool ctor guards (:32-68) | first resolution of the singleton — boot time only if the consumer resolves/warms eagerly; otherwise first send | operator | single process | the library never calls `WarmupAsync` itself; with lazy resolution a bad `MaxPoolSize` surfaces at the first email, not at boot |
| SmtpSender / Factory ctor guards | first resolution | operator | single process | wiring errors only |
| MailKitSecureSocketOptionsParser:14 via first connection | steady state | operator | single process, but **degraded-forever shape**: every create fails, cooldown cycles, sends end in `SmtpSendFailedException`; process stays up and keeps accepting work | worst observed blast shape; see C-1 |
| factory delegates (`AddSingleton(_ => ...)`) | n/a | — | — | no throw logic inside delegates |
| `IOptions` validation / `ValidateOnStart` / `IHostedService.StartAsync` | n/a | — | — | Options pattern and hosted services are not used |

## 6. Coverage Limits (mandatory)

- **Omission policies are non-exhaustive.** Detected range = patterns #7/#8 in section 1 plus full reads of the 13 core files. Fallback-value conventions expressed through other syntax (conditional expressions, LINQ defaults) were not systematically swept.
- **Dynamic exception paths are not traced.** Exception flow through the delegate seams (`Func<CancellationToken, Task>` operations in `TimeoutExecution`, DI factory lambdas, the `ContinueWith` continuation) was reasoned statically only; no reflection-based invocation exists in src, but this is asserted from the same static scan.
- **Third-party internals are invisible.** MailKit's `SmtpClient` (and MimeKit) own the actual protocol I/O; any swallowing or transformation inside them is unobservable here. `DefaultSmtpErrorClassifier`'s completeness depends on MailKit's exception contract (`SmtpCommandException`, `SmtpProtocolException`, socket/IO types) — boundary behavior only.
- **Tests were not part of the policy scan.** `tests/` was consulted solely as intent evidence for `SmtpStageAwareException`; test code may encode additional expected-behavior contracts not extracted here.
- **Static reading only.** Propagation-terminus conclusions (e.g., the C-1 cooldown-cycling shape) derive from code reading, not from runtime reproduction.

## 7. Handoff List

| finding | type | handoff target | recorded as |
|---|---|---|---|
| H-1: stale `connectionReturnedSignal` permits (known judgment 2026-06-06) + the unmarked `SemaphoreFullException` swallow at SmtpPool.cs:331 and `WakeWaitingCallers` interplay — wake-semantics defect risk, out of extraction scope | defect | `skills/csharp_review/meta.md` | risk concern RSK-001 + handoff artifact |

No security-scope findings: credentials are passed through to MailKit, never logged (no logger exists); `Password ?? string.Empty` is a validation gap (C-1), not an exposure.

## 8. Unresolved Items

| item | why unresolved | suggested owner |
|---|---|---|
| `SmtpStageAwareException` / `ISmtpStageAwareException` are production-dead (thrown only by tests) and `internal`, so the stage-aware seam cannot be used by external adapter implementations | intent (extension seam vs leftover) not decidable from src evidence | library owner — decide publish (make interface public) or document as test seam |
| Whether `BackgroundServiceExceptionBehavior` matters for any consumer wiring | no hosted service exists in the library; consumer-side wiring unknown | consumer documentation |
| Exact behavior of MailKit `SmtpClient.Dispose` under fault (affects the unguarded :684 dispose) | third-party internals out of scope | csharp_review if pursued |
