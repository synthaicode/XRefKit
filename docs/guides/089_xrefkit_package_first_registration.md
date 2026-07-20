<!-- xid: 4F8C2A7D1E90 -->
<a id="xid-4F8C2A7D1E90"></a>

# XRefKit と Skill Package の初回登録

このガイドは、XRefKit 本体と PyPI などで配布された Skill Package を
初めて利用環境へ登録する手順を定義する。

## 1. XRefKit 本体をインストールする

PowerShell で利用する Python 環境を有効にした後、XRefKit 本体を
インストールする。

```powershell
python -m pip install --upgrade xrefkit
python -m xrefkit --help
```

リポジトリを開発対象として使う場合は、リポジトリルートで次を実行する。

```powershell
python -m pip install -e .
```

## 2. Skill Package をインストールする

Skill Package は XRefKit 本体とは別の Python 配布物である。例として、
バッチ回帰 Skill Package をインストールする。

```powershell
python -m pip install xrefkit-skills-batch-regression
```

C#、brownfield のパッケージを使う場合は、それぞれ次を実行する。

```powershell
python -m pip install xrefkit-skills-csharp
python -m pip install xrefkit-skills-brownfield
```

パッケージ名は PyPI の distribution name、登録時に使う package id は
パッケージ内の `package_manifest.yaml` に定義された `package_id` である。

| distribution | package id | 代表 Skill |
|---|---|---|
| `xrefkit-skills-batch-regression` | `xrefkit.skills.batch_regression` | `batch.impact_regression` |
| `xrefkit-skills-csharp` | `xrefkit.skills.csharp` | `csharp.review` |
| `xrefkit-skills-brownfield` | `xrefkit.skills.brownfield` | `brownfield.workflow` |

## 3. インストール済み Package を発見する

Python entry point に登録された Skill Package を確認する。

```powershell
python -m xrefkit package discover --json
```

ここで表示されるのは発見結果であり、まだ resolver の利用対象として
有効化されたことを意味しない。

## 4. Package を有効化する

単発の確認では、package id を明示して一覧を表示する。

```powershell
python -m xrefkit package list `
  --enabled-package xrefkit.skills.batch_regression
```

Skill の解決まで行う場合は、entry point discovery と package id の両方を
指定する。

```powershell
python -m xrefkit show effective-skill batch.impact_regression `
  --mode tree `
  --enable-entry-point-discovery `
  --enabled-package xrefkit.skills.batch_regression
```

複数の Package を使う場合は `--enabled-package` を繰り返す。

```powershell
python -m xrefkit show effective-skill csharp.review `
  --mode tree `
  --enable-entry-point-discovery `
  --enabled-package xrefkit.skills.csharp `
  --enabled-package xrefkit.skills.brownfield
```

継続利用するサーバー設定では、`xrefkit.server.toml` の
`[packages] enabled` に package id を記録する。

```toml
[packages]
enabled = [
  "xrefkit.skills.brownfield",
  "xrefkit.skills.csharp",
]
```

## 5. Core 互換性を確認する

Package の発見だけでは Core 互換性は確定しない。`package_manifest.yaml` の
`requires.xrefkit_core` と、インストールされている XRefKit のバージョンを
確認してから resolver に登録する。

```powershell
python -m pip show xrefkit
python -m xrefkit package discover --json
```

現行リポジトリで確認できる manifest の要求範囲には差がある。特に
`xrefkit.skills.batch_regression` と `xrefkit.skills.csharp` は現在の manifest
では `>=2.0.0 <3.0.0` を要求し、`xrefkit.skills.brownfield` は
`>=0.4.3 <0.5.0` を要求する。Core のバージョンが要求範囲を満たさない
場合、発見できても resolver では利用できない。

## 6. `skills/_index.md` との関係

PyPI Package のインストール、`package discover`、または
`--enabled-package` の指定は、リポジトリの `skills/_index.md` を更新しない。

`skills/_index.md` はリポジトリ内の catalog-visible な `meta.md` から、次の
コマンドで生成する。

```powershell
python -m xrefkit skill index --write
```

したがって、配布 Package の初回登録と、リポジトリの公開 Skill カタログへの
登録は別の作業である。

## 7. 既存 Skill のアップグレード

既存の Skill Package を更新する場合は、distribution name を指定して
XRefKit 本体または対象 Package を更新する。

```powershell
# XRefKit 本体を更新
python -m pip install --upgrade xrefkit

# 例: 既存の Skill Package を更新
python -m pip install --upgrade xrefkit-skills-batch-regression
python -m pip install --upgrade xrefkit-skills-csharp
python -m pip install --upgrade xrefkit-skills-brownfield
```

特定バージョンへ更新する場合は `==` を使う。

```powershell
python -m pip install --upgrade xrefkit-skills-csharp==0.1.0
```

更新後は、次の順で状態を確認する。

```powershell
python -m pip show xrefkit
python -m pip show xrefkit-skills-csharp
python -m xrefkit package discover --json
python -m xrefkit package list --json `
  --enabled-package xrefkit.skills.csharp
```

同じ package id の新バージョンは entry point discovery に反映されるが、
有効化は package id 単位で明示的に行う。`xrefkit.server.toml` を使っている
場合は、`[packages] enabled` の package id を変更する必要はない。

更新後に Skill の構成や依存 Knowledge が変わっていないか、代表 Skill の
実効結果を再確認する。

```powershell
python -m xrefkit show effective-skill csharp.review `
  --mode tree `
  --enable-entry-point-discovery `
  --enabled-package xrefkit.skills.csharp
```

更新で Core 互換性エラーが出た場合は、Package を無理に有効化せず、
`package_manifest.yaml` の `requires.xrefkit_core` と XRefKit 本体の
バージョン範囲を確認する。複数 Package を同時に更新した場合は、問題の
Package を1つずつ切り分ける。

リポジトリ内の Skill を更新した場合だけ、必要に応じて次を実行して
`skills/_index.md` を再生成する。PyPI Package の更新だけでは実行しない。

```powershell
python -m xrefkit skill index --write
```

### アップグレード完了条件

- 本体と対象 Package のインストール済みバージョンを確認した。
- `package discover --json` で新バージョンを確認した。
- Core 互換性を確認した。
- `package list` または server config で対象 package id が有効になっている。
- 代表 Skill の `show effective-skill` を再確認した。
- リポジトリ内 Skill を変更した場合だけ `skill index --write` を実行した。

## 8. Batch Regression の materialize Skill を更新する場合

`xrefkit-skills-batch-regression` には、entry point discovery とは別に、
folder-based MCP 用の Skill 資産をリポジトリへ展開する CLI がある。

初回展開は次のコマンドで行う。

```powershell
xrefkit-batch-regression install-mcp-skill `
  --repo C:\path\to\xrefkit-repository
```

既存の展開済み Skill を Package の更新版で置き換える場合は、Package を
先に更新してから `--force` を付けて再実行する。

```powershell
python -m pip install --upgrade xrefkit-skills-batch-regression
xrefkit-batch-regression install-mcp-skill `
  --repo C:\path\to\xrefkit-repository `
  --force
```

既定の展開先は次のディレクトリである。

```text
skills/packs/batch-regression/batch-impact-regression
```

`--force` は既存ファイルを置き換えるため、実行前に対象ディレクトリの
Git 差分と、ローカルで独自変更したファイルがないことを確認する。
materialize 後は folder-based MCP サーバーを再起動する。

この CLI は `batch-regression` Package 固有の展開処理である。C# や
brownfield の Package は、通常 `package discover` と entry point discovery
による runtime 登録を使い、同じ `install-mcp-skill` コマンドがあるとは
仮定しない。

## 9. 指定フォルダ以下の既存 Skill を変換する

外部 Skill フォルダを XRefKit の Skill／Knowledge 分離形式へ変換する
一般 CLI は `skill import --batch` である。これは PyPI Package の discovery
や `batch-regression` 固有の MCP materialize とは別の処理である。

変換対象の親フォルダは、`skills/` と任意の `knowledge/` を持つ構成にする。

```text
external-root/
├─ skills/
│  ├─ skill-a/
│  │  └─ SKILL.md
│  └─ skill-b/
│     └─ SKILL.md
└─ knowledge/   # 任意
```

親フォルダ以下の Skill をまとめて変換する。

```powershell
python -m xrefkit skill import `
  C:\path\to\external-root `
  --batch `
  --skill-id-prefix imported `
  --json
```

互換 wrapper を使う場合は次のとおりである。

```powershell
python tools/convert_to_xrefkit_skill.py `
  C:\path\to\external-root `
  --batch `
  --skill-id-prefix imported `
  --json
```

既定の出力先は次のとおりで、private 境界に出力される。

```text
skills_private/imported.<skill-folder>/
knowledge/imported_skills/imported/
```

変換処理は、Skill 文書の走査、参照 Markdown／TXT の Knowledge 分離、
不足 XID の付与、Knowledge リンクの XID 化、`meta.md` の生成を行う。
変換計画だけを確認する場合は `--dry-run` を使う。

```powershell
python -m xrefkit skill import `
  C:\path\to\external-root `
  --batch `
  --skill-id-prefix imported `
  --dry-run `
  --json
```

公開 Skill として扱う場合だけ、変換後の内容を `skills/` へ昇格し、
`skills/_index.md` を更新する。既定の変換先である `skills_private/` は
公開カタログへ自動登録されない。

## 初回登録の完了条件

- `python -m xrefkit --help` が成功する。
- 対象 distribution が `pip show` で確認できる。
- `package discover --json` に対象 package id とバージョンが出る。
- `package_manifest.yaml` の Core 互換性を満たしている。
- `package list` または `show effective-skill` で明示的な有効化結果を確認する。
- リポジトリの公開 Skill カタログを更新する場合だけ `skill index --write` を実行する。
