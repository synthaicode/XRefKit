# Copilot instructions（日本語 / XRefKit）

このリポジトリでは、文書分割によるリンク破綻を防ぐために **XID** を主キーとして運用します。

## 入口（最初に参照）

- 人間向け入口: `docs/000_index.md`
- agent 契約: `agent/000_agent_entry.md`

## 絶対に守るルール（Contract）

- 参照は `#xid-...` を含むリンクを使う（パスは変わる前提）
- 既存 XID は変更しない
- 不足情報は推測で埋めない（`python -m fm xref search/show` で該当 XID を探して読む）

## XID はコマンドで付与する（採番しない）

作業後は次を実行する（ローカルで実行できる場合）。

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
python -m fm xref check --review
```

補足: `.xref/xid-index.json` は XID→パスのキャッシュ/索引です。参照解決の高速化に使えますが、最新化は `xref check` / `xref index` を実行して行います。
