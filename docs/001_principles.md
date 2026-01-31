<!-- xid: 71DFD9319CFB -->
<a id="xid-71DFD9319CFB"></a>

# Principles (Contract)

The goal is not to “centralize everything into one giant doc”. The goal is to make it possible to **reference and read only the needed fragments correctly**.

## Principles

1. **XID is the primary key**
   - Paths and filenames are expected to change
   - References must include `#xid-...` so `rewrite` can repair path breakage
2. **Separate entry (L0) from details (L1/L2)**
   - Keep entry pages short and stable (always read)
   - Let detailed pages grow (read only when needed)
3. **Fragments are self-contained**
   - One page / one fragment should stand on its own (assumptions, conditions, conclusion)
4. **Automate registration and validation**
   - Multi-format ingestion is inherently messy; don’t over-standardize input
   - Instead, mechanically validate XIDs/links/index for the Markdown output

## Prohibitions (protect link assets)

- Do not change existing XIDs (it breaks references)
- Do not delete a referenced page without updating its references

## When you must change an XID (do not break meaning)

If the meaning changes so much that “keeping the same XID would make it a different thing”, do not delete or overwrite the old page with unrelated content. Keep compatibility by explicitly recording the relationship:

- Important: Changing an XID is not a mechanical refactor. It is a decision that **changes what the ID means** (service/feature/concept). Treat it as a semantic change; human review is required.
- Put the new meaning in a new page (new XID)
- Keep the old page (old XID) and add a successor link
- In the new page, add a predecessor link

To standardize this, use:

```powershell
python -m fm xref deprecate <OLD_XID> <NEW_XID> --note "reason (optional)"
```
