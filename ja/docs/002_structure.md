<!-- xid: D0E1327DDD7F -->
<a id="xid-D0E1327DDD7F"></a>

# フォルダ構成（人間向け）

このリポジトリは、AI の運用規約・知識ルーティング・作業構造・XID による安定参照をまとめて扱う基盤です。

## トップレベルの役割

- `docs/`: 人間向けドキュメント（背景、設計、運用、索引）
- `flows/`: 機械可読なワークフロー定義
- `capabilities/`: 再利用可能な能力定義
- `knowledge/`: 共有ドメイン知識の断片
- `agent/`: agent 向け入口・運用契約（L0を短く固定）
- `fm/`: CLI 実装（`python -m fm ...`）
- `sources/`: 原本（PDF/Excel/Web 等）。人間が確認できる出典
- `skills/`: 実行用 Skill とルーティング索引
- `.github/`: Copilot/CI など GitHub 側の制御面
- `.cursor/`: Cursor 向けのルール定義

## 生成物/キャッシュ

- `.xref/`: 生成物（例: `.xref/xid-index.json`、`ctx pack` の出力など）
  - 通常は Git 管理しない（`.gitignore` 対象）

## 入口

- 人間向け入口: `docs/000_index.md`
- agent 向け入口: `agent/000_agent_entry.md`
