<!-- xid: A264E296AC71 -->
<a id="xid-A264E296AC71"></a>

# Initialization Sequence Reference

This page summarizes which files and MCP payloads are read during XRefKit
initialization, and in what order.

Use this page as a sequence reference. The repository-native startup target is
`docs/core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22`.
The shared xref routing policy remains
`docs/core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A`.

## Rule

Initialization order is not discovered by following `docs/` cross-references.
XRefKit itself must be able to initialize without MCP. MCP mode is a client
transport for receiving the same governance contract, not the base prerequisite.

`docs/` links are lookup handles. They do not imply recursive startup loading.

## XRefKit Repository-Native Mode

This is the base mode. Use it for XRefKit itself and whenever MCP is not yet
available.

| Step | File | Purpose |
| --- | --- | --- |
| 1 | Active startup file, such as `AGENTS.md` | Minimal vendor-specific pointer into the repository startup contract. |
| 2 | `docs/core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22` | Repository-native XRefKit startup contract. |
| 3 | `agent/000_agent_entry.md#xid-0B5C58B5E5B2` | Agent operational contract. |
| 4 | `docs/core/models/017_base_and_xref_layering.md#xid-5A1C8E4D2F90` | Base-control and xref-routing layer boundary. |
| 5 | `docs/core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A` | Shared xref routing policy. |
| 6 | `docs/core/contracts/016_uncertainty_protocol.md#xid-8A666C1FD121` | Uncertainty handling contract. |
| 7 | `docs/core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11` | Context-direction security guard. |
| 8 | `docs/core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED` | Shared memory and event-log operations. |
| 9 | `skills/_index.md` and needed `skills/index/*` files | Skill routing catalog, only when a Skill must be routed. |
| 10 | Selected Skill `meta.md` | Runtime metadata and operating envelope inputs. |
| 11 | `python -m xrefkit skill run --meta <path-to-meta.md> --task "<task>" --json` | Create the runtime envelope before opening the procedure. |
| 12 | Returned `skill_doc` | Open the selected `SKILL.md` only after the runtime envelope exists. |
| 13 | Selected workflow / knowledge XIDs | Load only the fragments required by the current task. |

## MCP Client Mode

When the XRefKit MCP server is configured, the client must not read governance
Markdown directly from the local filesystem.

| Step | Source | Tool / File | Purpose |
| --- | --- | --- | --- |
| 1 | MCP | `get_repository_identity` | Optional content-free cache namespace preflight. |
| 2 | MCP | `get_startup_context` | First governance-content load and source of startup `load_order`. |
| 3 | MCP response | `load_order` | Ordered XIDs to apply before task-specific routing. |
| 4 | MCP response | `references` | Document bodies returned for the startup XIDs. |
| 5 | MCP response | `prompt_flow_protocol` | Apply Prompt Flow identity, delegation, reconciliation, and uncertainty boundaries before task routing. |
| 6 | MCP | `get_document_by_xid` | Resolve only needed transferred links by XID. |
| 7 | MCP | Skill and workflow catalog tools | Route task-specific work after initialization. |

The Skill catalog is a routing surface, not an execution-tool manifest:

- `list_skills` and `rank_skills_for_purpose` do not carry each candidate's
  `required_tools`.
- After a Skill is selected, `get_skill` or `get_skill_requirements` returns
  that Skill's tool requirements.
- `get_skill_requirements` returns requirement metadata without procedure
  bodies; use `get_skill` when the selected procedure itself is needed.

When one prompt spans multiple runs, the client initializes one Prompt Flow
after `get_startup_context`, preserves its correlation fields, and follows the
returned reconciliation contract before attempting parent closure.

The client-side cache integration is:

```python
flow = cache.initialize_prompt_flow(startup_context, prompt_text)
root_run_correlation = flow.correlation()
child_run_correlation = flow.correlation(
    parent_run_id=parent_run_id,
    work_item_id="WI-001",
    node_id="node-001",
)
```

The client records `flow.initialized` locally without storing the raw prompt;
the prompt is represented by a hash. The client does not select Skills or
execute reconcile.

For a host that saved the MCP response as `startup.json`, the repository
client bridge is:

```powershell
python -m xrefkit mcp flow-init `
  --startup-context startup.json `
  --prompt "the user prompt" `
  --cache-root .xrefkit/mcp-cache `
  --repository-fingerprint <repository-fingerprint>
```

The JSON result supplies `root_run_correlation` for the first
`workflow run` or `skill run`, and the returned `PromptFlowContext` supplies
child correlation for later delegation.

An MCP host binds a started Skill Run through the client adapter:

```python
binding = await flow.bind_skill_run(
    mcp_call_tool,
    run_id=run_id,
    skill_id=skill_id,
    parent_run_id=parent_run_id,
    work_item_id="WI-001",
    node_id="node-001",
)
```

The adapter rejects a server response whose correlation fields do not match the
client Flow context.

For a host that invokes the repository workflow CLI, use the client builders to
preserve the same boundary instead of reconstructing correlation arguments in
host-specific code:

```python
run_args = flow.workflow_run_arguments(
    task="Execute generic work",
    parent_run_id=parent_run_id,
    work_item_id="WI-001",
    node_id="node-001",
    purpose="Deliver the requested change",
    expected_evidence=["pytest output"],
)
routing_args = flow.workflow_routing_arguments(
    log="work/sessions/parent.md",
    selected_skill="skill_a",
    candidates=["skill_a", "skill_b"],
    reason="The Work Item matches skill_a",
    target_work_item="WI-001",
)
```

These methods build and validate arguments; the host remains responsible for
executing the command under its own authority. They do not select a Skill,
start recovery, or close a Prompt Flow.

Current MCP startup XID order observed for this repository:

1. `0B5C58B5E5B2` - `agent/000_agent_entry.md`
2. `5A1C8E4D2F90` - `docs/core/models/017_base_and_xref_layering.md`
3. `6C0B62D6366A` - `docs/core/contracts/011_startup_xref_routing.md`
4. `8A666C1FD121` - `docs/core/contracts/016_uncertainty_protocol.md`
5. `A7F3C92D4E11` - `docs/core/contracts/053_context_direction_security_guard.md`
6. `4A423E72D2ED` - `docs/core/contracts/015_shared_memory_operations.md`

This list records the current server-returned sequence for readability. The
client must still follow the live `load_order` returned by
`get_startup_context`, because the server may change the bundle without relying
on Markdown link traversal.

## Do Not Load

Do not load these during initialization by default:

- `docs/000_index.md` as a bulk context file
- every `Related` link in a document
- every `knowledge_slots` binding or `capability` reference before route selection
- workflow pages that are not selected by the current task
- Skill procedure bodies before `xrefkit skill run` has created the runtime envelope

## Link Resolution

When a needed document is referenced by XID:

- MCP mode: resolve it with `get_document_by_xid`.
- Filesystem fallback: resolve it with `python -m xrefkit xref show <XID>`.

In both modes, load the selected fragment only. Do not follow transitive links
unless the next linked XID is independently needed for the current task.
