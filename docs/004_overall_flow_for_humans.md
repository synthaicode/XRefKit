<!-- xid: E01E6695A30A -->
<a id="xid-E01E6695A30A"></a>

# End-to-end flow (human view)

The purpose of this repository is to keep original materials (PDF/Excel/Web, etc.) in-repo, while maintaining an AI-friendly knowledge base (fragmented Markdown). It is designed so that links remain stable even after rename/move/split/merge operations.

As a secondary benefit, you can center your workflow around XIDs and `docs/` and avoid continuously rewriting vendor-specific “instruction files” or “rule files”. When you switch tools, the knowledge location and reference method remain stable, reducing migration cost.

The basic loop is:

**`sources/` (originals) → `docs/` (extracted fragments) → `fm xref` (consistency) → CI (breakage detection)**

This page is a one-page overview of what goes where and how day-to-day work proceeds. It is easiest to think in three situations: (1) import, (2) reference, (3) update.

## Key components (canonical vs. sources)

- `sources/`: vault of original materials (the sources humans can verify)
  - e.g., PDFs, Excel files, saved HTML snapshots, images, logs
- `docs/`: extracted knowledge base (the canonical form the AI reads)
  - “one page = one fragment” Markdown with an XID
  - each fragment ends with a source pointer (`sources/` path + locator)
- `fm/`: CLI that assigns XIDs, rewrites managed links, and validates consistency

The key split is: **humans verify `sources/`**, **AI reads `docs/`**. The AI should usually work only from `docs/`, and consult `sources/` only when needed, using the source pointer recorded in the fragment.

XID is the stable identifier that makes cross-doc references resilient to path changes (`fm xref` automates rewriting and validation).

## Critical point: deciding to change an XID

XID is the primary key for references. Therefore, changing an XID is not merely a mechanical refactor: it strongly suggests that **the meaning of what the page represents** (service/feature/concept) has changed.

- Default: keep existing XIDs (preserve meaning)
- Exception: only if “keeping the same XID would make it a different thing”, create a new XID and explicitly record the old→new relationship

This cannot be fully automated. Use `xref check --review` as a signal, and require human review. If you split IDs, use `xref deprecate` so the old page remains as a compatible entry that points to its successor.

## The operational cycle

### 1) Import (add new materials)

1. Add original materials to `sources/` as-is (no pre-splitting required)
2. Let the AI reference only the necessary parts and add/update `docs/` fragments
   - keep each fragment self-contained (assumptions/conditions/conclusion/procedure)
3. At the end of each fragment, record a source pointer (e.g., `source_path` + `page=` / `sheet=` / `source_url`)
4. Run consistency commands (when local execution is possible)

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
```

Completion condition: `xref check` returns `issues: 0`.

### 2) Reference (when you need to confirm something)

Instead of scanning the originals every time, first find and read the relevant fragments in `docs/`. This keeps AI reads small and stable.

1. Start at `docs/000_index.md`
2. Find candidate XIDs: `python -m fm xref search "<query>"`
3. Read only what you need: `python -m fm xref show <XID>`

If needed, bundle neighbors:

```powershell
python -m fm ctx pack --seed <XID> --depth 1 --out .xref/pack.md
```

### 3) Update (edit or reorganize existing docs)

Day-to-day edits happen in `docs/`. The important part is to run the consistency steps after structural changes.

- Edit content normally
- After rename/move/split/merge: run `xref rewrite` and `xref check` (never remove XID blocks)

## What “fragmentation” means here

Fragmentation is **not** splitting the original materials. It is shaping the AI-readable knowledge into units that can be referenced and loaded on demand.

- originals stay in `sources/` (for human verification)
- fragments live in `docs/` (for AI work and reuse)

## Common failure modes and mitigations

- Extracted docs but forgot to record source pointers
  - Fix: always keep `source_path` + locator (page/sheet/url) at the end of a fragment
- Fragments lack prerequisites and cannot be used standalone
  - Fix: add assumptions/conditions up front; link related fragments by XID
- Links break after moving files
  - Fix: `xref rewrite` → `xref check` (and run in CI)

## Related

- Entry index: [docs/000_index.md](000_index.md#xid-56DD6EB68343)
- Sources: [docs/020_sources.md](020_sources.md#xid-2FAD591BF725)
- Workflow: [docs/010_workflow.md](010_workflow.md#xid-7D1E1C0279F1)
- Agent contract: [agent/000_agent_entry.md](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
