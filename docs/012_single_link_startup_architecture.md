<!-- xid: AB27F6C19DF5 -->
<a id="xid-AB27F6C19DF5"></a>

# Single-Link Startup Architecture for Multi-Vendor AI

This document explains the operating model used in this repository for
different AI vendors (Copilot, Claude, Devin/AGENTS, Cursor, ChatGPT, etc.).

## Problem

Each AI vendor expects different startup files, locations, and formats.
If we maintain full rules separately in each vendor file, maintenance cost and
drift risk increase.

## Design

Use a **single shared policy link** as the startup entry point.
Vendor-specific startup files stay minimal and only point to the shared policy.

- Shared startup policy:
  - [Startup xref routing policy](011_startup_xref_routing.md#xid-6C0B62D6366A)
- Canonical detail pages:
  - [Docs Index](000_index.md#xid-56DD6EB68343)
  - [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)

## How It Works

1. Vendor startup file is loaded by the tool.
2. The file points to one shared policy page.
3. The shared policy routes knowledge access through `xref`.
4. Skills pull only required domain fragments from `docs/`.

This keeps startup files thin while preserving consistent behavior.

## Responsibilities Split

- Vendor startup files:
  - minimal adapter layer
  - one-link pointer to shared policy
- Shared policy / docs:
  - actual operational rules
  - skill-to-knowledge routing contract
- `xref`:
  - reference resolution and consistency checks

## Benefits

- Minimal per-vendor differences
- One place to update policy
- Lower risk of instruction drift
- Easier onboarding and migration between tools

## Update Rule

When policy changes, update the shared docs first, then keep vendor startup
files as link-only adapters.
