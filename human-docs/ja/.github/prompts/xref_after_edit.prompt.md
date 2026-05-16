# xref: ドキュメント編集後の整合性更新

目的: このリポジトリの Markdown 運用（XID 主キー / リンク破綻防止）を崩さずに変更を完了する。

## 手順

1. 変更対象の Markdown を編集する（XID ブロックは削除しない）
2. 変更後、次を順に実行する

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check --review
```

3. `xref init` により XID が付与された（=XID 一覧が変わった）場合のみ、索引用の一覧を再生成する（任意）

```powershell
python -m fm xref index > .xref/xid-index.json
```

4. `xref check` が失敗したら、出力に従ってリンクを修正し、再度 `rewrite` / `check` を通す

## 「同じ XID のままでよいか」の判断が必要なとき

内容の意味が大きく変わり、XID を分けるべきだと判断した場合は、旧ページを消さずに後継ページへ誘導する。

```powershell
python -m fm xref deprecate <OLD_XID> <NEW_XID> --note "変更理由（任意）"
python -m fm xref rewrite
python -m fm xref check --review
```

## 注意

- 既存ページの XID は変更しない
- 参照は `#xid-...` を含むリンクを使う
