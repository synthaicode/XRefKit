<!-- xid: 7D1E1C0279F1 -->
<a id="xid-7D1E1C0279F1"></a>

# 運用フロー（リンク破綻を防ぐ）

## ルール（最小）

- Markdown ファイルは先頭付近に XID ブロックを保持する
- 他ファイル参照は `#xid-<XID>` を含むリンクで行う
- 改名/移動/分割/統合の後に `python -m fm xref rewrite` を実行する
- 破綻検出は `python -m fm xref check` を CI などで継続実行する
- まとめて整合を取りたい場合は `python -m fm xref fix` を使う（init + rewrite + check）
- 更新時の人間レビュー用ヒントは `python -m fm xref check --review` を使う（best-effort）

## 他の AI がこのリポジトリを使う時の手順（固定）

1. `docs/000_index.md` を読む（入口）
2. 目的に近いページを `python -m fm xref search` で探し、読む XID を列挙する
3. 列挙した XID を `python -m fm xref show <XID>` で必要な分だけ読む
4. 作業し、参照した XID 一覧を作業ログとして残す

Skill 実行中に追加のドメイン知識が必要になった場合も、同じ導線を都度使います。  
`xref search` -> `xref show` -> 取得した XID 文脈で Skill を再開する、という流れです。

## よくある操作

### ファイル追加

1. `docs/` または `agent/` に Markdown を追加
2. `python -m fm xref init` で XID 付与
3. 必要なら `python -m fm xref rewrite`

### ソース取り込み（PDF/Excel/Web → docs）

元データは `sources/` に保存し、人間がいつでも確認できる状態にします。AI が参照する知識は `docs/` の Markdown（XID 付き断片）を正本にします。

1. `sources/` に元データを追加する
2. 元データを読み、`docs/` に “1ページ=1断片” で Markdown を追加/更新する（断片の末尾に出典を残す）
3. 仕上げに整合性を回す

```powershell
python -m fm xref fix
```

詳細: [ソース取り込み（PDF/Excel/Web）](020_sources.md#xid-2FAD591BF725)

### 意味が変わる更新（新しい XID に切り替える）

「同じ XID のままでは別物になる」と判断した場合は、旧ページを消さずに後継ページ（新 XID）を作り、旧→新の関係を明示します。

```powershell
python -m fm xref deprecate <OLD_XID> <NEW_XID> --note "変更理由（任意）"
python -m fm xref rewrite
python -m fm xref check --review
```

`python -m fm xref check` と `python -m fm xref fix` は、問題がある場合に終了コード `1` を返します。
