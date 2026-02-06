<!-- xid: 0B5C58B5E5B2 -->
<a id="xid-0B5C58B5E5B2"></a>

# Agent 入口（L0 / 常に読む）

このファイルは agent 側の入口です。人間向けの背景は `docs/` に置き、ここでは **運用の契約（Contract）**だけを短く保ちます。

関連: [概要](../docs/000_overview.md#xid-7C6C2B46A9D1)

## Contract（必須）

- 参照は XID を主キーにする（リンクには `#xid-...` を含める）
- Skill 指示とドメイン知識はファイルを分離して管理する
- `docs/` のドメイン知識は共通資産として扱い、Skill 側は必要な断片だけ都度参照する
- 不足情報がある場合は推測で埋めず、まず参照すべき XID を探して読む
- 改名/移動/分割/統合後はリンク検査を通す（`xref check`）

## 参照の取り方（固定手順）

1. 入口（`docs/000_index.md`）を読む
2. `python -m fm xref search "<query>"` で候補 XID を出す
3. `python -m fm xref show <XID>` で必要なページだけ読む

## Skill 実行時における xref の役割

Skill の実行中にドメイン知識が必要になった場合、`xref` は導線として機能します。

1. 意図やキーワードで候補断片を探す（`xref search`）
2. 必要な断片だけを解決して読む（`xref show`）
3. XID を根拠にして Skill の処理を続行する
