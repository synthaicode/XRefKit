<!-- xid: 0B5C58B5E5B2 -->
<a id="xid-0B5C58B5E5B2"></a>

# Agent Entry (L0 / always read)

This file is the agent-side entry point. Human-facing background lives under `docs/`. Keep this page short and stable: it is the **operational contract**.

Related: [Overview](../docs/000_overview.md#xid-7C6C2B46A9D1)

## Contract (required)

- Use XIDs as primary keys for references (links must include `#xid-...`)
- Do not fill missing information by guessing; first find the relevant XIDs and read them
- After rename/move/split/merge, run link validation (`xref check`)

## How to reference (fixed procedure)

1. Read the entry index: `docs/000_index.md`
2. Find candidate XIDs: `python -m fm xref search "<query>"`
3. Read only what you need: `python -m fm xref show <XID>`
