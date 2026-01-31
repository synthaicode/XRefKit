# Instructions (XRefKit)

This repo uses **XID** as the primary key for cross-document references.

## Entry points

- `docs/000_index.md` (human entry)
- `agent/000_agent_entry.md` (agent contract)

## Contract

- References must include `#xid-...` fragments (paths may change)
- Never change or remove existing XID blocks
- Do not guess missing information; use `python -m fm xref search` / `python -m fm xref show`

## Commands

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
python -m fm xref check --review
```
