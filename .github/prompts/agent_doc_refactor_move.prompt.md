# agent: Refactor docs (rename/move/split/merge)

Goal: perform rename/move/split/merge without breaking managed references (XID links).

## Rules

- Never change or remove existing XIDs
- Only links that include `#xid-...` are “managed links”
- Use `xref check` and fix until `issues: 0`

## Steps

1. Apply the rename/move/split/merge
2. Restore consistency:

```powershell
python -m fm xref rewrite
python -m fm xref check
```

3. If you created new Markdown files (split/merge), assign XIDs and re-check:

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
```
