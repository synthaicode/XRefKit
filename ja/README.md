# XRefKit（日本語）

XRefKit は「AI と知識を共有する」ための OSS 知識運用ツールキットです。

リポジトリ内に原本（PDF/Excel/Web スナップショットなど）を保持しつつ、AI が参照しやすい形として Markdown の断片（フラグメント）を整備します。文書間参照は安定ID（**XID**）を主キーにすることで、改名・移動・分割・統合があってもリンク破綻を抑えます。

**入口**

- 人間向け入口: `docs/000_index.md`
- agent 契約（常に読む）: `agent/000_agent_entry.md`

## XID とは

知識をファイル分割すると、リンクが壊れやすくなります。XRefKit では `#xid-...` を参照の主キーとし、ファイル移動後はリンクの「パス部分」だけを自動で更新します。

各 Markdown には XID ブロックを持たせます。

```md
<!-- xid: 1A2B3C4D5E6F -->
<a id="xid-1A2B3C4D5E6F"></a>
```

## コマンド

```powershell
# XID の付与/置換（不足を埋める）
python -m fm xref init

# #xid-... を含む「管理リンク」の相対パスを更新
python -m fm xref rewrite

# XID とリンクの検査
python -m fm xref check

# 人間レビュー用ヒント（best-effort）
python -m fm xref check --review

# 探して、必要な分だけ読む
python -m fm xref search "query"
python -m fm xref show 1A2B3C4D5E6F

# コンテキストパック（seed + 近傍）
python -m fm ctx pack --seed 7C6C2B46A9D1 --depth 1 --out .xref\\pack.md
```
