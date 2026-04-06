<!-- xid: 2D1B6A9E7C40 -->
<a id="xid-2D1B6A9E7C40"></a>

# Skill: xlsx_spec_traceability

## Purpose

Convert spreadsheet-based specifications into Markdown artifacts with stable traceability IDs, preserve the source pointer down to sheet and cell/image position, and write those IDs back into the workbook so humans can verify gaps directly in the original Excel file.

## Required References (XID)

- [Sources (PDF/Excel/Web): ingestion and referencing](../../docs/020_sources.md#xid-2FAD591BF725)

## Inputs

- source xlsx path
- optional target Markdown destination
- optional workbook or sheet scope
- optional traceability ID prefix

## Outputs

- Markdown specification fragments
- source pointer records for each extracted fragment
- screen-item descriptions derived from embedded images
- traceability ID map
- updated xlsx with written-back traceability IDs
- unresolved list

## Startup

- Confirm that the source workbook is stored under `sources/` or that the workbook copy being edited is the controlled source of truth.
- Confirm how traceability IDs should be prefixed and grouped.
- Confirm whether IDs should be written into existing columns, adjacent cells, comments, or a dedicated traceability sheet when the workbook layout has no safe free column.
- Confirm how to handle or escalate uncertainty around:
  - business rule interpretation
  - boundary values and threshold conditions
  - numeric rounding, clock/time handling, and timezone interpretation
  - concurrency assumptions and order-dependent behavior

## Planning

- Map each sheet into extraction units:
  - structured rows or tables
  - free-text specification blocks
  - embedded images and shapes
  - surrounding labels, headers, captions, and nearby cells
- Decide the target Markdown split so each fragment remains reviewable and can keep a narrow source pointer.
- Define how image-derived screen items will be connected to nearby text:
  - same row or table band
  - nearest caption or title block
  - nearest specification cells around the image anchor
- Prepare management rows for extraction units, image interpretation, ID assignment, workbook write-back, and unresolved ambiguities.

## Execution

- Read workbook content sheet by sheet and preserve the original location for every extracted item.
- For embedded images:
  - identify the image anchor position in the sheet
  - inspect surrounding cells, labels, and captions
  - connect the image to the nearest specification text that explains the same screen or area
- Extract screen items that appear only in the image and record them explicitly in Markdown.
- Assign a stable traceability ID to each requirement, rule, screen item, and image-derived item.
- Write Markdown fragments that include source pointers such as workbook path, sheet name, cell range, and image anchor.
- Write the assigned traceability IDs back into the workbook so the original Excel file can be reviewed directly without full side-by-side comparison against Markdown.

## Monitoring and Control

- If the surrounding text and the image imply different meanings, record the item as `unknown` and keep both interpretations visible.
- Do not rely on image appearance alone when nearby workbook text gives a stronger interpretation.
- Keep image-derived items linked to both:
  - the image position
  - the surrounding textual basis
- Keep IDs stable across reruns unless the semantic unit itself changed.
- If business rules, boundary values, rounding/timezone handling, or concurrency/order assumptions remain ambiguous, do not guess. Record the ambiguity as `unknown` and confirm it before finalizing the extracted result.

## Closure

- Verify that every Markdown fragment has a source pointer back to the workbook.
- Verify that every written-back ID in the workbook matches the corresponding Markdown item.
- Finalize rows as `done`, `unknown`, or `out_of_scope`.
- Preserve unresolved items where the workbook layout or image context is too weak for safe interpretation.

## Rules

- Do not treat workbook extraction as complete unless the IDs are written back into the workbook.
- Do not separate image-derived specification items from their sheet position and nearby textual basis.
- Do not collapse multiple screen items into one Markdown item if the workbook or image shows separate controls.
- Prefer direct workbook verification over Markdown-only reconciliation when checking omissions.
