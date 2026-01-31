# agent: 文書作成（docs へ知識を固定する）

目的: 調査結果・決定事項・運用ルールを、将来も参照できる “1ページ=1断片” の Markdown として `docs/` に追加する。

## 作業ルール

- 参照は `#xid-...` を含むリンクを使う（パスは可変）
- 既存ページの XID は変更しない
- 新規ページの XID は採番しない（最後に `xref init` を実行して付与する）

## 手順

1. `docs/000_index.md` から関連ページを辿り、必要なら `python -m fm xref search/show` で既存知識を確認する
2. 新規ファイル `docs/<NNN>_<slug>.md` を作り、単体で意味が通るように書く（前提/目的/手順/例/例外など）
3. 仕上げに整合性を取る

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
```

4. `xref check` が `issues: 0` になることを確認して完了
