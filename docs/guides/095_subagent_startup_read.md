<!-- xid: D7A4C9E2B861 -->
<a id="xid-D7A4C9E2B861"></a>

# `workflow subagent-read` の利用ガイド

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
