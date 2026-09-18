<!-- xid: D7A4C9E2B861 -->
<a id="xid-D7A4C9E2B861"></a>

# Guide to Using `subagent startup read`

`workflow subagent-read` materializes bounded startup context from the filesystem for the executor responsible for child work in an already-open local workflow run. Opening the run, registering the work item, and understanding and executing the returned material are performed outside this command.

## Prerequisites: An Open Run and Work Item

First create a run log with `workflow run`, then register a work item with a completion criterion as `pending` or `in_progress`. The binding's `run_id` and `work_item_id` must match this open run.

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

If the run log is unopened, the run ID does not match, the work item does not exist, or the criterion is empty, startup read fails without recording success. The local filesystem reader also rejects a run log with `mcp_session_id`. An MCP-bound run resolves governance context through the MCP provider.

## Execution

```powershell
python -m xrefkit workflow subagent-read `
  --root . `
  --log work/sessions/2026-09-18_child_doc.md `
  --binding work/subagent-doc.json `
  --json
```

`--binding` is a UTF-8 JSON file. `--json` always requests JSON output: on success, `state` is `materialized`; when input or hash validation fails, CLI output contains `state: "blocked"` and `errors`. Even on success, the process does not start an agent; it only reads the material and appends a receipt to the run log.

## Binding Format

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

The `run_id` above is an example. Replace it with the ID of the newly started run, and calculate `sha256` from the target file's actual raw bytes. The placeholders in the example are not accepted as-is.

The required identity and binding fields are `run_id`, `work_item_id`, `purpose`, `capability`, `tuning`, and `responsibility`. Their meaning and derivation are owned by the [Workflow Runtime Binding contract](../core/contracts/111_workflow_runtime_binding.md#xid-8D50A972BA9F), and this binding verifies their transfer and consistency. `scope_in`, `scope_out`, and `stop_conditions` are string arrays. `protocols` currently requires `workflow`, and the only additional protocol that may be added is `reporting`. `knowledge_access.mode` must be `on_demand`, and `catalog` is a locator for a file inside root. The catalog body is not loaded automatically.

`references` is optional, but each element requires a `path` inside root and a lowercase SHA-256 `sha256` for the raw bytes at that point. There may be at most 32 entries; processing stops if a hash does not match during reading. `source_mode` is fixed to `filesystem` for the local reader.

## What Is Materialized

On success, `AGENTS.md`, the startup contract and base-control startup source, protocol documents specified by the binding's `protocols`, the run log's `skill_doc` when present, and hash-pinned `references` are returned in order as `documents`. Each document includes `path`, `xid` when applicable, `sha256`, and `bytes`.

At the same time, the following `subagent.startup.read` receipt is recorded in the run log.

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

The receipt's `meaning` makes the boundary explicit. `materialized` only indicates that the host can deliver the content to the executor for child work; it does not indicate agent startup, content comprehension, procedure execution, or artifact quality acceptance. No automatic subagent dispatch or spawn occurs.

## Knowledge and XID

The catalog is an on-demand lookup handle, and startup read does not include the catalog body in `documents`. When knowledge is needed for a work decision, search and resolve its XID and separately record which decision or artifact it was applied to. `path` and XID identify a reference, but they do not replace verification of a hash-pinned reference.

## Boundary for MCP-Bound Runs

To keep MCP governance context separate from the local reader, a non-empty `mcp_session_id` in the run log is rejected with `MCP-bound runs must resolve governance through the MCP provider`. MCP mode uses the provider's XID resolution and session-binding procedure. The filesystem fallback does not read MCP-only documents on its behalf or accept an MCP-bound run as local.

## Responsibilities and Verification After Execution

The host records execution and handoff using the assigned roles, based on actual work results, artifacts, and verification evidence. The receipt records reading startup material; it is not evidence that the work is complete. Typically, the executor updates the work item and output/evidence artifact, while `instruction:handoff_owner` records the handoff phase. The checker performs deterministic verification as the `instruction:checker` role, separate from the executor.

```powershell
python -m xrefkit skill phase --log <run-log> --phase execution --status done --role instruction:executor
python -m xrefkit skill phase --log <run-log> --phase handoff --status done --role instruction:handoff_owner
python -m xrefkit skill verify --log <run-log>
python -m xrefkit skill close --log <run-log>
```

`skill verify` deterministically checks the run log's work item, artifact, role, phase, and other fields. It does not judge the quality of output content or infer subagent comprehension. Do not claim procedural completion of the run until verify and close succeed. Mark the work item done based on its completion condition and actual evidence, then proceed to verify/close. Do not use `materialized` alone as evidence that the work is complete.

## CLI Check

```powershell
python -m xrefkit workflow subagent-read --help
```

This command displays `--root`, `--log`, required `--binding`, and `--json`. The implementation is in `xrefkit/subagent_startup.py`, and basic behavior checks are in `tests/test_subagent_startup.py`. In particular, verify materialization of only selected sources, stale hashes, paths outside root, incorrect XIDs, unopened logs, MCP-bound runs, and explicit selection of the reporting protocol.

## MCP Client Adapter

A host using an MCP session calls the following async API through an initialized transport. The `workflow subagent-read` CLI remains filesystem-only.

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

`session` is the MCP client session initialized by the host, and `binding` is a dictionary assembled from the actual run and work item. A host using `context_id` over stateless HTTP also updates the response context in the callback and carries it into the next call.

The required binding fields are the same for a local binding; in MCP they are supplemented by the following items. Verify `repository_fingerprint` using `get_repository_identity` or an equivalent operation on the connected endpoint.

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

This is a delta example. `schema_version`, `run_id`, `work_item_id`, `purpose`, `capability`, `tuning`, `responsibility`, scope, and stop conditions are also required. Field meaning follows Workflow Runtime Binding; the adapter does not redefine it. MCP `content_hash` is SHA-256 over the UTF-8 body and is distinct from the local reader's `sha256` over raw file bytes.

For MCP client initialize, exclude protocols from the initial exchange with `xrefkit.excluded_protocols` in the initialize params. Its value is an array of `prompt_flow`, `workflow`, and `reporting`; omission or `[]` selects all three. `xrefkit.initial_protocols` is legacy compatibility: it is treated as an include list for `workflow`/`reporting`, while `prompt_flow` is always included. Both extensions cannot be sent together.

Verify that the protocols selected by the host's initialize match the binding's `protocols`. The adapter does not rewrite the session's selection. Also verify that selected protocols return a body and excluded protocols return `null`. Reading a workflow run requires `workflow`; stop when the session contains only reporting. Preserve `initial_protocol_selection`, including its source, in the result and receipt.

Reading proceeds in the following order.

1. Verify the open local run, work item, and binding.
2. Obtain the pack, selected protocols, and Prompt Flow contract from `get_startup_context`.
3. Verify the `bind_skill_run` response and record correlation in the trusted local runtime.
4. Obtain managed Skill runs with `get_skill` and explicit references with `get_document_by_xid`.
5. Verify repository identity, hashes, sizes, and run state, then record the read receipt.

An `instruction` run does not retrieve Skill content. `general_skill`, which uses an ordinary Skill document, stops as unsupported because this adapter cannot determine a remote managed Skill identity. It does not search the Knowledge catalog or bulk-load its body. It does not execute paths or `client_record_command` returned by MCP, and it does not read governance documents through the local filesystem.

It does not leave a success receipt for a stale startup pack, missing body, hash or fingerprint mismatch, or a run state changed during retrieval. Update a stale pack on the server side before retrying. Each body is limited to 256,000 bytes, and the total including binding and protocols is limited to 1,000,000 bytes. Even if body retrieval fails partway through, an already-established session correlation remains a fact.

This adapter does not change the existing admin port, Skill/Knowledge upload, or protocol-selection server APIs. After materialization, the host still separately needs to start the actual subagent, execute the work, run Workflow Protocol verify/close, and obtain human adoption of the artifact.

## Generating an ExecutionBinding from an Open Run

`workflow bind-execution` connects execution information concretized by the parent from the instruction to an existing Run and work item. The generator does not copy the triad from Skill meta. Semantic routing for Skill selection and model evaluation, granting authority, and subagent dispatch are the host's responsibility.

```powershell
python -m xrefkit workflow bind-execution `
  --log work/run.md --request work/execution-request.json --json > work/binding.json
python -m xrefkit workflow subagent-read `
  --root . --log work/run.md --binding work/binding.json --json
```

The request is JSON based on the local/MCP binding above, with `schema_version` and `run_id` removed and the basis for the current instruction recorded in `instruction_basis`. It explicitly includes `work_item_id`, purpose, binding fields, scope, stop conditions, protocols, and the Knowledge locator. `references` may be omitted, in which case it becomes an empty array. Do not include `repository_fingerprint` in a local request; it is required in an MCP request. Undefined keys are rejected.

The generated result is a binding that can be passed directly to the existing reader, with the following additions:

- `run_id` and `schema_version: 1`
- `binding_origin: "workflow_builder"`
- `run_snapshot`: parent-child correlation, selected Skill, task, authority, assigned roles, the work item's criterion and status, and Closure Gate state

The API is `xrefkit.execution_binding.build_execution_binding(log, request)`. During generation it reads only the run log; it does not retrieve referenced content or update files. The caller specifies reference hashes from the actual versions, and the reader checks them during retrieval. Even if the generator accepts the JSON structure, it does not verify that specified local paths or remote XIDs exist.

Both readers compare the generated binding snapshot at startup. If roles, authority, task, correlation, or the work item's criterion or status changes after generation, stop, inspect the change, and recreate the binding. MCP session correlation is established during reading, so it is excluded from the snapshot. The original hand-written binding remains usable, but does not receive the generator's snapshot comparison.

This is a consistency check between information supplied by the host and the Run; it is not authentication by signature. Merely describing something in `instruction_basis` or authority does not create new execution authority. Existing guards, stop and escalation rules, verify/close, and human adoption conditions continue to apply. Do not fabricate model selection or execution observations in this generated result. Migration to the new Skill/catalog format and connection to model-routing implementation are separate change units.
