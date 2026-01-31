# Instructions（XRefKit / 日本語）

このリポジトリは、文書分割によるリンク破綻を防ぐために **XID** を主キーとして運用します。

## Entry points

- `docs/000_index.md`（人間向け入口）
- `agent/000_agent_entry.md`（agent契約）

## Contract

- 参照は `#xid-...` を含むリンクを使う（パスは変わる前提）
- 既存の XID を変更/削除しない
- 不足情報は推測で埋めない（`python -m fm xref search/show` で必要な断片を探して読む）

## Commands

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
python -m fm xref check --review
```
