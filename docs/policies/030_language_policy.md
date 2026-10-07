<!-- xid: 72FB974C8236 -->
<a id="xid-72FB974C8236"></a>

# Language Policy (AI Canonical Docs + Human Language Trees)

This repository intentionally separates:

- canonical AI-facing operational Markdown in `docs/`, `knowledge/`, `skills/`,
  `capabilities/`, and `agent/`
- human-facing language trees under `human-docs/`

Current human-facing trees:

- Japanese: `human-docs/ja/`
- English: `human-docs/en/`

## Why we do *not* cross-link languages by XID

XIDs are used to keep references stable across rename/move/split/merge. That works best when there is exactly one canonical set of XID-managed pages.

If we managed both languages under the same XID index, we would create unavoidable problems:

- **Duplicate XIDs** (translations often share the same “concept”)
- **Ambiguous targets** for rewrite/check (which language should a link resolve to?)
- Higher operational cost for little gain (translations are for humans, not the primary reference graph)

Therefore:

- **All managed XID references live in the English canonical trees**
- **All canonical Markdown in `docs/`, `knowledge/`, `skills/`,
  `capabilities/`, and `agent/` is authored in English**
- The human-facing trees under `human-docs/` are **excluded from the XID index** and do not participate in `xref rewrite/check`

New canonical Markdown and substantive updates to existing canonical Markdown
must use English throughout. Keep XIDs, identifiers, paths, commands, field
names, enum values, and status values unchanged. Content intentionally showing
a localized input or output may retain that sample language when the example
requires it; its explanation remains English.

## What to do when you need bilingual navigation

If you want to point between English and Japanese pages, use a simple, explicit pointer (non-managed link), for example:

- In canonical docs: `- Japanese: ../human-docs/ja/<path>.md`
- In Japanese human docs: `- English canonical: ../../docs/<path>.md`
- In English human docs: `- English canonical: ../../docs/<path>.md`

These links are not rewritten by XRefKit; keep them stable and minimal.

## What “canonical” means here

- `knowledge/` is the canonical domain knowledge the AI reads and references by XID
- `docs/` is canonical operational documentation for this repository
- `skills/`, `capabilities/`, and `agent/` contain canonical executable or
  operating instructions
- `sources/` holds originals for human verification
- `human-docs/` holds human-facing language trees, materials, and presentation assets; it may drift and is not part of the managed reference graph
