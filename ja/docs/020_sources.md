<!-- xid: 2FAD591BF725 -->
<a id="xid-2FAD591BF725"></a>

# ソース（PDF/Excel/Web）取り込みと参照

このリポジトリでは、元データ（PDF/Excel/Web など）を **リポジトリ内に保存**し、人間がいつでも確認できる状態にします。

重要: **取り込み対象の元データは事前に分割する必要はありません。**（元の PDF/Excel/HTML 等をそのまま置く）

AI が参照する“知識”は `docs/` 側の Markdown（XID 付き断片）を正本とし、元データは **出典（source of truth）**として紐づけます。

## 置き場所

- 元データ（バイナリ/HTML スナップショットなど）: `sources/`
- AI 参照用の知識（断片 Markdown）: `docs/`

## 取り込みの基本パイプライン

1. `sources/` に元データを追加する（PDF/Excel/HTML など）
2. 元データを読み、`docs/` に “1ページ=1断片” で Markdown を追加/更新する
3. 変更の最後に `python -m fm xref init` / `rewrite` / `check` を回し、`issues: 0` にする

## 出典の書き方（推奨）

断片 Markdown の末尾に、出典を必ず残します（機械可読な最低限の情報）。

例（PDF）:

```md
## 出典

- source_type: pdf
- source_path: ../sources/vendor/product/spec-2026-01.pdf
- source_locator: page=12-14
- extracted_at: 2026-01-31
```

例（Web）:

```md
## 出典

- source_type: web
- source_url: https://example.com/docs/feature
- captured_path: ../sources/web/example.com/feature-2026-01-31.html
- captured_at: 2026-01-31
```

## AI の運用（重要）

- AI は元データ全体を毎回読むのではなく、まず `docs/000_index.md` と `python -m fm xref search/show` で該当断片を探して読む
- 元データが必要な時だけ、出典情報から `sources/` の該当箇所（ページ/シート/URL）を辿る
