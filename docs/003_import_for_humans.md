<!-- xid: 0CF07930F2FA -->
<a id="xid-0CF07930F2FA"></a>

# Importing existing documents (human view)

The `docs/` folder in this repository is split into multiple files to keep the system’s own documentation and operations (XID/link consistency) maintainable.

**You do not need to pre-split the documents you want to import (PDF/Excel/Web, etc.).**

## The basic import idea (do not split the source)

1. Put the original material into `sources/` as-is (PDF/Excel/HTML, etc.)
2. Let the AI reference only the relevant parts and write extracted results into `docs/` as Markdown fragments (“one page = one fragment”)
3. At the end of each fragment, record the source location (`sources/` path + locator)

## Why `docs/` is split (for users)

Even if the original source is huge, the AI should not need to read everything every time.

- `sources/`: original material vault (for human verification)
- `docs/`: extracted knowledge fragments (XID-managed) for AI work

This split allows the AI to reference **only what is needed** by XID, while remaining resilient to rename/move operations.

## Next

- Workflow: `docs/010_workflow.md`
- Sources: `docs/020_sources.md`
