# AI運用基盤としての XRefKit（要約）

このリポジトリは、単なる XID リンク維持ツールではありません。現在は、AI を安定して運用するための基盤として次をまとめて管理します。

- AI の運用規約
- 知識の読み方と境界
- Skill と Knowledge の作業構造（汎用 protocol と semantic routing で制御）
- 原本に裏づけられた知識断片
- XID による安定参照

## 何が変わったのか

初期は「XID を使ってリンクを壊さない」ことが前面に見えていました。

現在はそれに加えて、

- AI が何を勝手に変えてはいけないか
- 何を知識として読み、何を証拠として扱うか
- 不明点をどう扱うか
- どの単位で仕事を分けるか

をリポジトリ内で明示することが重要になっています。

## いまの読み方

人間が最初に読むなら、次の順がわかりやすいです。

1. `human-docs/ja/000_overview.md`
2. `human-docs/ja/001_principles.md`
3. `human-docs/ja/010_workflow.md`
4. `human-docs/ja/002_structure.md`

必要に応じて、

- 取り込みを見るときは `human-docs/ja/003_import_for_humans.md`
- 原本と出典の扱いを見るときは `human-docs/ja/020_sources.md`
- 発表用資料を見るときは `human-docs/ja/054_*` 以降

を読みます。

## 役割分担

- `sources/`
  - 人間が確認する原本
- `knowledge/`
  - AI が参照する知識断片
- `skills/`
  - 具体的な実行手順
- `agent/`
  - AI の入口契約
- `docs/`
  - 人間向けの説明と運用整理

## 位置づけ

XID は今でも重要です。ただし役割は「主役」ではなく、AI の運用と知識接続を壊さないための下支えです。
