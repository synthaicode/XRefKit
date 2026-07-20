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

## 初回登録の完了条件

- `python -m xrefkit --help` が成功する。
- 対象 distribution が `pip show` で確認できる。
- `package discover --json` に対象 package id とバージョンが出る。
- `package_manifest.yaml` の Core 互換性を満たしている。
- `package list` または `show effective-skill` で明示的な有効化結果を確認する。
- リポジトリの公開 Skill カタログを更新する場合だけ `skill index --write` を実行する。
