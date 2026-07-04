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
| 11 | `python -m fm skill run --meta <path-to-meta.md> --task "<task>" --json` | Create the runtime envelope before opening the procedure. |
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
| 5 | MCP | `get_document_by_xid` | Resolve only needed transferred links by XID. |
| 6 | MCP | Skill and workflow catalog tools | Route task-specific work after initialization. |

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
- Skill procedure bodies before `fm skill run` has created the runtime envelope

## Link Resolution

When a needed document is referenced by XID:

- MCP mode: resolve it with `get_document_by_xid`.
- Filesystem fallback: resolve it with `python -m fm xref show <XID>`.

In both modes, load the selected fragment only. Do not follow transitive links
unless the next linked XID is independently needed for the current task.
