<!-- xid: 0E5C778EB6AF -->
<a id="xid-0E5C778EB6AF"></a>

# MCP Contribution Return Adoption Usage Guide

このガイドは、MCP から取得した Skill を利用したクライアントがローカルで作成した
Knowledge または決定論ツールを返却し、人間の判断を経て XRefKit の正式資産へ配置する
運用を説明する。設計上の境界は
[MCP Skill のローカル編集と配布元への還元](../designs/090_mcp_skill_local_edit_design.md#xid-A4C7E2D91B60)
を参照する。

## 要件

### 目的と境界

このフローが扱うのは、次の二種類の返却物である。

- `knowledge`: XID を持つ UTF-8 Markdown 1ファイル
- `deterministic_tool`: runtime、entrypoint、入出力契約、検証証跡を持つ完全なディレクトリ

クライアント AI は返却時に `proposed_target_path` を指定できる。これは配置候補を示す
evidence であり、採用権限ではない。人間が trusted UI または identity adapter で内容と
配置先を確認し、署名付き `approval_assertion` によって `approved_target_path` を固定する。
MCP サーバーは accepted review と one-time `approval_token` を検証した場合だけ、server-owned
transport で正式配置する。

返却、review、adoption、publication、distribution、live verification は別の状態である。
`adopt_contribution_return` が成功しても、公開、配布、稼働環境からの再取得確認は実行されない。
adoption event の `publication`、`distribution`、`live_verification` はそれぞれ
`not_performed` のまま残る。

### 前提

1. MCP サーバーの `get_startup_context` が完了している。
2. クライアントが MCP から対象 Skill を取得している。
3. `xrefkit skill run` で作成した `run_id` と対象 `skill_id` を `bind_skill_run` で
   現在の MCP session に関連付けている。
4. 返却内容は UTF-8 text であり、各 `content_hash` は BOM を追加せず、本文を UTF-8
   encode した byte 列の lowercase SHA-256 である。
5. `skill_content_hash` は実際に使用した現在の Skill 本文の SHA-256 と一致する。
6. 使用した Knowledge がある場合、`knowledge_versions` に実際の `xid` と
   `content_hash` を記録する。
7. 正式配置先を判定できる `ownership.yaml` が受信 repository にある。
8. review と adoption を使うサーバーに、32 UTF-8 bytes 以上の
   `XREFKIT_CONTRIBUTION_APPROVAL_SECRET` が設定されている。

返却契約とサイズ上限は固定値として写さず、処理開始時に
`get_contribution_return_contract()` を呼び、その応答を使用する。現在の実装は最大64ファイル、
1ファイル 1 MiB、合計 5 MiB、network request 8 MiB などを返すが、運用クライアントは
応答値を正とする。

### 正式配置を許可する path

path は `/` 区切りの安全な repository-relative POSIX path とする。絶対 path、`..`、
Windows reserved name、alternate data stream になり得る表現は拒否される。

| kind | 許可形 | 追加条件 |
|---|---|---|
| `knowledge` | `knowledge/<relative-path>.md` | 対象 ownership zone の `catalog: true` が必要 |
| `knowledge` | `packs/<pack-id>/knowledge/<relative-path>.md` | 対象 ownership zone の `catalog: true` が必要 |
| `knowledge` | `packs/local/<pack-id>/knowledge/<relative-path>.md` | 対象 ownership zone の `catalog: true` が必要 |
| `deterministic_tool` | `tools/<new-directory>` | target は `tools/` 配下の新規directoryで、zone は `id: kernel-code`、`owner: base`、`distribution: true` が必要。返却fileはこのdirectory内へ配置される |

Knowledge は既存 canonical target と既存 catalog XID の衝突を許可しない。決定論ツールは
全ファイルを一つの directory/collection として移し、配置中にも実行しない。どちらも既存
target を上書きしない。

## 仕組み

### 保存物と状態

返却物は受信 repository の
`.xrefkit/contribution-returns/<contribution_id>/` に保存される。

- `manifest.json`: `pending_review` の返却manifestと `payload_hash`
- `files/`: inertな返却本文。登録、一覧、exportでは実行・有効化しない
- `events/review.json`: 人間の判断を固定した署名付きimmutable event
- `events/adoption-prepared.json`: transport開始前の署名付きimmutable event
- `events/adoption.json`: 正式配置結果の署名付きimmutable event

署名済みeventは `event_hash` と `server_signature` を持つ。`list_contribution_returns`、
`export_contribution_return`、`adopt_contribution_return` は存在するeventを検証し、改変、署名不一致、
review binding不一致を検出した場合は処理を停止する。

代表的な状態遷移は次のとおりである。

```text
pending_review -> accepted -> adoption_pending -> adopted
              \-> rejected
```

`adoption_pending` は `adoption-prepared.json` があり、完了eventがまだない状態である。

### 人間の approval assertion

`approval_assertion` は AI が自己申告で作る値ではない。MCP client の外側にある trusted
UI/identity adapter が、人間の判断を受けて発行する。現在の verifier は
`HMAC-SHA256` を使用し、次のclaimをreview要求と完全一致させる。

- `assertion_id`
- `contribution_id`
- `decision_id`
- `decision`: `accepted` または `rejected`
- `reviewer`
- `payload_hash`
- `proposed_target_path` とその SHA-256、または両方 `null`
- `approved_target_path` とその SHA-256、または両方 `null`
- `expires_at`: Unix time。helperの既定値は発行から300秒

実装には trusted adapter 用helperとして
`xrefkit.mcp.contribution_adoption.issue_hmac_approval_assertion` がある。これはMCP toolではない。
次はadapter側の生成例である。`manifest` は検証済みのreview bundleから組み立てる。

```python
import hashlib
import os
import uuid

from xrefkit.mcp.contribution_adoption import issue_hmac_approval_assertion


def path_hash(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


decision_id = str(uuid.uuid4())
reviewer = "human:operator@example"
approved_target_path = "knowledge/operations/client-learned-rule.md"
assertion = issue_hmac_approval_assertion(
    os.environ["XREFKIT_CONTRIBUTION_APPROVAL_SECRET"],
    {
        "assertion_id": str(uuid.uuid4()),
        "contribution_id": manifest["contribution_id"],
        "decision_id": decision_id,
        "decision": "accepted",
        "reviewer": reviewer,
        "payload_hash": manifest["payload_hash"],
        "proposed_target_path": manifest["proposed_target_path"],
        "proposed_target_path_hash": path_hash(manifest["proposed_target_path"]),
        "approved_target_path": approved_target_path,
        "approved_target_path_hash": path_hash(approved_target_path),
    },
)
```

secret はMCPサーバーとtrusted adapterだけに渡し、AI prompt、MCP tool入力、返却manifest、audit、
WebDAV URL、repositoryへ保存しない。実行環境のsecret managerまたは同等の既存資格情報管理を
使用し、client AIへ環境変数を公開しない。secretをrotationすると、旧secretで署名された既存eventを
現verifierで読めなくなるため、未完了recordの完了または移行方針を決めてから切り替える。

accepted reviewを初回作成した応答だけが平文の `approval_token` を返す。サーバーが保存するのは
SHA-256だけであり、同じreviewを再送したidempotent応答ではtokenは `null` になる。trustedな呼出側は
tokenをadoption完了まで一時的なsecretとして保持し、logや会話本文へ残さない。

## 運用

### サーバー設定

local adapterは既定値であり、追加のtransport指定は不要である。WebDAVを使う場合は、MCPサーバー
processに次を設定する。

```powershell
$env:XREFKIT_CONTRIBUTION_APPROVAL_SECRET = '<secret-managerから注入>'
$env:XREFKIT_ADOPTION_WEBDAV_STAGING_URL = 'https://dav.example.invalid/xrefkit-staging'
$env:XREFKIT_ADOPTION_WEBDAV_CANONICAL_URL = 'https://dav.example.invalid/xrefkit-canonical'
$env:XREFKIT_ADOPTION_WEBDAV_STAGING_USERNAME = '<staging-user>'
$env:XREFKIT_ADOPTION_WEBDAV_STAGING_PASSWORD = '<staging-password>'
$env:XREFKIT_ADOPTION_WEBDAV_USERNAME = '<adoption-user>'
$env:XREFKIT_ADOPTION_WEBDAV_PASSWORD = '<adoption-password>'

python -m xrefkit.mcp.server --repo C:/path/to/XRefKit --contribution-adoption-transport webdav
```

URLだけは次の引数でも指定できる。引数は対応する環境変数より優先される。

- `--webdav-staging-url`
- `--webdav-canonical-url`

approval secretも `--contribution-approval-secret` で指定できるが、process command lineにsecretを
残さない運用では `XREFKIT_CONTRIBUTION_APPROVAL_SECRET` を使用する。WebDAV transportを選択した
状態でURLまたは資格情報が欠けている場合はサーバー起動が失敗し、local adapterへfallbackしない。
URLはabsolute HTTP(S) URLとし、credential、query、fragmentを埋め込まない。

WebDAV serverには次のmethodと条件付き処理が必要である。

| credential | 対象 | 必要なmethod / 条件 |
|---|---|---|
| staging | staging root以下 | `MKCOL`, `PUT`, `GET`, `HEAD`, `PROPFIND` (`Depth: infinity`) |
| adoption | canonical rootとMOVE元 | canonicalの`HEAD`, recovery時の`GET`/`PROPFIND`, stagingからcanonicalへのserver-side `MOVE` |

staging credentialにcanonical rootへの `PUT` または `MOVE` 権限を与えない。adoption credentialは
MCP server processだけが保持する。`MOVE` は `Destination`、staging resourceの `ETag`を使う
`If-Match`、`Overwrite: F` を付ける。WebDAV serverは同じ操作でstaging URLからcanonical URLへ
server-side MOVEでき、collectionの `ETag` と `Depth: infinity` の `PROPFIND`を提供する必要がある。

### 1. 契約取得と返却

最初に `get_contribution_return_contract({})` を呼び、現在の schema、limits、orderingを確認する。
その後、bind済みsessionで `submit_contribution_return` を呼ぶ。以下はKnowledgeの具体例である。
UUIDとhashは実値に置き換える。

```json
{
  "contribution_id": "8dba5ca7-83c8-44be-8cc0-d3ed662933e4",
  "kind": "knowledge",
  "title": "Client learned retry rule",
  "summary": "Skill実行で確認した再試行条件をレビューへ返す",
  "files": [
    {
      "path": "client-learned-rule.md",
      "content": "<!-- xid: C1E17A9B204F -->\n<a id=\"xid-C1E17A9B204F\"></a>\n\n# Client Learned Retry Rule\n\n本文。\n",
      "content_hash": "<contentをUTF-8 encodeしたlowercase SHA-256>"
    }
  ],
  "skill_content_hash": "<実際に使用したSkill本文のlowercase SHA-256>",
  "package_id": null,
  "knowledge_versions": [
    {
      "xid": "<実際に使用したKnowledge XID>",
      "content_hash": "<その本文のlowercase SHA-256>"
    }
  ],
  "knowledge": {
    "xid": "C1E17A9B204F"
  },
  "deterministic_tool": null,
  "proposed_target_path": "knowledge/operations/client-learned-rule.md"
}
```

成功応答の確認対象は次である。以下は応答の抜粋である。

```json
{
  "schema": "xrefkit.contribution_return/v1",
  "contribution_id": "8dba5ca7-83c8-44be-8cc0-d3ed662933e4",
  "status": "pending_review",
  "payload_hash": "<serverが計算したSHA-256>",
  "proposed_target_path": "knowledge/operations/client-learned-rule.md",
  "created": true,
  "idempotent_replay": false,
  "audit_status": "recorded"
}
```

同じ `contribution_id` と同じpayloadの再送は `created: false`、
`idempotent_replay: true` になる。異なるpayloadで同じIDを再使用すると拒否される。

決定論ツールの場合は複数の `files` を指定できる。`path` はbundle内pathであり、target directoryを
重ねない。metadata例は次のとおりである。

```json
{
  "kind": "deterministic_tool",
  "files": [
    {"path": "check.py", "content": "print('ok')\n", "content_hash": "<SHA-256>"},
    {"path": "README.md", "content": "# Checker\n", "content_hash": "<SHA-256>"}
  ],
  "knowledge": null,
  "deterministic_tool": {
    "runtime": "python>=3.11",
    "entrypoint": "check.py",
    "input_contract": {"type": "object"},
    "output_contract": {"type": "object"},
    "verification_evidence": [
      {"kind": "test", "command": "pytest", "result": "passed"}
    ]
  },
  "proposed_target_path": "tools/returned-checker"
}
```

### 2. 一覧、export、人間review

`list_contribution_returns({})` は本文を含まないinbox metadataを返す。reviewerは候補を選び、
bind済みsessionから
`export_contribution_return({"contribution_id": "<UUID>"})` を呼んで完全なinert bundle、hash、
source、binding、既存eventを確認する。`activation_performed` は `false` のままである。

人間がacceptする場合、trusted adapterはexport内容と希望する正式配置先を表示し、判断後に前節の
assertionを発行する。次の入力を `review_contribution_return` へ渡す。

```json
{
  "contribution_id": "8dba5ca7-83c8-44be-8cc0-d3ed662933e4",
  "decision_id": "5a999c23-5962-4a60-a1ed-052342b37490",
  "decision": "accepted",
  "reviewer": "human:operator@example",
  "decision_evidence": "本文、XID、参照元、ownershipと配置先を確認した。",
  "approval_assertion": "<trusted adapterが発行した署名付きassertion>",
  "approved_target_path": "knowledge/operations/client-learned-rule.md"
}
```

成功応答では `event: review_decided`、`decision: accepted`、`review_binding_hash`、
`server_signature`、`created: true` と `approval_token` を確認する。rejectする場合は
`decision: rejected` とし、`approved_target_path` は指定しない。rejected recordはadoptionできない。

review eventはimmutableである。同じ入力の再送だけがidempotent replayとして認められ、別の判断、
reviewer、evidence、targetへの変更は拒否される。変更が必要な場合は、新しい `contribution_id` で
返却からやり直し、人間が再審査する。

### 3. 正式配置

初回accepted reviewで受け取ったtokenを使い、bind済みsessionから
`adopt_contribution_return` を呼ぶ。

```json
{
  "contribution_id": "8dba5ca7-83c8-44be-8cc0-d3ed662933e4",
  "adoption_id": "9c6f59e4-c58f-4459-85bd-058d94c2869b",
  "reviewer": "human:operator@example",
  "decision_evidence": "accepted reviewに従って正式配置を実行する。",
  "approval_token": "<初回accepted reviewで返されたone-time token>"
}
```

MCPサーバーはrepository-wide adoption lock内でmanifest、全file hash、署名済みreview、token、XID、
ownership、target衝突を再検証する。成功応答では次を確認する。以下は応答の抜粋である。

```json
{
  "event": "adopted",
  "status": "adopted",
  "canonical_target": "knowledge/operations/client-learned-rule.md",
  "canonical_files": [
    {
      "path": "knowledge/operations/client-learned-rule.md",
      "content_hash": "<返却内容と同じSHA-256>"
    }
  ],
  "transport": {
    "transport": "webdav_conditional_move",
    "precondition": "If-Match and Overwrite:F",
    "source_etag": "<staging resource ETag>",
    "recovered": false
  },
  "publication": "not_performed",
  "distribution": "not_performed",
  "live_verification": "not_performed",
  "tool_execution_performed": false,
  "created": true,
  "idempotent_replay": false,
  "audit_status": "recorded"
}
```

local adapterの場合、`transport.transport` は `local_atomic_move` になる。Knowledgeはstaging fileから
exclusive hard linkで公開し、決定論ツールはfsync済みtreeをplatformのno-overwrite atomic directory
renameで公開する。対応するatomic primitiveがないplatformでは停止する。

### 監査

既定のstructured audit JSONLは `<repo>/work/mcp/xid_audit.jsonl` であり、
`--audit-log <path>` で変更できる。代表eventは次のとおりである。

- `contribution.return_submitted`
- `contribution.return_exported`
- `contribution.review_decided`
- `contribution.adopted`

tool応答の `audit_status` が `failed` の場合、主要処理が成功していても監査追記は失敗している。
運用上の完了として扱う前にaudit保存先と権限を復旧し、必要な記録を別途確認する。
recordの現在状態は `list_contribution_returns`、本文と署名済みeventを含む完全な証跡は
`export_contribution_return` で確認する。

### 失敗時の対処とrecovery

| 症状 | 判定と対処 |
|---|---|
| `XREFKIT_SKILL_RUN_REQUIRED` | 対象Skillの `run_id` と `skill_id` を現在sessionへ `bind_skill_run` し、同じ操作を再実行する |
| current Skill/Knowledge hash不一致 | 使用版と現在配布版を確認する。hashを作り替えて通さず、必要なら新しい返却として再作成する |
| approval verifier未設定、assertion不一致・期限切れ | trusted adapterとMCP serverのsecret、claim、時刻を確認し、新しいassertionを発行する |
| target ownership不一致、XID重複、target既存 | 正式配置を停止する。ownershipまたは既存資産を人間が確認し、新しい `contribution_id` とreviewで別targetを審査する |
| WebDAV staging hash/tree不一致 | staging collectionの余分なentry、欠落、内容改変を調査する。MCP serverは一致しないtreeをMOVEしない |
| staging resourceにETagがない | WebDAV server設定を修正する。無条件MOVEへ切り替えない |
| `adoption_pending` | 同じ `adoption_id`、`approval_token`、reviewer、evidenceでadoptionを再実行する |
| canonical targetが既に存在する | prepared eventがあり、全target path、tree、hashが完全一致する場合だけrecovery成功になる。余分なentryやhash差異があれば衝突として停止する |
| approval token紛失 | token再発行toolはない。旧recordのadoptionを続けず、必要なら新しい `contribution_id` で返却し、人間のreviewからやり直す |

`adoption-prepared.json` はremote/local mutationより前に作られる。その後に通信断やprocess停止が
起きた場合、再実行はこのprepared eventを根拠にcanonical targetを照合する。完全一致した既存targetは
`recovered: true` として完了できる。部分一致、extra file、異なるhashは成功に読み替えない。

### adoption後の別作業

adoptionは受信repositoryのcanonical pathへ内容を配置するところまでである。その後に必要な
XID索引更新、repository check、commit、pull request、merge、package/release publication、distribution、
MCP server更新、別clientからのlive取得確認は、それぞれの既存workflowで実行し、個別に証拠を残す。
adoption eventだけを根拠に公開済み、配布済み、live利用可能と報告しない。

## 未解決・未検証

- 実WebDAV製品への接続、authentication、ACL、collection ETag、`Depth: infinity`、条件付き
  server-side `MOVE` の相互運用は未検証である。現在の検証はfixtureによる。
- trusted UI/identity adapterの製品実装、secret manager連携、secret rotation手順はこの実装に
  含まれない。repositoryにはHMAC verifierとissuer helperがある。
- WebDAV server製品ごとのlock、quota、retention、staging cleanup、backup、障害監視は運用環境で
  定義する必要がある。
- adoption後のpublication、distribution、live verificationの自動連携は実装されていない。

本番導入前に専用のtest repositoryと非本番WebDAV rootを用意し、Knowledge 1ファイルと
決定論ツール1directoryについて、正常系、既存target、通信中断後recovery、余分なcollection entry、
ETag欠落、権限拒否を確認する。結果がない環境のlive対応状態は `unknown` として扱う。

## 関連

- [MCP Skill のローカル編集と配布元への還元](../designs/090_mcp_skill_local_edit_design.md#xid-A4C7E2D91B60)
- [XRefKit Startup Contract](../core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22)
- [Shared Memory Operations](../core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED)
- [Document Update Policy](../policies/074_document_update_policy.md#xid-B1D42A6F90C3)
