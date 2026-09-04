<!-- xid: 5A1C8E4D2F90 -->
<a id="xid-5A1C8E4D2F90"></a>

# Base Control and Xref Routing Layers

This page clarifies the internal split between the base AI control layer and the XRefKit-specific routing layer.

The repository currently keeps both layers together because the startup path must stay simple and reliable. The goal is not to split repositories now. The goal is to keep the layers conceptually separate so they can be evolved or extracted later if needed.

This page is the boundary definition.
It does not restate the startup-file architecture in detail.

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

Representative pages are listed from `docs/000_index.md#xid-56DD6EB68343`
when lookup is needed.

## Layer 2: XRefKit-Specific Routing

This layer defines how this repository stores, resolves, and loads knowledge.

Typical contents:

- XID as the primary key
- `xref search/show/rewrite/check/fix`
- `knowledge/` as shared domain fragments
- `skills/` as executable procedure carrying the capability/tuning/responsibility identity

These rules are about how XRefKit routes knowledge and keeps references durable.

Representative pages are listed from `docs/000_index.md#xid-56DD6EB68343`
when lookup is needed.

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
  - `xrefkit xref` commands
  - repository structure and routing
  - skill / knowledge organization


