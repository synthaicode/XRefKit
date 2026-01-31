# agent: Extract knowledge (turn into reusable fragments)

Goal: extract reusable fragments from existing notes/logs/specs/conversations and freeze them into `docs/`.

## Decision (reuse vs new extraction)

- First search existing `docs/` and add only the missing delta:

```powershell
python -m fm xref search "<query>"
python -m fm xref show <XID>
```

- If existing docs are sufficient, do not create new pages; finish by linking via XIDs

## Recommended fragment shape

Keep “one page = one fragment”:

- What you learned (conclusion)
- When it applies (conditions)
- Procedure (short bullets)
- Examples (optional)
- Related XID references

## Finalize

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
```
