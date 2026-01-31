# XRefKit（Claude Code / 日本語）

このリポジトリは、改名・移動・分割・統合があってもリンク破綻を抑えるために **XID** を主キーとして運用します。

## 入口（必ず最初に参照）

- 人間向け入口: `docs/000_index.md`
- agent契約: `agent/000_agent_entry.md`

## Contract（必須）

- 参照は `#xid-...` を含むリンクを使う（パスは可変）
- 既存 XID は変更しない
- 不足情報は推測で埋めない（`python -m fm xref search/show` で該当 XID を探す）

## 作業後（整合性）

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
python -m fm xref check --review
```
