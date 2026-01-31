# xref: After editing docs (consistency update)

Goal: finish changes without breaking the repo’s XID-based link system.

## Steps

1. Edit the Markdown files (do not remove XID blocks)
2. Run:

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check --review
```

3. Only if XIDs were added/changed (i.e., the XID index changed), regenerate the lookup file (optional):

```powershell
python -m fm xref index > .xref/xid-index.json
```

4. If `xref check` reports issues, fix them and re-run `rewrite` / `check`

## If you decide the XID must change (semantic change)

If meaning changed enough that the XID should be split, keep the old page and point it to the successor:

```powershell
python -m fm xref deprecate <OLD_XID> <NEW_XID> --note "reason (optional)"
python -m fm xref rewrite
python -m fm xref check --review
```

## Notes

- Never change existing XIDs
- References must include `#xid-...` fragments
