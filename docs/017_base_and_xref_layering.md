<!-- xid: 5A1C8E4D2F90 -->
<a id="xid-5A1C8E4D2F90"></a>

# Base Control and Xref Routing Layers

This page clarifies the internal split between the base AI control layer and the XRefKit-specific routing layer.

The repository currently keeps both layers together because the startup path must stay simple and reliable. The goal is not to split repositories now. The goal is to keep the layers conceptually separate so they can be evolved or extracted later if needed.

This page is the boundary definition.
It does not restate the startup-file architecture in detail; see [Single-link startup architecture](012_single_link_startup_architecture.md#xid-AB27F6C19DF5) for that.

## Layer 1: Base Control

This layer defines how the base AI must behave before repository-specific knowledge routing begins.

Typical contents:

- startup contract shape
- boundary and authority handling
- context-direction guard
- uncertainty / `unknown` handling
- stop / escalate behavior
- logging and traceability expectations

These rules are about controlling a capable model so it does not silently change scope, authority, or confidence level.

Representative pages in this repository:

- [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
- [Startup xref routing policy](011_startup_xref_routing.md#xid-6C0B62D6366A)
- [Shared memory operations](015_shared_memory_operations.md#xid-4A423E72D2ED)
- [Uncertainty protocol](016_uncertainty_protocol.md#xid-8A666C1FD121)
- [Context direction security guard](053_context_direction_security_guard.md#xid-A7F3C92D4E11)

## Layer 2: XRefKit-Specific Routing

This layer defines how this repository stores, resolves, and loads knowledge.

Typical contents:

- XID as the primary key
- `xref search/show/rewrite/check/fix`
- `knowledge/` as shared domain fragments
- `skills/` as behavior and procedure
- `capabilities/` as reusable work-unit definitions
- `flows/` as workflow control structure

These rules are about how XRefKit routes knowledge and keeps references durable.

Representative pages in this repository:

- [Overview](000_overview.md#xid-7C6C2B46A9D1)
- [Workflow](010_workflow.md#xid-7D1E1C0279F1)
- [Skill authoring with xref](013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)

## Why Keep Them Together For Now

- startup file loading is not reliably multi-stage across tools
- repository-specific entry points are more likely to be read when they stay local
- XRefKit routing is the actual execution environment for this repository

So the practical design is:

`base control -> xref routing -> task execution`

inside one repository.

## Operational Rule

When reading this repository:

1. apply base control first
2. then follow XRefKit routing and loading rules
3. then execute task-specific skills and workflows

Do not treat XRefKit routing rules as a replacement for base control. Do not treat base control as a substitute for repository-specific knowledge routing.

## Extraction Boundary

If these layers are ever separated into different repositories, the extraction boundary should be:

- exportable:
  - startup contract
  - context-direction guard
  - uncertainty / `unknown` policy
  - generic logging and escalation control
- remain in XRefKit:
  - XID model
  - `fm xref` commands
  - repository structure and routing
  - skill / capability / flow / knowledge organization

## Related

- [Single-link startup architecture](012_single_link_startup_architecture.md#xid-AB27F6C19DF5)
- [Startup xref routing policy](011_startup_xref_routing.md#xid-6C0B62D6366A)
- [Uncertainty protocol](016_uncertainty_protocol.md#xid-8A666C1FD121)
- [Context direction security guard](053_context_direction_security_guard.md#xid-A7F3C92D4E11)
