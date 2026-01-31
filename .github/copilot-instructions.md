# Copilot instructions (XRefKit)

This repo uses **XID** as the primary key for cross-document references to prevent link breakage across rename/move/split/merge.

## Entry points (read first)

- Human entry: `docs/000_index.md`
- Agent contract: `agent/000_agent_entry.md`

## Non-negotiable contract

- References must include `#xid-...` fragments (paths may change)
- Never change existing XIDs
- Do not guess missing information; first locate the relevant XIDs via `python -m fm xref search/show`

## XIDs are assigned by commands (not invented)

After edits, run:

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
python -m fm xref check --review
```

Note: `.xref/xid-index.json` is an XID→path cache/index. You may read it for fast resolution, but update it by running `xref check`/`index` when needed.

## Common guidance

- New Markdown: write content first → run `xref init` → use `...#xid-<XID>` managed links
- Rename/move: run `xref rewrite` → `xref check`
- Split/merge: keep the XID of the most-referenced page; assign new XIDs with `xref init`
