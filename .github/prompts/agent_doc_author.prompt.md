# agent: Author docs (freeze knowledge into `docs/`)

Goal: add research results, decisions, and operational rules as reusable Markdown fragments under `docs/` (“one page = one fragment”).

## Rules

- References must include `#xid-...` fragments (paths are expected to change)
- Never change existing XIDs
- Do not invent new XIDs; assign them at the end via `xref init`

## Steps

1. Start from `docs/000_index.md`; use `python -m fm xref search/show` as needed
2. Create `docs/<NNN>_<slug>.md` and ensure it stands alone:
   - assumptions / purpose / procedure / examples / exceptions (as needed)
   - cross-references use `...#xid-...` (leave placeholders until XIDs exist)
3. Finalize consistency:

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
```

4. Finish when `xref check` reports `issues: 0`
