<!-- xid: 7D1E1C0279F1 -->
<a id="xid-7D1E1C0279F1"></a>

# Workflow (prevent link breakage)

## Minimal rules

- Keep the XID block near the top of each managed Markdown file
- Cross-file references must use links that include `#xid-<XID>`
- After rename/move/split/merge, run `python -m fm xref rewrite`
- Continuously validate with `python -m fm xref check` (e.g., in CI)
- For one-shot maintenance, use `python -m fm xref fix` (runs init + rewrite + check)
- For human review hints during updates, use `python -m fm xref check --review` (best-effort)
- When creating new documents, follow the existing format conventions, character encoding, and encoding form used in the surrounding repository area unless an intentional change is required
- When editing source files, preserve the existing format conventions, character encoding, and encoding form unless an intentional change is required
- When adding entries to XML, preserve the existing semantic grouping and insert entries in the structurally appropriate location instead of appending mechanically to the end
- After editing structured source files such as XML, JSON, YAML, or similar parseable formats, run a deterministic parser or equivalent deterministic validation step and confirm there is no parse error

## Fixed procedure for any AI using this repo

1. Read the entry index: `docs/000_index.md`
2. Find candidate pages: `python -m fm xref search "<query>"` and list the XIDs to read
3. Read only what you need: `python -m fm xref show <XID>`
4. Do the work and record the XIDs you referenced in the work log

When a running skill needs additional domain knowledge, use the same route on demand:
`xref search` -> `xref show` -> resume the skill with the retrieved XID context.

## Common operations

### Add a new doc

1. Add a Markdown file under `docs/`, `agent/`, `knowledge/`, `capabilities/`, or `skills/`
2. Follow the existing format conventions, character encoding, and encoding form used by nearby managed files unless the task explicitly requires a controlled change
3. Assign XIDs: `python -m fm xref init`
4. If needed: `python -m fm xref rewrite`

### Ingest sources (PDF/Excel/Web → knowledge)

Store originals under `sources/` so humans can always verify them. Treat `knowledge/` Markdown fragments (with XIDs) as the canonical domain knowledge the AI reads.

1. Add original materials to `sources/`
2. Read the originals and add/update `knowledge/` as “one page = one fragment” (record sources at the end)
3. Run consistency steps

```powershell
python -m fm xref fix
```

Details: [Sources](020_sources.md#xid-2FAD591BF725)

### Let the AI write managed docs (recommended)

- Let the AI write normal Markdown (no need to invent XIDs)
- After generation, run `python -m fm xref init` to assign XIDs
- From then on, use `...#xid-...` managed links

### Rename / move

- Never remove `<!-- xid: ... -->` and `<a id="xid-..."></a>`
- After changes: `python -m fm xref rewrite`

### Edit structured source files

- Preserve the existing formatting style, character encoding, and encoding form unless the task explicitly requires a controlled change
- When adding entries to XML, inspect the surrounding grouping, ordering, and meaning boundaries first, then insert the new entry where that structure says it belongs
- When editing structured source files such as XML, JSON, YAML, or similar parseable formats, run a deterministic parser or equivalent deterministic validation step after the edit
- Do not treat the edit as complete until the file parses without error
- When a project-specific formatter, linter, compiler, or validator already exists for that format, prefer that validator over ad hoc checking

### Split

- Keep the original file’s XID in the original file (preserve existing links)
- New split-out files get new XIDs via `python -m fm xref init`
- After rewiring references: `python -m fm xref rewrite`

### Merge

- Keep the XID of the page with more inbound references
- Before deleting anything, repoint references to the surviving page
- Only delete when `python -m fm xref check` reports `broken_xref: 0`

### Semantic change (switch to a new XID)

If keeping the same XID would turn the page into “a different thing”, do not delete the old page. Create a successor page and explicitly record the relationship.

1. Create the new page (new XID) and move the new meaning there (run `xref init` if needed)
2. Record old→new relationship:

```powershell
python -m fm xref deprecate <OLD_XID> <NEW_XID> --note "reason (optional)"
```

3. Verify consistency:

```powershell
python -m fm xref rewrite
python -m fm xref check --review
```

`python -m fm xref check` and `python -m fm xref fix` return exit code `1` when issues are found.
