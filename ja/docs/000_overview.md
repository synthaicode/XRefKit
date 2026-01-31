<!-- xid: 7C6C2B46A9D1 -->
<a id="xid-7C6C2B46A9D1"></a>

# 概要

このリポジトリは、原本（PDF/Excel/Web など）をリポジトリ内に保持しつつ、AI が参照しやすい形（断片 Markdown）に整備し、改名・移動・分割・統合があっても参照が壊れにくい運用を実現するための作業場です。

## 重要な課題

- agent 設計は分割が避けられない（コンテキスト制約）
- 人間向け説明（`docs/`）と agent 向け契約（`agent/`）は別粒度が必要
- ファイル数が増えるほどリンク管理が破綻しやすい

## 対応方針: XID で参照する

参照は「パス」ではなく **XID** を主キーにします。

- 各ファイルは XID を持つ
- 管理リンクは `#xid-<XID>` を含む
- 改名/移動後は `python -m fm xref rewrite` がリンクのパス部分だけを更新する

## AI が行う XID 運用（重要）

「AI が XID を管理する」とは、AI が値を採番することではなく、`fm` のコマンドで **XID/リンク整合性を維持する**ことです。

- XID の付与/置換は `python -m fm xref init` が行う（AI は実行して結果を解釈する）
- `init` / `rewrite` / `check` を回し、`issues: 0` にする
- 参照解決のために `.xref/xid-index.json` をキャッシュとして使える

## リポジトリ構成（最小）

- `docs/`: 人間向けドキュメント（背景、設計、運用、索引）
- `agent/`: agent 向け入口・運用契約（L0を短く固定）
- `fm/`: CLI 実装（`python -m fm ...`）
- `sources/`: 原本（PDF/Excel/Web 等）。人間が確認できる出典
- `.github/`: Copilot/CI など GitHub 側の制御面

運用フロー: [運用フロー](010_workflow.md#xid-7D1E1C0279F1)

agent 側入口: [Agent 入口](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
