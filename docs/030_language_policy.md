<!-- xid: 72FB974C8236 -->
<a id="xid-72FB974C8236"></a>

# Language policy (English canonical + Japanese archive)

This repository intentionally maintains **two language trees**:

- English: `docs/` and `agent/` (canonical operational knowledge)
- Japanese: `ja/docs/` and `ja/agent/` (human-facing Japanese copies/notes)

## Why we do *not* cross-link languages by XID

XIDs are used to keep references stable across rename/move/split/merge. That works best when there is exactly one canonical set of XID-managed pages.

If we managed both languages under the same XID index, we would create unavoidable problems:

- **Duplicate XIDs** (translations often share the same “concept”)
- **Ambiguous targets** for rewrite/check (which language should a link resolve to?)
- Higher operational cost for little gain (translations are for humans, not the primary reference graph)

Therefore:

- **All managed XID references live in the English tree** (`docs/`, `agent/`)
- The Japanese tree under `ja/` is **excluded from the XID index** and does not participate in `xref rewrite/check`

## What to do when you need bilingual navigation

If you want to point between English and Japanese pages, use a simple, explicit pointer (non-managed link), for example:

- In English: `- Japanese: ../ja/docs/<path>.md`
- In Japanese: `- English: ../../docs/<path>.md`

These links are not rewritten by XRefKit; keep them stable and minimal.

## What “canonical” means here

- `docs/` is the canonical knowledge the AI reads and references by XID
- `sources/` holds originals for human verification
- `ja/` is a parallel human-facing copy; it may drift and is not part of the managed reference graph

