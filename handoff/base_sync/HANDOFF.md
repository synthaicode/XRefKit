# 引継ぎ: XRefKit 基盤同期の吸収作業(ローカル側AI向け)

あなた(ローカル側AI)への引継ぎ文書です。目的は、**XRefKit 基盤リポジトリの更新を、ローカルで改変・追加されたコピーへ安全に取り込む**ことです。差分の検出・分類は同梱の Python ツールが決定的に行い、あなたは分類済みの作業リストを規則に従って1件ずつ処理します。

## 大原則(この3つに反する行動は禁止)

1. **ツールの分類は候補であり、判定はあなたと人間が行う。** ただし `both_changed` など `requires: human_review` の項目を自動マージすることは**禁止**。人間に提示して判断を仰ぐ。
2. **XIDは不変。** 既存文書のXID宣言(`<!-- xid: ... -->` と `<a id="xid-...">`)を書き換えない・削除しない。
3. **1件ずつ処理し、全件に記録を残す。** 各項目の `status` を `resolved` または `escalated` に更新し、何をしたかを1行で記録する。黙って飛ばさない。

## 同梱物と前提

| ファイル | 役割 |
|---|---|
| `HANDOFF.md` | 本書 |
| `xrefkit_sync_worklist.py` | 差分調査ツール(stdlib のみ、読み取り専用) |
| `base-history-manifest.json` | 基盤ブランチ `codex/sync-main-without-mp4-action` の全履歴(XID→ハッシュ) |
| `export_base_manifest.py` | 参考: マニフェストの生成元(基盤側で実行するもの。ここでは使わない) |
| `../../ownership.yaml` | パス所有権と同期対象 zone の宣言 |

必要環境: Python 3.11+。git は不要。

## Zone 前提

この同期は `ownership.yaml` の `base_sync: true` zone だけを通常の吸収対象にする。

- `packs/local/` はローカル専用 zone。基盤同期の作業項目として扱わない
- `packs/<pack>/` は shared pack zone。基盤側で追加・移動された内容は XID ベースで追跡する
- `site/`, `human-docs/`, `work/`, `observations/` は通常の基盤吸収対象ではない
- `handoff/` は delivery zone。同期手順とツール自体を配布するため、基盤同期対象に含める

追加で必要な入力:
- **ローカルコピー**のパス(このリポジトリを基に改変してきたフォルダ)
- **基盤の現在ツリー**: GitHub `synthaicode/XRefKit` のブランチ `codex/sync-main-without-mp4-action` を「Download ZIP」して展開したフォルダ(git 不要)

## Step 1: 差分調査を実行する

```powershell
python xrefkit_sync_worklist.py `
  --manifest base-history-manifest.json `
  --local <ローカルコピーのパス> `
  --base-tree <展開した基盤ZIPのパス> `
  --out-dir sync-report
```

出力:
- `sync-report/sync-worklist.json` — あなたが処理する作業リスト
- `sync-report/sync-worklist.md` — 件数サマリと要レビュー一覧
- `sync-report/diffs/*.diff` — レビュー対象の差分

最初に `sync-worklist.md` の `copy point` の `match_ratio` を確認すること。**90%未満の場合は作業を中断し、人間に報告**(コピー元の特定が疑わしい)。

## Step 2: kind ごとの処理規則

以下の順序で処理する。各項目を処理したら worklist の `status` を更新する。

### 2-1. 自動処理してよいもの(先に片付ける)

| kind | 処理 |
|---|---|
| `unchanged` / `converged` / `converged_addition` / `mutually_deleted` | 何もしない。`resolved` にする |
| `base_only_advanced` | ローカルは触っていない文書。`--base-tree` の該当ファイル(`head_path`)をローカルの該当パスへ上書きコピー |
| `base_new` | 基盤の新規文書。`--base-tree` からローカルの同じ相対パスへコピー |
| `moved_in_base` | 内容同一・基盤側で移動。ローカルのファイルを `head_path` の位置へ移動(参照はXIDベースなので壊れない)。shared pack への移動もこの分類で扱う |
| `base_deleted_local_unchanged` | ローカルでも削除 |

### 2-2. 判断を伴うもの(あなたの裁量で処理し、理由を記録する)

**`no_xid_local_addition`(XIDのない ローカル追加)— 新規として取り込む:**
1. 新規XIDを採番する(下記「XID採番手順」)
2. ファイル先頭に宣言を追加:
   ```markdown
   <!-- xid: XXXXXXXXXXXX -->
   <a id="xid-XXXXXXXXXXXX"></a>
   ```
3. ローカルPack(`packs/local/<システム名>/knowledge/` 等)へ配置する
4. **この新規XIDを参照すべきSkillの差分吸収**: 関連するローカルSkill・フォークSkillの `knowledge_refs` や本文参照を、新規XIDを指すように更新する。どのSkillが参照すべきかの判断はあなたの裁量。ただし更新した各Skillについて「なぜ参照させたか」を1行記録すること

**`local_addition`(XIDのあるローカル追加):** ローカルPackへ配置(XIDはそのまま)。上記4と同じ参照吸収を行う。

**`local_only_modified`(ローカルだけが変えた基盤文書)— ラダー分類:**
1. 差分(`diffs/`)を読み、変更の正体を判定する:
   - **ローカル事実**(対象コードの構造・規約・プロジェクト固有情報)→ その部分を切り出して ローカルPackの knowledge 断片(新規XID)にし、元ファイルは基盤版に戻して knowledge 参照に置き換える
   - **パラメータ**(閾値・対象・オプション)→ bindings に外出しできるならそうする
   - **純粋な手順改善** → フォークとして正式化する。Skill の meta.md に以下を追記:
     ```markdown
     - forked_from: `<元のskill_id>`
     - fork_base_hash: `<worklist の fork_base_hash の値をそのまま転記>`
     - fork_disposition: local_only
     - fork_reason: <1行で>
     ```
2. 判定に迷う場合は `escalated` にして人間へ

**`absorbed_into`(基盤側で他文書に統合されたXID):** ローカル内の参照を `absorbed_into` の示す統合先XIDへ張り替える。ローカルがその文書を改変していた場合(`requires: human_review` 付き)は人間へ。

### 2-3. 人間へエスカレーションするもの(自動マージ禁止)

`both_changed` / `base_deleted_local_modified` / `local_deleted` / `xid_collision` は、diff と状況説明を添えて人間に提示し、`escalated` にする。**あなたがマージ内容を決めてはいけない。**

## XID採番手順(git・fm がない環境向け)

1. 16進大文字12桁をランダム生成する(例: Python で `secrets.token_hex(6).upper()`)
2. 一意性を確認する: worklist 内の全 `key` と、ローカル全体の `grep -r "xid: XXXXXXXXXXXX"` の両方でヒットゼロであること
3. 衝突したら再生成

## Step 3: 完了条件と報告

以下がすべて満たされたら完了:

- [ ] worklist の全項目が `resolved` か `escalated`
- [ ] `escalated` 一覧(diff 参照付き)を人間向けにまとめた
- [ ] 変更ログを1ファイル作成した: 日付_sync_absorption.md(処理件数、フォーク宣言した Skill、採番した新規XID、参照を張り替えた Skill とその理由)
- [ ] ローカルに `python -m xrefkit` がある場合: `python -m xrefkit xref fix` を実行しリンク整合を確認(なければスキップし、その旨を記録)

## 背景(なぜこの方式か)

- 差分は**パスではなくXIDで**突合している。基盤はファイルを頻繁に移動・改名するが(実績: docs/ 再編成で25文書が移動)、XIDが同一なら同じ文書として追跡され、偽の衝突が出ない
- ハッシュは「XIDリンク正規化+改行正規化後の sha256」で、XRefKit MCP の `content_hash` と同じ言語。`fork_base_hash` はそのまま MCP の検証やドリフト検知と突合できる
- 方針の出典: 基盤リポジトリに対して差分を取り込む/XIDがないものは新規として取り込む/新規XIDを参照するSkillの差分吸収はローカル側AIの裁量/`both_changed` の自動マージ禁止(propose-approve 運用)
