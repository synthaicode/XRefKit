<!-- xid: 2FAD591BF725 -->
<a id="xid-2FAD591BF725"></a>

# Sources (PDF/Excel/Web): ingestion and referencing

This repository keeps original materials (PDF/Excel/Web, etc.) **inside the repo** so humans can always verify them.

Important: **you do not need to pre-split the original materials**. Store the originals as-is (PDF/Excel/HTML, etc.).

The AI-readable “knowledge” is maintained as Markdown fragments under `docs/` (XID-managed). Originals under `sources/` act as the **source of truth** that each fragment points to.

## Where to put things

- Originals (binaries, HTML snapshots, etc.): `sources/`
- AI-readable knowledge (fragmented Markdown): `docs/`

## Basic ingestion pipeline

1. Add originals to `sources/` (PDF/Excel/HTML, etc.)
2. Read originals and add/update `docs/` as “one page = one fragment”
3. At the end of the change, run `init` / `rewrite` / `check` until `issues: 0`

## How to record sources (recommended)

At the end of each fragment Markdown, always record a minimal, machine-readable source pointer.

Example (PDF):

```md
## Sources

- source_type: pdf
- source_path: ../sources/vendor/product/spec-2026-01.pdf
- source_locator: page=12-14
- extracted_at: 2026-01-31
```

Example (Web):

```md
## Sources

- source_type: web
- source_url: https://example.com/docs/feature
- captured_path: ../sources/web/example.com/feature-2026-01-31.html
- captured_at: 2026-01-31
```

## Operational guidance for AI

- Do not re-read entire originals every time. First locate and read relevant fragments via `docs/000_index.md` and `python -m fm xref search/show`.
- Only when needed, follow the source pointer to consult the exact location in `sources/` (page/sheet/URL).
