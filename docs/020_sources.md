<!-- xid: 2FAD591BF725 -->
<a id="xid-2FAD591BF725"></a>

# Sources (PDF/Excel/Web): ingestion and referencing

This repository keeps original materials (PDF/Excel/Web, etc.) **inside the repo** so humans can always verify them.

Important: **you do not need to pre-split the original materials**. Store the originals as-is (PDF/Excel/HTML, etc.).

The AI-readable domain knowledge is maintained as Markdown fragments under `knowledge/` (XID-managed). Originals under `sources/` act as the **source of truth** that each fragment points to.

This page is the detailed source-recording rule.
For the import mental model, see [Importing existing documents](003_import_for_humans.md#xid-0CF07930F2FA).
For the broader repository cycle, see [End-to-end flow](004_overall_flow_for_humans.md#xid-E01E6695A30A).

## Where to put things

- Originals (binaries, HTML snapshots, etc.): `sources/`
- AI-readable knowledge (fragmented Markdown): `knowledge/`

## Basic ingestion pipeline

1. Add originals to `sources/` (PDF/Excel/HTML, etc.)
2. Read originals and add/update `knowledge/` as “one page = one fragment”
3. Record a source pointer in each resulting fragment
4. At the end of the change, run `init` / `rewrite` / `check` until `issues: 0`

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

## Exception for xddp-related sources

As a repository-wide default, originals should remain inside `sources/`.
However, `xddp`-related materials may be handled as an explicit exception by recording only external references and not mirroring the original files in this repo.

Use this exception only for `xddp` materials.
Do not generalize it to other source families unless the rule is updated intentionally.

Example (external file reference):

```md
## Sources

- source_type: file_link
- source_uri: \\server\share\xddp\ET2018_04.pdf
- source_locator: page=12-14
- access_note: xddp source is managed externally and is not mirrored in this repo
```

Example (external web reference):

```md
## Sources

- source_type: web
- source_url: https://example.com/xddp/method
- source_locator: section=overview
- access_note: xddp source is referenced externally and is not mirrored in this repo
```

## Operational guidance for AI

- Do not re-read entire originals every time. First locate and read relevant fragments via `knowledge/000_index.md` and `python -m fm xref search/show`.
- Only when needed, follow the source pointer to consult the exact location in `sources/` (page/sheet/URL).
- When importing external information, explicitly watch for:
  - business rule misinterpretation
  - boundary-value interpretation mismatch
  - numeric rounding, clock/time handling, and timezone mismatch
  - concurrency assumptions and order-dependent behavior
- If any of the above remains unclear from the source, mark it as unresolved and confirm with the user or source owner before finalizing the extracted knowledge.
