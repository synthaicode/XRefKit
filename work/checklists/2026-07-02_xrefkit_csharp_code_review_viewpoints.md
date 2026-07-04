# XRefKit C# Code Review Viewpoints

## Source Basis

This checklist summarizes the current XRefKit C# review viewpoints from:

- `skills/csharp_review/SKILL.md#xid-466B980B8ED3`
- `knowledge/csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA`
- `knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101`
- `capabilities/quality/180_cap_qa_010_beyond_diagnostics_code_risk_review.md#xid-4A3CA9ECFA71`
- `knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001`

## Review Boundary

XRefKit の C# レビューは、Roslyn/compiler/analyzer が既に検出できる問題を主対象にしない。

主対象は、静的診断だけでは見落としやすい以下のリスクである。

- 意味、環境、複数ファイル、複数プロジェクトにまたがる実装リスク
- 運用時の負荷、失敗、再試行、共有リソース枯渇につながるコードパス
- 設計や仕様の不足ではなく、ソースから評価できる実装上の危険
- 証拠不足により断定できない `needs_confirmation` / `unknown`

Security scope の深掘りは `security_review` へ渡す。設計仮定、DDL/コード不整合、業務制約の不足は `constraint-derivation` pack へ渡す。

## Review Viewpoints

| Viewpoint | What to Check | Typical Evidence |
| --- | --- | --- |
| Diagnostics baseline | build/analyzer/Roslyn で既に出る問題を本レビューの finding に混ぜていないか | build output, analyzer report, project file |
| Attribute misuse | 属性の origin、機能前提、適用場所、値、プロジェクト側 precondition が一致しているか | attribute usage, package/source definition, config, DI/setup code |
| Resource lifetime | `IDisposable` / `IAsyncDisposable`、接続、ファイル、timer、buffer などの所有と解放が明確か | constructors, using/await using, loops, factory/lifetime registration |
| Resource efficiency | hot path の不要 allocation、LINQ chain、boxing、繰り返し serialization、chatty I/O がないか | loops, request handlers, batch workers, profiling notes if available |
| Operational resilience | retry storm、connection churn、pool misuse、backlog drain spike、shared-resource exhaustion、blast radius がないか | retry loops, queue/file import, batch size, fan-out, connection creation |
| Synchronization/concurrency | `.Result` / `.Wait()`、deadlock、race、context capture、timeout/cancellation 不足がないか | async flow, locks, shared state, cancellation token propagation |
| Time-controlled waits | fake clock / virtual clock / polling delay が、状態変化で直接 wake できず hang しないか | tests, wait loops, scheduler/clock abstraction, signal path |
| Required input integrity | 必須入力の欠落が `0`、`false`、empty、null、default enum、`??`、`TryGet`、catch-and-default で黙殺されないか | config/API/cache/DB/file/message lookup and fallback branches |
| Error handling | swallowed exception、log-and-continue、`throw ex;`、unobserved async failure、cleanup bypass がないか | catch blocks, background workers, transaction/compensation paths |
| Retry/idempotency | retry に backoff、jitter、budget、stop condition、idempotency があるか | retry policy, idempotency key, attempt count, downstream call boundary |
| Deadline/cancellation | caller-visible deadline 後に不要な work を続けないか、fan-out 先へ cancellation が伝播するか | tokens, timeout settings, worker stages, RPC/client calls |
| Time/culture | `DateTime.Now` / `UtcNow` 混在、`DateTimeKind` 不整合、culture-sensitive parse/format が境界で使われていないか | timestamp comparisons, persistence, serialization, protocol strings |
| State/determinism boundary | 状態遷移の決定性が保証されているか。非同期パスやエージェント間連携で、副作用のある mutable state が暗黙的に共有またはリークしていないか | pure functions, state machines, thread-local or scoped state, side-effect isolation |
| Uncertainty/escalation path | 判定、パース、予測の不確実性が、中途半端な値で正常系として流されず、明示的に `unknown` または escalation/handoff path へ渡されているか | structural fallback branches, classification confidence checks, escalation triggers |
| Contract/schema resilience | 外部コンテキスト、メッセージ、AIモデル出力の微細な形式変化に対して、serialize/deserialize 境界がクラッシュ、未知扱い、拒否、互換処理のどれとして設計されているか | JSON/MessagePack strictness config, polymorphic deserialization, ignore-unknown attributes, schema/version handling |
| Traceability/context propagation | 非同期実行、バックグラウンドタスク、エージェントを跨ぐ処理で、trace id、発火元、実行文脈が途切れずに伝播しているか | `Activity.Current`, `AsyncLocal` flows, structured logging context metadata, task/job metadata |
| Support lifecycle | TFM、.NET runtime、critical package の support status が有効か | target framework, package versions, official lifecycle source |
| Code quality | approved design boundary、readability、testability、dependency control、dead code が崩れていないか | changed files, tests, dependency files, design references |
| Security handoff | injection、hardcoded secrets、certificate validation 無効化などが見えた場合に深掘りせず渡せているか | source path and concrete handoff note |
| Design handoff | コードに埋め込まれた業務仮定、DDL/コード不整合、未確認の仕様判断を渡せているか | source path, branch condition, missing design/constraint evidence |

## Finding Rules

Every finding should include:

- category
- severity: `critical`, `major`, `minor`, or `needs_confirmation`
- evidence path
- violated condition
- remediation direction
- missing evidence, when the finding is not fully provable

Do not report a clean category by omission. The review output should show every active category as `pass`, `fail`, `pass-after-fix`, `escalated`, or `not_applicable`.

## Severity Orientation

Use severity from evidence and failure path, not from pattern names alone.

- `critical`: direct closure blocker, severe data loss/security-equivalent impact, or deterministic block finding.
- `major`: plausible production failure, shared-resource exhaustion, silent business-critical fallback, data loss, or cross-workload blast radius.
- `minor`: localized correctness, maintainability, or efficiency issue with limited impact.
- `needs_confirmation`: issue is plausible but missing evidence prevents a reliable judgment.

If evidence is insufficient, record `unknown` / `needs_confirmation` instead of guessing.

## Handoff Rules

Keep the C# review focused on source-evaluable implementation risk.

- Security-scope findings go to `skills/security_review/meta.md`.
- Design assumptions and DDL/code mismatches go to the relevant `constraint-derivation` Skill.
- Implementation-local findings return to `implementation_flow` with finding id, evidence, violated condition, remediation direction, and pending validation boundary.
- Runtime, integration, and manual tests can remain validation handoff items; they do not erase source-evaluable findings.

## Pre-CI Verdict

For a reviewed diff, keep the source gate verdict separate from per-finding severity.

```text
verdict: blocked | needs-review | proceed
reason: <why this verdict>
evidence: <paths / artifact ids / baseline state>
downgrade_reason: <required when not proceed>
required_followup: <next owner or specialist Skill, or none>
```

Use `proceed` only when the trace exists, diff scope is declared, triage is complete, the diagnostics baseline is explicit, every active category has a result, and no closure-affecting `needs_confirmation` or open concern remains.
