# agent: 変更反映（改名/移動/分割/統合）

目的: 改名・移動・分割・統合を行っても、参照（XIDリンク）が破綻しない状態を維持する。

## 作業ルール

- 既存ページの XID は変更しない / 消さない
- `#xid-...` を含むリンクを管理リンクとして扱う
- 破綻検出は `xref check`（`issues: 0` まで直す）

## 手順

1. 改名/移動/分割/統合を実施する
2. 整合性を回復する

```powershell
python -m fm xref rewrite
python -m fm xref check
```

3. 新規 Markdown を作った場合は `xref init` も行う

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
```
