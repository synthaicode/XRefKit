<!-- xid: 6C0B62D6366A -->
<a id="xid-6C0B62D6366A"></a>

# Startup Xref Routing Policy

This page defines the shared startup policy for vendor-specific startup files
(Copilot, Claude, Devin/AGENTS, Cursor, ChatGPT, etc.).

## Shared Policy

- Manage skill definitions and domain knowledge as separate files.
- Treat domain knowledge in `knowledge/` as shared/common.
- Each skill reads only what it needs, on demand, via `xref`.
- Treat `skills/_index.md` as the canonical skill catalog for listing/routing skills.
- When a task/skill needs domain knowledge, route via:
  - `python -m fm xref search "<query>"`
  - `python -m fm xref show <XID>`
- Keep references XID-based (`#xid-...`) and keep existing XID blocks unchanged.
- After edits, run `python -m fm xref fix`.

## Centralized Detail

- Entry index: [Docs Index](000_index.md#xid-56DD6EB68343)
- Agent contract: [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
- Architecture rationale: [Single-link startup architecture](012_single_link_startup_architecture.md#xid-AB27F6C19DF5)
- Uncertainty behavior: [Uncertainty protocol](016_uncertainty_protocol.md#xid-8A666C1FD121)
