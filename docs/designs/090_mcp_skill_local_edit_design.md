<!-- xid: A4C7E2D91B60 -->
<a id="xid-A4C7E2D91B60"></a>

# MCP Skill のローカル編集と配布元への還元

状態: ローカル編集、MCP所有のinbound WebDAV返却、署名付きreview、local正式資産化を実装済み。自動三者マージ等は設計提案。
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

MCP 提供の Skill を使った後にローカルで作成した Knowledge、決定論ツール、またはSkill観察を戻す場合は、Skill Run を `bind_skill_run` で関連付けたまま `get_contribution_return_contract` を取得する。続いて `create_contribution_upload_session` が短命な `upload_id`、MCP所有WebDAV URL、1回だけ表示するBearer tokenを発行する。clientはそのupload collectionにだけ`MKCOL`/`PUT`できる。tokenはURLやqueryに含めず、serverはhashだけを保存する。

upload後、clientは本文を再送せず、`seal_contribution_upload`へexpected path、SHA-256、byte countと返却metadataを渡す。MCPは同じSkill Run binding、期限、file/collection/in-flight global quota、完全なtree、hash、UTF-8を検証する。受信byteはdurable reservationをglobal lock内で確保してから書き、失敗時はpartial fileとreservationを解放する。期限切れstagingは決定論的に回収する。seal開始時にtokenを失効し、staging treeをHTTPから到達不能なfrozen treeへ原子的に移してから、`.xrefkit/contribution-returns/` の `pending_review` recordへ変換する。process停止後は同じrequest hashと一意なfreeze状態だけを再開する。extra/missing file、改変、再利用、期限切れ、競合seal、曖昧なrecovery状態、symlink/reparse pointはfail closedとする。AI の `proposed_target_path` は候補であって採用権限ではない。本文をMCP JSONへ含める旧`submit_contribution_return`は移行期間の互換経路に限る。

返却物は `list_contribution_returns` で本文なしに確認し、`export_contribution_return` でレビュー用の完全な bundle を取得する。登録・出力時には決定論ツールを実行せず、Knowledge catalog や `get_client_tool_*` に追加しない。

正式資産化は二つの明示操作に分ける。人間は MCP client の外側にある trusted UI/identity adapter で判断し、server-configured secret で署名された `approval_assertion` を発行する。`review_contribution_return` はこの assertion を検証してから `accepted` または `rejected`、reviewer identity、decision evidence、承認した canonical target を記録する。client が渡す reviewer 文字列だけでは受理しない。assertion と immutable review event は contribution `payload_hash`、AI の `proposed_target_path` とその hash、承認 target とその hash、`contribution_id`、`decision_id`、reviewer を固定する。`accepted` の初回記録時だけ one-time `approval_token` を返し、保存するのは token hash のみとする。`adopt_contribution_return` はこの token と immutable event の一致を確認し、repository-wide adoption lock 内で payload、XID、target ownership を再検証してから、server-owned transport に正規配置を委ねる。`rejected` は正式資産化できない。review/adoption event は server署名とevent hashを持ち、list/export/adoptで検証できない場合は fail closed とする。

Knowledge の target は `ownership.yaml` 上で `catalog: true` の `knowledge/` または pack の `knowledge/` 配下に限り、既存 XID と target path の衝突を拒否する。決定論ツールは `kernel-code` zone の `tools/` 配下に新規directoryとして置き、全fileを一つのdirectory/collectionとして移す。正式資産化中にツールを実行しない。

正式資産化はlocal transportだけを使用し、fsync 済み staging file/tree を no-overwrite の atomic file publication または directory rename で配置する。対応するatomic primitiveがないplatformでは停止する。WebDAV endpointにはupload collection以外のrouteが存在せず、client tokenではcanonical repositoryへ`PUT`、`MOVE`、`COPY`、`DELETE`できない。外部WebDAV server、外部canonical URL、adoption credentialは要件に含めない。

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
- `create_contribution_upload_session(expires_in_seconds?)`
- `seal_contribution_upload(upload_id, contribution_id, kind, title, summary, expected_files, skill_content_hash, ...)`
- `submit_contribution_return(contribution_id, kind, title, summary, files, skill_content_hash, package_id?, knowledge_versions?, knowledge?, deterministic_tool?)`
- `list_contribution_returns()`
- `export_contribution_return(contribution_id)`
- `review_contribution_return(contribution_id, decision_id, decision, reviewer, decision_evidence, approval_assertion, approved_target_path?)`
- `adopt_contribution_return(contribution_id, adoption_id, reviewer, decision_evidence, approval_token)`

Server configuration for inbound WebDAV:

- `--enable-inbound-webdav`
- `--inbound-webdav-host`（stdio companionはloopbackのみ）
- `--inbound-webdav-port`（stdioで必須。streamable-httpはMCP portを共有）
- `--inbound-webdav-public-base-url`
- `--inbound-webdav-session-seconds`
- `XREFKIT_CONTRIBUTION_APPROVAL_SECRET`（trusted assertion verificationとevent signing。32 UTF-8 bytes以上）

旧`--contribution-adoption-transport webdav`、`--webdav-staging-url`、`--webdav-canonical-url`、`XREFKIT_ADOPTION_WEBDAV_*`は誤方向のoutbound設定であり、指定時は移行案内付きで起動を拒否する。

stdio companionは実listenerから生成したloopback URLだけを発行する。streamable-httpのnon-loopback listenerはTLSを必須とし、明示URLも実際のscheme、host、portとの完全一致を要求する。SSE transportではinbound receiverを有効化しない。

CLI:

- `python -m xrefkit.mcp.cli prepare-skill-edit --repo <repo> --skill-id <id>`
- `python -m xrefkit.mcp.cli list-skill-edits --repo <repo>`
- `python -m xrefkit.mcp.cli export-skill-edit --repo <repo> --skill-id <id>`
- `python -m xrefkit.mcp.cli deactivate-skill-edit --repo <repo> --skill-id <id>`
- `python -m xrefkit.mcp.cli create-local-knowledge --repo <repo> --xid <xid> --content-file <file>`
- `python -m xrefkit.mcp.cli export-local-knowledge --repo <repo> --xid <xid>`

## 実装範囲と未実装

段階1として、ローカル編集版の取得・登録・自動選択、編集版の XID 解決、Skill の一覧・差分出力・無効化、新規ローカル Knowledge の作成・一覧・XID 解決・追加差分出力・無効化を実装した。さらに、MCP Skill Run に由来を結び付けた Knowledge／決定論ツール／Skill観察のinbound WebDAV返却、署名付き human review、local transportによる正式資産化を実装した。

自動三者マージ、任意の MCP 間をまたぐクライアント側 XID Federation、配布元への PR／公開、公開確認後の自動無効化は未実装である。これらは元版・編集版・現在の配布版の競合解決、権限、公開範囲を定義してから追加する。

crash後にclientから同一sealが再送されない`sealing` sessionのoperator GC policyは未実装である。wildcard bind、public DNS alias、reverse proxyの別URLも現契約では許可せず、必要な場合はlistener identityとTLS終端のtrust境界を別途定義する。

## 関連契約

- [XRefKit Startup Contract](../core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22)
- [Startup Xref Routing Policy](../core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A)
- [Document Update Policy](../policies/074_document_update_policy.md#xid-B1D42A6F90C3)
