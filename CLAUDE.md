# XRefKit (Claude Code)

This repo uses **XID** as the primary key for cross-document references to prevent link breakage across rename/move/split/merge.

## Entry points (read first)

- Human entry: `docs/000_index.md`
- Agent contract: `agent/000_agent_entry.md`

## Contract (required)

- References must include `#xid-...` fragments (paths may change)
- Never change existing XIDs
- Do not guess missing information; use `python -m fm xref search/show` to find and read the relevant XIDs

## After changes

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
python -m fm xref check --review
```
