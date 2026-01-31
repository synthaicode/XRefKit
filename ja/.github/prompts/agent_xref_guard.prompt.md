# agent: xref 守衛（破綻を止める）

目的: 変更により発生したリンク破綻（管理リンク）を、最小の修正で `issues: 0` に戻す。

## 手順

1. 現状を確認する

```powershell
python -m fm xref check
```

2. 改名/移動が原因なら、まず機械的に回復する

```powershell
python -m fm xref rewrite
python -m fm xref check
```

3. まだ壊れている場合は、`xref check` の指摘に従ってリンクを修正する
4. 最後に `issues: 0` になるまで `xref check` を繰り返す
