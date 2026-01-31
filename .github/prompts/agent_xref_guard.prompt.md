# agent: xref guard (stop breakage)

Goal: fix managed link breakage with minimal changes, until `issues: 0`.

## Steps

1. Check the current state:

```powershell
python -m fm xref check
```

2. If rename/move is the cause, recover mechanically:

```powershell
python -m fm xref rewrite
python -m fm xref check
```

3. If issues remain, follow `xref check` output and fix links
4. Repeat until `issues: 0`
