<!-- xid: 6C0B62D6366A -->
<a id="xid-6C0B62D6366A"></a>

# Startup Xref Routing Policy

This page defines the shared startup policy for vendor-specific startup files
(Copilot, Claude, Devin/AGENTS, Cursor, ChatGPT, etc.).

This page is the operational entry rule for startup files.
For the startup-file structure itself, see [Single-link startup architecture](012_single_link_startup_architecture.md#xid-AB27F6C19DF5).
For the boundary between base AI control and XRefKit-specific routing, see [Base control and xref routing layers](017_base_and_xref_layering.md#xid-5A1C8E4D2F90).

## Shared Policy

- Apply base AI control rules before repository-specific xref routing; see [Base control and xref routing layers](017_base_and_xref_layering.md#xid-5A1C8E4D2F90).
- Manage skill definitions and domain knowledge as separate files.
- Treat domain knowledge in `knowledge/` as shared/common.
- Treat capability definitions in `capabilities/` as reusable work-unit definitions.
- Each skill reads only what it needs, on demand, via `xref`.
- Treat `skills/_index.md` as the canonical skill catalog for listing/routing skills.
- When a task uses a Skill, start it through `python -m fm skill run --meta <path-to-meta.md> --task "<task>" --json` before opening or executing `SKILL.md`.
- Add task-specific work items with `python -m fm skill workitem` before closure; generic phase rows are not enough to close Skill-backed work.
- Record output and evidence links with `python -m fm skill artifact` before closure.
- Keep the returned `run_log` and assigned roles active; update execution, check, and handoff with `python -m fm skill phase --role <assigned-role>` so execution and checking stay separated.
- When a task follows the business-capability model, route via [Capability Routing for Agents](../agent/010_capability_routing.md#xid-1F93A7C24010).
- When a task or skill needs domain knowledge, route via:
  - `python -m fm xref search "<query>"`
  - `python -m fm xref show <XID>`
- Keep references XID-based (`#xid-...`) and keep existing XID blocks unchanged.
- After edits, run `python -m fm xref fix`.

## Centralized Detail

- Entry index: [Docs Index](000_index.md#xid-56DD6EB68343)
- Agent contract: [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
- Agent routing: [Capability Routing for Agents](../agent/010_capability_routing.md#xid-1F93A7C24010)
- Architecture rationale: [Single-link startup architecture](012_single_link_startup_architecture.md#xid-AB27F6C19DF5)
- Layer boundary: [Base control and xref routing layers](017_base_and_xref_layering.md#xid-5A1C8E4D2F90)
- Uncertainty behavior: [Uncertainty protocol](016_uncertainty_protocol.md#xid-8A666C1FD121)
