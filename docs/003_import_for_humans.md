<!-- xid: 0CF07930F2FA -->
<a id="xid-0CF07930F2FA"></a>

# Importing Existing Documents (Human View)

This page is the human-facing entry for importing new source material into the repository.

It explains only the import mental model.
For source-recording details, see [Sources](020_sources.md#xid-2FAD591BF725).
For the full repository cycle, see [End-to-end flow](004_overall_flow_for_humans.md#xid-E01E6695A30A).

**You do not need to pre-split the documents you want to import (PDF/Excel/Web, etc.).**

## The basic import idea (do not split the source)

1. Put the original material into `sources/` as-is (PDF/Excel/HTML, etc.)
2. Let the AI reference only the relevant parts and write extracted results into `knowledge/` as Markdown fragments (“one page = one fragment”)
3. At the end of each fragment, record the source location (`sources/` path + locator)

## Why the source is not pre-split

Even if the original source is huge, the AI should not need to read everything every time.

- `sources/`: original material vault (for human verification)
- `knowledge/`: extracted knowledge fragments (XID-managed) for AI work

This split allows the AI to reference **only what is needed** by XID, while remaining resilient to rename/move operations.

## Cautions during import

When importing external information, pay explicit attention to the following:

- business rule misinterpretation
- boundary-value interpretation mismatch
- numeric rounding, clock/time handling, and timezone mismatch
- concurrency assumptions and order-dependent behavior

If any of these points is unclear from the source material alone, record it as unresolved and confirm it before treating the import result as final.

## Next

- Sources: [Sources](020_sources.md#xid-2FAD591BF725)
- Workflow: [Workflow](010_workflow.md#xid-7D1E1C0279F1)
- Full cycle: [End-to-end flow](004_overall_flow_for_humans.md#xid-E01E6695A30A)
