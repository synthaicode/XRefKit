# xref: 推測せず探して読む（search → show）

目的: 不足情報がある時に、推測で埋めずに適切なドキュメント断片（XID）を参照してから作業する。

## 手順

1. まず `docs/000_index.md` を読む
2. 調べたいテーマをクエリにして検索する

```powershell
python -m fm xref search "<query>"
```

3. 候補 XID を必要な分だけ表示する

```powershell
python -m fm xref show <XID>
```

4. 読んだ XID を作業メモとして列挙してから、変更・実装に進む
