# xref: Search then read (no guessing)

Goal: when information is missing, avoid guessing; locate and read the right fragments (XIDs) first.

## Steps

1. Read `docs/000_index.md`
2. Search by theme:

```powershell
python -m fm xref search "<query>"
```

3. Show only what you need:

```powershell
python -m fm xref show <XID>
```

4. List the XIDs you read in your work notes, then proceed
