# agent: 知識抽出（再利用できる断片にする）

目的: 既存のメモ・ログ・設計資料・会話ログなどから、再利用できる “断片” として `docs/` に固定する。

## 判断（再利用 vs 新規抽出）

- まず既存 docs を検索し、足りない差分だけを追加する

```powershell
python -m fm xref search "<query>"
python -m fm xref show <XID>
```

- 既存が十分なら新規ページを増やさず、参照（XIDリンク）を張って終える

## 抽出の出力形式（推奨）

新規ページは “1ページ=1断片” を守る。

- 何が分かるか（結論）
- いつ/どの条件で使えるか（適用条件）
- 手順（箇条書きで短く）
- 例（あれば）
- 関連 XID 参照

## 仕上げ

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
```
