<!-- xid: A4C7E2D91B60 -->
<a id="xid-A4C7E2D91B60"></a>

# MCP Skill のローカル編集と配布元への還元

状態: ローカル編集、返却、署名付きreview、local/WebDAV正式資産化を実装済み。自動三者マージ等は設計提案。
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

MCP 提供の Skill を使った後にローカルで作成した Knowledge または決定論ツールを戻す場合は、Skill Run を `bind_skill_run` で関連付けたまま `get_contribution_return_contract` を取得し、`submit_contribution_return` を呼ぶ。要求には UUID、UTF-8 の本文と SHA-256、実際に使った Skill 本文のハッシュ、利用した Knowledge の XID とハッシュを含める。AI は `proposed_target_path` を提示できるが、これは候補であって採用権限ではない。受信側 MCP は現在の配布内容と照合し、`.xrefkit/contribution-returns/` の staging collection に `pending_review` として保存する。契約が返すファイル数・本文量・metadata量・JSON深度の上限を登録前に適用し、streamable HTTPでは要求本文にも上限を設ける。Windowsで別名やADSになり得るpathも拒否する。

返却物は `list_contribution_returns` で本文なしに確認し、`export_contribution_return` でレビュー用の完全な bundle を取得する。登録・出力時には決定論ツールを実行せず、Knowledge catalog や `get_client_tool_*` に追加しない。

正式資産化は二つの明示操作に分ける。人間は MCP client の外側にある trusted UI/identity adapter で判断し、server-configured secret で署名された `approval_assertion` を発行する。`review_contribution_return` はこの assertion を検証してから `accepted` または `rejected`、reviewer identity、decision evidence、承認した canonical target を記録する。client が渡す reviewer 文字列だけでは受理しない。assertion と immutable review event は contribution `payload_hash`、AI の `proposed_target_path` とその hash、承認 target とその hash、`contribution_id`、`decision_id`、reviewer を固定する。`accepted` の初回記録時だけ one-time `approval_token` を返し、保存するのは token hash のみとする。`adopt_contribution_return` はこの token と immutable event の一致を確認し、repository-wide adoption lock 内で payload、XID、target ownership を再検証してから、server-owned transport に正規配置を委ねる。`rejected` は正式資産化できない。review/adoption event は server署名とevent hashを持ち、list/export/adoptで検証できない場合は fail closed とする。

Knowledge の target は `ownership.yaml` 上で `catalog: true` の `knowledge/` または pack の `knowledge/` 配下に限り、既存 XID と target path の衝突を拒否する。決定論ツールは `kernel-code` zone の `tools/` 配下に新規directoryとして置き、全fileを一つのdirectory/collectionとして移す。正式資産化中にツールを実行しない。

local transport は fsync 済み staging file/tree を no-overwrite の atomic file publication または directory rename で配置し、対応するatomic primitiveがないplatformでは停止する。WebDAV transport は staging 用資格情報で operation collection を作り、全staged fileを `GET` してSHA-256とcollection treeの完全一致を確認した後、server-side adoption資格情報でcollection ETagを指定したdirectory `MOVE` を `If-Match` と `Overwrite: F` 付きで実行する。WebDAV URL・username・passwordはserver config/environmentだけに置き、MCP responseやcontribution recordへ書かない。client/AIのWebDAV権限はstaging collectionに限定し、canonical rootへ `PUT` できる権限を与えない。

レビュー、正式資産化、公開、配布、live verificationは別状態である。adoption event は canonical path、content hash、transport precondition、元の `contribution_id` とreview bindingを残すが、publication、distribution、live verificationは `not_performed` のままにする。

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
- `get_contribution_return_contract()`
- `submit_contribution_return(contribution_id, kind, title, summary, files, skill_content_hash, package_id?, knowledge_versions?, knowledge?, deterministic_tool?)`
- `list_contribution_returns()`
- `export_contribution_return(contribution_id)`
- `review_contribution_return(contribution_id, decision_id, decision, reviewer, decision_evidence, approval_assertion, approved_target_path?)`
- `adopt_contribution_return(contribution_id, adoption_id, reviewer, decision_evidence, approval_token)`

Server configuration for WebDAV adoption:

- `--contribution-adoption-transport webdav`
- `--webdav-staging-url` or `XREFKIT_ADOPTION_WEBDAV_STAGING_URL`
- `--webdav-canonical-url` or `XREFKIT_ADOPTION_WEBDAV_CANONICAL_URL`
- `XREFKIT_ADOPTION_WEBDAV_STAGING_USERNAME`
- `XREFKIT_ADOPTION_WEBDAV_STAGING_PASSWORD`
- `XREFKIT_ADOPTION_WEBDAV_USERNAME`
- `XREFKIT_ADOPTION_WEBDAV_PASSWORD`
- `XREFKIT_CONTRIBUTION_APPROVAL_SECRET`（trusted assertion verificationとevent signing。32 UTF-8 bytes以上）

CLI:

- `python -m xrefkit.mcp.cli prepare-skill-edit --repo <repo> --skill-id <id>`
- `python -m xrefkit.mcp.cli list-skill-edits --repo <repo>`
- `python -m xrefkit.mcp.cli export-skill-edit --repo <repo> --skill-id <id>`
- `python -m xrefkit.mcp.cli deactivate-skill-edit --repo <repo> --skill-id <id>`
- `python -m xrefkit.mcp.cli create-local-knowledge --repo <repo> --xid <xid> --content-file <file>`
- `python -m xrefkit.mcp.cli export-local-knowledge --repo <repo> --xid <xid>`

## 実装範囲と未実装

段階1として、ローカル編集版の取得・登録・自動選択、編集版の XID 解決、Skill の一覧・差分出力・無効化、新規ローカル Knowledge の作成・一覧・XID 解決・追加差分出力・無効化を実装した。さらに、MCP Skill Run に由来を結び付けた Knowledge／決定論ツールのレビュー待ち返却、署名付き human review、local または WebDAV transport による正式資産化を実装した。

自動三者マージ、任意の MCP 間をまたぐクライアント側 XID Federation、配布元への PR／公開、公開確認後の自動無効化は未実装である。これらは元版・編集版・現在の配布版の競合解決、権限、公開範囲を定義してから追加する。

## 関連契約

- [XRefKit Startup Contract](../core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22)
- [Startup Xref Routing Policy](../core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A)
- [Document Update Policy](../policies/074_document_update_policy.md#xid-B1D42A6F90C3)
