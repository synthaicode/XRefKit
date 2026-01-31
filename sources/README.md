# sources/

Store original materials here (PDF/Excel/Web snapshots, etc.).

- Goal: keep verifiable “sources” inside the repo for humans
- Note: the AI’s canonical knowledge lives in `docs/` as XID-managed Markdown fragments

## Suggested layout

- `sources/pdf/...`
- `sources/excel/...`
- `sources/web/<domain>/...`

## How `docs/` references `sources/`

At the end of each fragment under `docs/`, record a source pointer such as `source_path` / `source_locator`.

See: `docs/020_sources.md`
