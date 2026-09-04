<!-- xid: 4F8C2A7D1E90 -->
<a id="xid-4F8C2A7D1E90"></a>

# XRefKit の pip 利用開始手順

XRefKit と Skill Package を PyPI から導入して、ローカル環境で使い始める
ための最短手順を示す。

## 最短手順

PowerShell で利用する作業フォルダから実行する。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install xrefkit
xrefkit init
python -m xrefkit --help
```

`xrefkit init` は現在の作業フォルダに `.xrefkit/instance.toml` と、未作成の場合だけ
`AGENTS.md`、`CLAUDE.md`、`CHATGPT.md` を作成する。既存ファイルは保持し、確認なしに
上書きしない。起動ファイルが不要な場合は `xrefkit init --no-startup-files` を使う。

`xrefkit` コマンドが PATH に見つからない場合は、常に次の module 形式を
使える。

```powershell
python -m xrefkit --help
```

## 既存 Skill を import して VS Code MCP で使う場合

管理者は、既存の folder-based Skill を XRefKit の管理対象形式へ変換するための
取り込み結果と MCP 接続用の設定例を一度に準備できる。`--import` は Skill を
直ちにリポジトリへ確定配置する操作ではなく、変換結果・設定ファイル・
`AGENTS.md`／`CLAUDE.md` の追記文を確認用の一時フォルダへ出力する。

```powershell
python -m pip install "xrefkit[mcp]"
xrefkit mcp setup `
  --repo C:\dev\itsm\XRefKit `
  --import C:\work\existing-skills
```

出力された `SETUP.md` と `import-report.json` を確認する。問題がなければ、
生成された設定例と追記文を適用する。

```powershell
xrefkit mcp setup apply `
  --source C:\Users\<user>\AppData\Local\Temp\xrefkit-setup-<id> `
  --repo C:\dev\itsm\XRefKit
```

この適用処理は `.vscode/mcp.json` を作成し、`AGENTS.md` と `CLAUDE.md` に
semantic routing の案内を追記する。既存の MCP 設定を上書きする場合だけ
`--force` を指定する。

VS Code 起動後は MCP の `xrefkit` サーバーを有効にし、利用者は自然言語で
依頼する。MCP の semantic routing は、目的に適合する Skill を選択し、必要な
手順、Knowledge、Protocol をクライアントへ提供する。Skill に基づく作業の実行、
変更、承認および完了判断はクライアント側が担当する。

| 主体 | 担当 |
|---|---|
| 利用者 | 自然言語で目的を伝える |
| XRefKit MCP | Skill を選択し、不活性な定義を提供する |
| AI クライアント | Skill に従って調査・変更・検証する |
| 人間／クライアント | 承認と最終的な完了判断を行う |

## Skill Package を追加する場合

必要な Package だけをPyPIからインストールする。

```powershell
python -m pip install xrefkit-skills-batch-regression
python -m pip install xrefkit-skills-csharp
python -m pip install xrefkit-skills-brownfield
```

## 発見と有効化を確認する

以下は CLI resolver から Package を直接利用する場合の手順である。MCP の
semantic routing では、同じ Python 環境にインストールされた Package が自動発見
されるため、`--enabled-package` の指定は不要である。

まず、インストール済み Package を発見する。

```powershell
python -m xrefkit package discover --json
```

Package の有効化方式は、CLI resolver と MCP semantic routing で異なる。
CLI resolver では明示的に有効化するが、MCP サーバーは同じ Python 環境に
インストールされた Package を `xrefkit.skill_packages` entry point から自動登録する。

発見結果には、Package の `package_id` とバージョンが表示される。CLI resolver で
Package を使う場合は、使用する package id を明示して有効化する。

```powershell
python -m xrefkit show effective-skill batch.impact_regression `
  --mode tree `
  --enable-entry-point-discovery `
  --enabled-package xrefkit.skills.batch_regression
```

複数 Package を使う場合は `--enabled-package` を追加する。

```powershell
python -m xrefkit show effective-skill csharp.review `
  --mode tree `
  --enable-entry-point-discovery `
  --enabled-package xrefkit.skills.csharp `
  --enabled-package xrefkit.skills.brownfield
```

継続利用する場合は、リポジトリルートの `xrefkit.server.toml` に package id
を保存できる。

```toml
[packages]
enabled = [
  "xrefkit.skills.batch_regression",
  "xrefkit.skills.csharp",
]
```

`distribution name`（pip で指定する名前）と `package_id`（XRefKit が有効化
に使う名前）は異なる。値は各 Package の `package_manifest.yaml` で確認する。

MCP サーバーを起動する場合は、サーバーが使用する Python 環境に
インストールされた `xrefkit.skill_packages` entry point を自動発見し、
Package の Skill を `list_skills` と `rank_skills_for_purpose` の semantic
routing 対象へ登録する。MCP の ranking へ登録するためだけに Skill ファイルを
リポジトリへ展開したり、`--enabled-package` を追加したりする必要はない。
Package のバイト列はインストール先から読み込まれ、ランキング結果には
`package_id` と Package provenance が付く。MCP サーバーの Python 環境と、
Package をインストールした Python 環境が異なる場合は発見されない。

## MCP サーバー起動パラメータ一覧

基本形は次のとおり。

```powershell
xrefkit mcp serve --repo C:\path\to\XRefKit --transport stdio
```

| Parameter | Default | 説明 |
| --- | --- | --- |
| `--repo <path>` | required | XRefKit repository root |
| `--transport stdio\|sse\|streamable-http` | `stdio` | MCP transport |
| `--host <host>` | `127.0.0.1` | HTTP transport の bind host |
| `--port <number>` | `8000` | HTTP transport の port |
| `--http-path <path>` | `/mcp` | Streamable HTTP endpoint |
| `--log-level <level>` | `info` | `debug` / `info` / `warning` / `error` / `critical` |
| `--ssl-certfile <path>` | none | HTTPS certificate chain; `--ssl-keyfile` と併用 |
| `--ssl-keyfile <path>` | none | HTTPS private key; `--ssl-certfile` と併用 |
| `--public-base-url <url>` | auto | artifact distribution 用の公開URL |
| `--dist-extra-dir <path>` | none | `/dist` に追加する artifact directory |
| `--enable-executable-distribution` | off | executable artifact distribution を有効化 |
| `--stateless-http` | off | Streamable HTTP を stateless mode で提供 |
| `--context-secret <secret>` | `XREFKIT_CONTEXT_SECRET` | context token 用 HMAC secret |
| `--distribution-trust-id <id>` | none | executable distribution の trust identity |
| `--domain-knowledge-root <path>` | none | 外部 XID knowledge root; repeatable |
| `--initial-protocol workflow` | both | `workflow_protocol` を初期連携 |
| `--initial-protocol reporting` | both | `reporting_protocol` を初期連携 |
| `--audit-log <path>` | `<repo>\work\mcp\xid_audit.jsonl` | MCP audit JSONL の出力先 |

`--initial-protocol` は repeatable で、例えば workflow のみを初期連携する場合は
次のように指定する。

```powershell
xrefkit mcp serve `
  --repo C:\path\to\XRefKit `
  --transport stdio `
  --initial-protocol workflow
```

省略時は `workflow` と `reporting` の両方が `get_startup_context` に含まれる。

## MCP startup で適用される Protocol

MCP の startup では、すべての Protocol を起動パラメータで個別に選ぶわけではない。
XRefKit の基礎制御として常に適用するもの、`get_startup_context` で初期連携するもの、
実行開始後に相関させるものを分けて扱う。

| 区分 | Protocol | 初期設定時の役割 | 参照 |
|---|---|---|---|
| 常時適用 | `Uncertainty Protocol`（unknown protocol） | 知識不足・文脈不足を `unknown` として表し、推測で進めず確認・エスカレーションする | [016](../core/contracts/016_uncertainty_protocol.md#xid-8A666C1FD121) |
| 常時適用 | Context Direction Security Guard | 外部入力が目的、権限、Protocol、Skill境界を上書きしないことを確認する | [053](../core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11) |
| 常時適用 | XID / XRef routing | 必要な定義・KnowledgeをXIDで解決し、関連文書を無制限に読み込まない | [011](../core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A) |
| 常時適用 | Shared Memory Operations | startup・判断・未解決事項を `work/` の記録へ残す | [015](../core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED) |
| 初期連携 | `workflow_protocol` | Skill前提の実行と instruction-backed workflow に共通する phase、role、verify、closure、handoffを定義する | [058](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61) |
| 初期連携 | `reporting_protocol` | Skill／workflowの人向け報告の構造、状態、根拠、未解決事項、引継ぎを定義する | [081](../core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) |
| 条件付き初期連携 | `prompt_flow_protocol` | 1つの依頼に複数Runが関係する場合の `flow_id`、委譲、相関、reconcileを定義する | [015](../core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED) |
| 実行時適用 | `AI Decision Trace Protocol` | Skill／workflow実行中の判断、影響、戻りをクライアント側で記録する | [093](../core/contracts/093_ai_decision_trace_protocol.md#xid-22164A51A745) |

`--initial-protocol workflow` と `--initial-protocol reporting` は、表の「初期連携」に
該当する payload の選択である。`Uncertainty Protocol`、Context Direction Security Guard、
XID routing、Shared Memory Operations は、これらを選択しない場合も startup の基礎制御として
無効化してはならない。

## Batch Regression をフォルダへ展開する場合

通常の Package 利用では不要。folder-based MCP が Skill ファイルを必要と
する場合だけ、Package をインストールした後に実行する。

```powershell
xrefkit-batch-regression install-mcp-skill `
  --repo C:\path\to\XRefKit
```

既存の展開先を更新する場合は `--force` を付ける。独自変更があるファイルを
上書きするため、実行前に Git 差分を確認する。

```powershell
xrefkit-batch-regression install-mcp-skill `
  --repo C:\path\to\XRefKit `
  --force
```

この処理の既定の展開先は
`skills/packs/batch-regression/batch-impact-regression` である。C# と
brownfield は、通常の entry point discovery を使う。

## GitHub ReleaseからSkillを同期する場合

PyPIに未登録のSkillを管理者がまとめて取得する場合は、GitHub Releaseの
Skill bundleをXRefKitから同期できる。bundleは `skills/` と `knowledge/`
を含むドメイン単位のZIPとして公開する。

```powershell
python -m xrefkit skills sync --bundle csharp
python -m xrefkit skills sync --all
```

既定では `synthaicode/XRefKit` のうち、bundle専用タグに対応する最新Releaseを取得し、現在のリポジトリの
`skills/`、`knowledge/`、`review_axes/`、`schemas/`へ登録する。同期状態は
`.xrefkit/skill-sync/`に記録される。前回同期したファイルは更新できるが、
手作業で存在するファイルは、確認なしには上書きしない。

更新内容を確認するだけの場合は、次を使う。

```powershell
python -m xrefkit skills sync --bundle csharp --dry-run --json
```

同期後にMCPサーバーを再起動すると、ライブカタログが最新のSkillとKnowledgeを
セマンティックルーティング対象として読み込む。同期は管理者の登録操作であり、
通常の利用者が個別Skillを選択する操作ではない。

## 更新

更新はインストール時と同じ Python 環境で行う。

```powershell
python -m pip install --upgrade xrefkit
python -m pip install --upgrade xrefkit-skills-batch-regression
python -m xrefkit package discover --json
```

Package の manifest にある `requires.xrefkit_core` と XRefKit のバージョンが
合わない場合は、無理に有効化せず、互換範囲を確認する。

## 使い分け

| 目的 | 実行すること |
|---|---|
| XRefKit 本体を使う | `python -m pip install xrefkit` |
| MCP サーバーを使う | `python -m pip install "xrefkit[mcp]"` |
| 公開 Package を追加する | `python -m pip install <distribution>` |
| CLI resolver で Package を使う | `--enabled-package` または `xrefkit.server.toml` |
| MCP で Package を使う | MCP と同じ Python 環境へインストール |
| PyPI 未公開 Skill を登録する | `python -m xrefkit skills sync` |
| folder-based MCP へ展開する | Package 固有の `install-mcp-skill` |

## 完了確認

次の3点が成功すれば、通常のローカル利用を開始できる。

```powershell
python -m xrefkit --help
python -m xrefkit package discover --json
python -m xrefkit show effective-skill <skill-id> `
  --mode tree `
  --enable-entry-point-discovery `
  --enabled-package <package-id>
```

`skills/_index.md` はリポジトリ内 Skill のカタログであり、Package の
インストールや発見では更新されない。リポジトリ内 Skill 自体を変更した
場合だけ、必要に応じて次を実行する。

```powershell
python -m xrefkit skill index --write
```
