# XRefKit（日本語）

XRefKit は「AI と知識を共有する」ための OSS 知識運用ツールキットです。

リポジトリ内に原本（PDF/Excel/Web スナップショットなど）を保持しつつ、AI が参照しやすい形として Markdown の断片（フラグメント）を整備します。文書間参照は安定ID（**XID**）を主キーにすることで、改名・移動・分割・統合があってもリンク破綻を抑えます。
この構成では `xref` は脇役の補助機能で、主目的は Skill/agent とドメイン知識断片を正しく結びつけることです。

## 入口

- 人間向け入口: `docs/000_index.md`
- agent 契約（常に読む）: `agent/000_agent_entry.md`

AI ベンダー別の起動ファイルは最小限にし、`xref` で知識を読む導線だけ示します。詳細ルールは上記入口へ一元化します。

## クイックスタート

```powershell
# 1) Python 環境を確認
python --version

# 2) 一括メンテナンスを実行
python -m fm xref fix

# 3) 必要な知識断片を検索・表示
python -m fm xref search "query"
python -m fm xref show 1A2B3C4D5E6F
```

`xref fix` で問題が出た場合は、まずその解消を優先してから手動リンク編集を行ってください。

## XID とは

知識をファイル分割すると、リンクが壊れやすくなります。XRefKit では `#xid-...` を参照の主キーとし、ファイル移動後はリンクの「パス部分」だけを自動で更新します。

各 Markdown には XID ブロックを持たせます。

```md
<!-- xid: 1A2B3C4D5E6F -->
<a id="xid-1A2B3C4D5E6F"></a>
```

## 典型ワークフロー

1. 原本を `sources/` に追加・更新する。
2. 要点を `docs/` または `knowledge/` の Markdown 断片に反映する。
3. 参照はパス依存ではなく XID（`#xid-...`）で張る。
4. 編集後に `python -m fm xref fix` を実行する。
5. `xref search/show` または `ctx pack` で必要最小限の文脈を取り込む。

## XRefKit の価値（リンク管理以外）

- **Skill 駆動の実行**: `skills/` に多様な再利用可能 Skill を集約し、`skills/_index.md` からルーティングする。
- **判断履歴の追跡可能性**: `work/` に AI 実行ログを共有し、意思決定や引き継ぎの経緯をたどれる。
- **知識の正規化**: `knowledge/` を共通の正本として、agent/tool 側は XID 参照で接続する。
- **指示と知識の疎結合**: 「振る舞い」は薄く安定化し、「知るべきこと」は必要時に取得する（`xref search/show`, `ctx pack`）。

## コマンド

```powershell
# XID の付与/置換（不足を埋める）
python -m fm xref init

# #xid-... を含む「管理リンク」の相対パスを更新
python -m fm xref rewrite

# XID とリンクの検査
python -m fm xref check

# まとめて整合（init + rewrite + check）
python -m fm xref fix

# 人間レビュー用ヒント（best-effort）
python -m fm xref check --review

# 探して、必要な分だけ読む
python -m fm xref search "query"
python -m fm xref show 1A2B3C4D5E6F

# コンテキストパック（seed + 近傍）
python -m fm ctx pack --seed 7C6C2B46A9D1 --depth 1 --out .xref\\pack.md
```

`python -m fm xref check` と `python -m fm xref fix` は、問題がある場合に終了コード `1` を返します（CI で失敗検知可能）。

## リポジトリ構成

- `docs/`: 人間向けの運用ドキュメントとポリシー
- `knowledge/`: 共有ドメイン知識の断片
- `sources/`: 人間検証用の原本
- `skills/`: スキル定義とルーティング索引（`skills/_index.md`）
- `work/`: AI 実行ログとふりかえり（判断履歴の共有）
- `agent/`: agent エントリと契約
- `fm/`: CLI 実装（`xref`, `ctx`）
