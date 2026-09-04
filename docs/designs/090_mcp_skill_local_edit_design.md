<!-- xid: A4C7E2D91B60 -->
<a id="xid-A4C7E2D91B60"></a>

# MCP Skill のローカル編集と配布元への還元

状態: 段階1実装済み。段階2以降は設計提案。
作成日: 2026-09-05

## 目的

MCP が提供する Skill に不足が見つかった時点で、利用プロジェクト内に編集版を作り、同じ Skill と XID の参照を保ったまま使えるようにする。Skill ではなく Knowledge の新規追加が必要な場合は、プロジェクト固有の XID 文書として登録する。改善が共通化できる場合は、元の配布元へ変更案として戻す。

## 要求

- 修正指示を起点に、初回のローカルコピーを自動化する。
- 既存の編集内容を後続の取得で上書きしない。
- 意味による Skill 選択と、配布版／編集版の使用版解決を分離する。
- 同じ文書の編集では XID を維持する。
- MCP の Knowledge と利用プロジェクトのローカル Knowledge を区別して解決する。
- 実行に使った版と依存文書を追跡できるようにする。
- 元版との差分を作り、配布元への変更案として提示する。
- Skill の不足と Knowledge の新規追加を別の操作として扱う。

## 仕組み

編集版は対象リポジトリの `.xrefkit/skill-edits/<skill-id>/` に保存し、`.xrefkit/skill-edits.json` に提供元、元版のパス・ハッシュ、編集版のパス、使用状態を記録する。MCP の `prepare_skill_edit` は初回だけ `meta.md` と `SKILL.md` を取得し、既存ファイルを上書きしない。

カタログは登録済みで有効な編集版を元の候補に重ねる。目的によるルーティングで Skill ID を選んだ後、登録された編集版を自動的に使用する。無効化するとファイルを保持したまま配布版へ戻る。

編集版の `meta.md` と `SKILL.md` が宣言する XID はそのまま使う。`get_document_by_xid` は編集版を優先し、対応する元パスだけを置き換える。無関係な同一 XID は競合として扱い、パス順で選択しない。

MCP が提供する文書とローカル Knowledge の横断は、利用側の XRefKit が解決を取りまとめる。MCP のみにある XID は MCP から、ローカルのみにある XID はローカルから解決する。両方にあり使用版を決められない場合は競合、どちらにもない場合は参照切れとする。

新規 Knowledge は `.xrefkit/knowledge-edits/` に保存し、`.xrefkit/knowledge-edits.json` に XID、ファイル、内容ハッシュ、使用状態を登録する。登録後は通常の Knowledge カタログと `get_document_by_xid` から解決できる。新規文書なので元版との差分ではなく、追加ファイルとして `export_local_knowledge` が patch を出力する。

## 運用

修正指示を受けた AI は、対象 Skill を特定して `prepare_skill_edit` を呼び、返された編集版を対象に修正する。修正後は Skill の契約、メタデータ、XID 参照を検証する。編集版の一覧は `list_skill_edits` で確認する。

配布元へ戻す場合は `export_skill_edit` で元版との差分を取得し、必要なら `write_patch=true` で `work/mcp/skill-edits/` に保存する。ローカル専用 Knowledge を自動的に公開対象へ含めない。配布元でレビュー・取り込み・配布が完了し、MCP から新内容を取得できたことを確認してから `deactivate_skill_edit` を呼ぶ。無効化後も編集ファイルは保持する。

編集ファイルの更新と、実行中の Skill Run への採用は分ける。実行途中に黙って内容を切り替えず、採用時は再検証と使用版の記録を行う。

## 実装入口

MCP tools:

- `prepare_skill_edit(skill_id, package_id?)`
- `list_skill_edits()`
- `export_skill_edit(skill_id, write_patch?)`
- `deactivate_skill_edit(skill_id)`
- `create_local_knowledge(xid, content, filename?, domain?)`
- `list_local_knowledge()`
- `export_local_knowledge(xid, write_patch?)`
- `deactivate_local_knowledge(xid)`

CLI:

- `python -m xrefkit.mcp.cli prepare-skill-edit --repo <repo> --skill-id <id>`
- `python -m xrefkit.mcp.cli list-skill-edits --repo <repo>`
- `python -m xrefkit.mcp.cli export-skill-edit --repo <repo> --skill-id <id>`
- `python -m xrefkit.mcp.cli deactivate-skill-edit --repo <repo> --skill-id <id>`
- `python -m xrefkit.mcp.cli create-local-knowledge --repo <repo> --xid <xid> --content-file <file>`
- `python -m xrefkit.mcp.cli export-local-knowledge --repo <repo> --xid <xid>`

## 実装範囲と未実装

段階1として、ローカル編集版の取得・登録・自動選択、編集版の XID 解決、Skill の一覧・差分出力・無効化、新規ローカル Knowledge の作成・一覧・XID 解決・追加差分出力・無効化を実装した。`tests/mcp_catalog.py` と `tests/test_skill_edits.py` の合計 52 件が成功している。

自動三者マージ、任意の MCP 間をまたぐクライアント側 XID Federation、配布元への PR／公開、公開確認後の自動無効化は未実装である。これらは元版・編集版・現在の配布版の競合解決、権限、公開範囲を定義してから追加する。

## 関連契約

- [XRefKit Startup Contract](../core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22)
- [Startup Xref Routing Policy](../core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A)
- [Document Update Policy](../policies/074_document_update_policy.md#xid-B1D42A6F90C3)
