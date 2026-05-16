# sources/（日本語）

このディレクトリには、元データ（PDF/Excel/Web の保存物など）を置きます。

- 目的: 人間がいつでも確認できる “出典” を、リポジトリ内に保持する
- 注意: AI が参照する “知識の正本” は `docs/` の XID 付き Markdown とする

## 推奨構成（例）

- `sources/pdf/...`
- `sources/excel/...`
- `sources/web/<domain>/...`

## docs からの参照

`docs/` の断片 Markdown 末尾に `source_path` / `source_locator` などの形で、参照元を必ず残します。

詳細: `docs/020_sources.md`
