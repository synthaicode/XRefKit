<!-- xid: C3A1F78D9B22 -->
<a id="xid-C3A1F78D9B22"></a>

# XRefKit Startup Contract

This page is the repository-native startup contract for XRefKit itself.

XRefKit must be able to start without XRefKit MCP. MCP is a distribution and
resolution interface for XRefKit governance content, not the prerequisite for
the repository's own startup contract.

## Startup Target

Vendor startup files such as `AGENTS.md`, `CLAUDE.md`, and `CHATGPT.md` point
here as the first repository-governed startup read.

Use this page when the active runtime is the XRefKit repository itself, local
filesystem fallback, or an AI tool that has not yet established an XRefKit MCP
session.

Use `docs/core/contracts/079_startup_contract_pack.md#xid-D4E8A1C63B57` only
as the MCP model-facing compressed startup body returned by
`get_startup_context`.

## Required Startup Reading

At XRefKit startup, apply the following repository-native sequence:

1. Read the active vendor startup file.
2. Read this XRefKit startup contract.
3. Apply the base-control and xref-routing source set below.
4. Route task-specific work only after startup is complete.

Base-control and xref-routing source set:

1. `agent/000_agent_entry.md#xid-0B5C58B5E5B2`
2. `docs/core/models/017_base_and_xref_layering.md#xid-5A1C8E4D2F90`
3. `docs/core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A`
4. `docs/core/contracts/016_uncertainty_protocol.md#xid-8A666C1FD121`
5. `docs/core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11`
6. `docs/core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED`

These source documents are the repository-native startup set. They are not
MCP-only documents.

## Startup Invariants

- XRefKit startup does not require MCP.
- MCP mode may return an equivalent startup contract pack, but that pack is a
  transport-specific model-facing compression.
- Do not treat the MCP pack as the canonical startup target for XRefKit itself.
- Apply base AI control before XRefKit-specific routing.
- Keep Skill procedure bodies, domain knowledge, and work logs separate.
- Treat `docs/` links as lookup handles, not recursive startup-load
  instructions.
- Resolve only the XIDs needed for the active task after startup.
- Do not invent missing project rules. Mark the rule as missing and suggest
  whether it belongs in AGENTS/startup, a Skill, knowledge, or workflow
  definition.

## Task Routing After Startup

After startup, route work by user intent:

- Use `skills/_index.md` and needed `skills/index/*` files only when a Skill
  must be selected.
- Select the Skill semantically before direct `--meta <path>` execution.
- Create the runtime envelope with `python -m xrefkit skill run --meta <path> --task
  "<task>" --json` before opening or executing `SKILL.md`.
- Load selected knowledge, workflow, and linked documents only when the active
  task or selected Skill requires them.

## MCP Relationship

When MCP is configured, clients may use MCP tools to receive and resolve the
same governance contract:

- `get_repository_identity` is an optional content-free cache preflight.
- `get_startup_context` returns the MCP startup payload.
- `startup_contract_pack.body` is the MCP model-facing compressed startup text.
- `prompt_flow_protocol` is the MCP initialization contract for one prompt
  spanning generic workflow and delegated Skill Runs. It defines correlation,
  reconciliation, explicit status projection, and uncertainty boundaries.
- `get_document_by_xid` resolves needed linked XIDs.
- `get_skill` transfers selected Skill content.
- After `xrefkit skill run` creates `run_id`, `bind_skill_run` binds that ID to
  the active MCP session. The client then executes the returned
  `client_record_command` against the returned `run_log` before task-specific
  XID access.

In MCP mode, an XID-bearing path such as `docs/...md#xid-...` is a lookup
handle and diagnostic location, not an instruction for the client to search its
local filesystem. The client resolves the selected body by calling
`get_document_by_xid` with the XID. Any filesystem lookup needed to map that XID
to content is an MCP server-side responsibility.

This is the MCP mode for clients. It does not change the repository-native rule
that XRefKit's own startup contract must be valid without MCP.
