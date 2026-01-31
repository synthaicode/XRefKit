<!-- xid: D0E1327DDD7F -->
<a id="xid-D0E1327DDD7F"></a>

# フォルダ構成（人間向け）

このリポジトリは「分割されたドキュメントを XID で参照し、改名/移動/分割/統合後もリンク破綻を防ぐ」ための運用とツール一式です。

## トップレベルの役割

- `docs/`: 人間向けドキュメント（背景、設計、運用、索引）
- `agent/`: agent 向け入口・運用契約（L0を短く固定）
- `fm/`: CLI 実装（`python -m fm ...`）
- `sources/`: 原本（PDF/Excel/Web 等）。人間が確認できる出典
- `.github/`: Copilot/CI など GitHub 側の制御面
- `.cursor/`: Cursor 向けのルール定義

## 生成物/キャッシュ

- `.xref/`: 生成物（例: `.xref/xid-index.json`、`ctx pack` の出力など）
  - 通常は Git 管理しない（`.gitignore` 対象）

## 入口

- 人間向け入口: `docs/000_index.md`
- agent 向け入口: `agent/000_agent_entry.md`
