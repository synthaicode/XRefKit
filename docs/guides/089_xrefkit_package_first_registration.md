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

`xrefkit` コマンドが PATH に見つからない場合は、常に次の module 形式を
使える。

```powershell
python -m xrefkit --help
```

## 既存 Skill を import して VS Code MCP で使う場合

管理者は、既存 Skill の取り込みと MCP 接続用の設定例を一度に準備できる。
設定ファイルや `AGENTS.md`／`CLAUDE.md` の追記文は、リポジトリへ直接書かず、
確認用の一時フォルダへ出力される。

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
依頼する。Skill の選択と実行は MCP の semantic routing が担当する。

## Skill Package を追加する場合

必要な Package だけをPyPIからインストールする。

```powershell
python -m pip install xrefkit-skills-batch-regression
python -m pip install xrefkit-skills-csharp
python -m pip install xrefkit-skills-brownfield
```

## 発見と有効化を確認する

まず、インストール済み Package を発見する。

```powershell
python -m xrefkit package discover --json
```

発見結果には、Package の `package_id` とバージョンが表示される。発見
だけでは resolver の利用対象にならないため、使用する package id を明示して
有効化する。

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

既定では `synthaicode/XRefKit` の最新Releaseを取得し、現在のリポジトリの
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
| XRefKit をローカルで使う | `python -m pip install xrefkit` |
| 公開 Package を使う | `python -m pip install <distribution>` |
| Package を resolver で使う | `package discover` 後に `--enabled-package` |
| MCP 用 Skill フォルダを作る | `install-mcp-skill`（Batch Regression 固有） |

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
