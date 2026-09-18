<!-- xid: D7A4C9E2B861 -->
<a id="xid-D7A4C9E2B861"></a>

# Subagent startup read の利用ガイド

`workflow subagent-read` は、すでに開かれている local workflow run に対して、
子作業を担当する実行主体へ渡す bounded な startup context を filesystem から
materialize するコマンドである。run を開くこと、work item を登録すること、返された
資料を理解して実行することは、このコマンドの外側で行う。

## 前提: 開かれた run と work item

先に `workflow run` で run log を作り、completion criterion を持つ work item を
`pending` または `in_progress` として登録する。binding の `run_id` と
`work_item_id` は、この開かれた run と一致しなければならない。

```powershell
python -m xrefkit workflow run `
  --root . `
  --task "bounded document work" `
  --out work/sessions/2026-09-18_child_doc.md `
  --completion-condition "Guide matches CLI behavior" `
  --json

python -m xrefkit skill workitem `
  --log work/sessions/2026-09-18_child_doc.md `
  --item WI-DOC `
  --text "Write the guide" `
  --completion-criterion "Guide matches CLI behavior; example JSON and command validated" `
  --status pending `
  --role instruction:executor
```

run log が未開封、run ID が不一致、work item が存在しない、または criterion が
空の場合、startup read は成功を記録せずに失敗する。run log に
`mcp_session_id` がある場合も local filesystem reader は拒否する。MCP-bound run は
MCP provider で governance context を解決する。

## 実行方法

```powershell
python -m xrefkit workflow subagent-read `
  --root . `
  --log work/sessions/2026-09-18_child_doc.md `
  --binding work/subagent-doc.json `
  --json
```

`--binding` は UTF-8 JSON ファイルである。`--json` は常に JSON 出力として扱われ、
成功時の `state` は `materialized`、入力検証や hash 検証に失敗した場合の CLI 出力は
`state: "blocked"` と `errors` を含む。成功時でも process は agent を起動せず、
資料を読み取って receipt を run log に追記するだけである。

## binding の形式

```json
{
  "schema_version": 1,
  "source_mode": "filesystem",
  "run_id": "7745d211-7332-418d-843e-ca957166cfa5",
  "work_item_id": "WI-DOC",
  "purpose": "Write a Japanese guide for workflow subagent-read",
  "capability": "doc",
  "tuning": "XRefKit local repository",
  "responsibility": "Guide matches CLI behavior",
  "scope_in": ["docs/guides/095_subagent_startup_read.md"],
  "scope_out": ["Other workers files", "MCP and public publication"],
  "stop_conditions": ["Missing contract or source evidence"],
  "protocols": ["workflow"],
  "knowledge_access": {
    "mode": "on_demand",
    "catalog": "knowledge/000_index.md"
  },
  "references": [
    {
      "path": "xrefkit/subagent_startup.py",
      "sha256": "<64 lowercase hexadecimal characters>"
    }
  ]
}
```

上記の run_id は例である。新しく開始した run の ID に置き換え、sha256 は対象ファイルの実際の raw bytes から計算する。例中の placeholder はそのままでは受理されない。

必須の識別・責任フィールドは `run_id`、`work_item_id`、`purpose`、`capability`、
`tuning`、`responsibility` である。`scope_in`、`scope_out`、`stop_conditions` は
文字列配列、`protocols` は現在 `workflow` を必須とし、追加できる protocol は
`reporting` に限られる。`knowledge_access.mode` は `on_demand` でなければならず、
catalog は root 内のファイルを指す locator である。catalog 本文は自動ロードされない。

`references` は任意の配列だが、各要素には root 内の `path` と、その時点の raw bytes
に対する lowercase SHA-256 の `sha256` が必要である。最大 32 件で、読取時に hash が
一致しなければ処理は停止する。`source_mode` は local reader のため
`filesystem` 固定である。

## 何が materialize されるか

成功すると、`AGENTS.md`、startup contract と base control の startup source、
binding の `protocols` に指定した protocol 文書、run log の `skill_doc`（存在する
場合）、および hash-pinned `references` が順に `documents` として返される。各文書には
`path`、`xid`（該当する場合）、`sha256`、`bytes` が含まれる。

同時に、次の `subagent.startup.read` receipt が run log に記録される。

```json
{
  "event": "subagent.startup.read",
  "run_id": "7745d211-7332-418d-843e-ca957166cfa5",
  "work_item_id": "WI-DOC",
  "source_mode": "filesystem",
  "protocols": ["workflow"],
  "reads": [{"path": "xrefkit/subagent_startup.py", "xid": null,
              "sha256": "<64 lowercase hexadecimal characters>", "bytes": 8466}],
  "meaning": "materialized by reader; not model comprehension or execution evidence"
}
```

receipt の `meaning` は境界を明示する。materialized は、host が本文を子作業の
実行主体へ届けられる状態を示すだけで、agent の起動、本文の comprehension、手順の
execution、成果物の品質受入れを示さない。subagent の自動 dispatch や spawn も行われない。

## Knowledge と XID

catalog は on-demand の lookup handle であり、startup read は catalog 本文を
`documents` に含めない。必要な knowledge は、作業の判断が必要になった時点で XID を
検索・解決し、どの判断や成果物に適用したかを別途記録する。path と XID は参照を特定
するために使うが、hash-pinned reference の検証結果を省略するものではない。

## MCP-bound run の境界

local reader に MCP の governance context を混在させないため、run log の
`mcp_session_id` が空でない場合は `MCP-bound runs must resolve governance through the
MCP provider` として拒否する。MCP mode では provider の XID 解決・session binding
手順を使う。filesystem fallback が MCP-only document を代読したり、MCP-bound run を
local として受理したりはしない。

## 実行後の責任と確認

host は実際の作業結果・成果物・検証証拠を根拠に、assigned role を使って execution と handoff を記録する。receipt は起動資料の読取り記録であり、作業の完了証拠ではない。
典型的には executor が work item と output/evidence artifact を更新し、
`instruction:handoff_owner` が handoff phase を記録する。checker は executor と分離
された `instruction:checker` として deterministic な確認を担当する。

```powershell
python -m xrefkit skill phase --log <run-log> --phase execution --status done --role instruction:executor
python -m xrefkit skill phase --log <run-log> --phase handoff --status done --role instruction:handoff_owner
python -m xrefkit skill verify --log <run-log>
python -m xrefkit skill close --log <run-log>
```

`skill verify` は run log の work item、artifact、role、phase などを決定的に確認する。
output 本文の品質を判断したり、subagent の理解を推定したりしない。verify と close が
成功するまで run の手続き上の完了を主張しない。work item はその完了条件と実際の証拠に基づいて done にし、その後で verify/close に進む。`materialized` だけを作業完了の根拠にしない。

## CLI の確認

```powershell
python -m xrefkit workflow subagent-read --help
```

このコマンドは `--root`、`--log`、必須の `--binding`、`--json` を表示する。実装は
`xrefkit/subagent_startup.py`、基本的な挙動確認は `tests/test_subagent_startup.py` に
ある。特に selected sources のみの materialization、stale hash、root 外 path、誤った
XID、unopened log、MCP-bound run、reporting protocol の明示指定を確認する。

## MCP client adapter

MCP session を利用する host は、初期化済みの transport から次の async API を呼ぶ。
`workflow subagent-read` CLI は引き続き filesystem 専用である。

```python
from pathlib import Path
from xrefkit.mcp.subagent_startup import read_mcp_subagent_startup

async def call_tool(name, arguments):
    response = await session.call_tool(name, arguments)
    if response.isError:
        raise RuntimeError(str(response.content))
    return response.structuredContent

result = await read_mcp_subagent_startup(Path("work/run.md"), binding, call_tool)
# Host supplies result to the assigned subagent before it starts its work.
```

`session` は host が初期化した MCP client session、`binding` は実際の run と
work item から組み立てた辞書である。stateless HTTP で `context_id` を利用する host は、
callback 内で応答の context 更新と次の呼出しへの引継ぎも行う。

local binding の必須責任フィールドは同じで、MCP では次の項目に置き換える。
`repository_fingerprint` は接続先の `get_repository_identity` などで確認する。

```json
{
  "source_mode": "mcp",
  "repository_fingerprint": "<expected repository fingerprint>",
  "protocols": ["workflow"],
  "knowledge_access": {
    "mode": "on_demand",
    "catalog_tool": "search_knowledge_catalog",
    "resolve_tool": "get_document_by_xid"
  },
  "references": [
    {"xid": "8A666C1FD121", "content_hash": "<64 lowercase hex characters>"}
  ]
}
```

これは差分例である。`schema_version`、`run_id`、`work_item_id`、`purpose`、
`capability`、`tuning`、`responsibility`、scope と stop conditions も必要になる。
MCP の `content_hash` は UTF-8 本文に対する SHA-256 で、local reader の raw file
bytes に対する `sha256` と区別する。

host の initialize で選択した protocol と binding の `protocols` が一致することを
確認する。adapter が session の選択を書き換えることはない。workflow run の読取りには
`workflow` が必要であり、reporting のみの session では停止する。
`initial_protocol_selection` は取得元を含めて result と receipt に保持する。

読取りは次の順で進む。

1. 開かれた local run と work item、binding を確認する。
2. `get_startup_context` から pack、選択された protocol と Prompt Flow 契約を取得する。
3. `bind_skill_run` の応答を検証し、信頼済み local runtime で correlation を記録する。
4. managed Skill run は `get_skill`、明示された参照は `get_document_by_xid` で取得する。
5. repository identity、hash、サイズ、run 状態を確認して読取 receipt を記録する。

`instruction` run は Skill 本文を取得しない。普通の Skill 文書を使う `general_skill`
は、この adapter では remote managed Skill identity を決定できないため未対応として停止する。
Knowledge catalog の検索や本文の一括ロードは行わない。MCP 応答に含まれる path や
`client_record_command` は実行せず、governance 文書を local filesystem で代読しない。

stale な startup pack、欠落した本文、hash や fingerprint の不一致、取得中に変更された
run 状態では成功 receipt を残さない。stale pack は server 側で更新してから再試行する。
本文は 1 件 256,000 bytes、binding と protocol を含む総量は 1,000,000 bytes まで。
途中で本文取得が失敗した場合でも、すでに成立した session correlation は事実として残る。

この adapter は既存の管理ポート、Skill/Knowledge upload、protocol 選択の server API を
変更しない。materialization 後も、host による実際の subagent 起動、作業の実行、
Workflow Protocol の verify/close、人による成果物採用は別途必要である。

## 開いたRunからExecutionBindingを生成する

`workflow bind-execution` は、親が指示から具体化した実行情報を、既存のRunとwork itemへ
結び付ける。生成器はSkill metaからtriadをコピーしない。Skill選択やモデル評価を行う
意味的routing、権限の付与、subagentのdispatchはhost側の責任である。

```powershell
python -m xrefkit workflow bind-execution `
  --log work/run.md --request work/execution-request.json --json > work/binding.json
python -m xrefkit workflow subagent-read `
  --root . --log work/run.md --binding work/binding.json --json
```

requestは上記のlocal/MCP bindingから`schema_version`と`run_id`を除き、
`instruction_basis`に今回の指示根拠を記載したJSONである。`work_item_id`、purpose、triad、
scope、stop conditions、protocols、Knowledge locatorは明示する。`references`は省略でき、
その場合は空配列になる。local requestには`repository_fingerprint`を含めず、
MCP requestでは必須とする。未定義のkeyは拒否する。

生成結果は既存のreaderへそのまま渡せるbindingで、次を追加する。

- `run_id`と`schema_version: 1`
- `binding_origin: "workflow_builder"`
- `run_snapshot`: 親子相関、選択Skill、task、authority、assigned roles、work itemの
  criterionとstatus、Closure Gate状態

APIは`xrefkit.execution_binding.build_execution_binding(log, request)`である。
生成時にはrun logだけを読み、参照先の本文を取得したりファイルを更新したりしない。
参照hashは呼出し側が実際の版から指定し、readerが取得時に検査する。
生成器でJSONの構造が通っても、指定したlocal pathやremote XIDの存在確認は未実施である。

両readerはgenerated bindingのsnapshotを起動時に照合する。役割・権限・task・相関、
work itemの条件やstatusが生成後に変われば停止し、変更内容を確認してbindingを作り直す。
MCPのsession correlationは読取り中に確立するため、snapshot対象から除く。
元の手書きbindingも引き続き利用できるが、生成器のsnapshot照合は付かない。

これはhostが渡した情報とRunの整合性検査であり、署名による認証ではない。
`instruction_basis`やauthorityに記述があることだけで新たな実行権限は生まれず、
既存のguard、停止・エスカレーション、verify/close、人間による採用条件を継続適用する。
モデルの選択や実行観測はこの生成結果に捏造しない。Skill/catalogの新形式への移行と、
モデルrouting実装との接続は別の変更単位で行う。
