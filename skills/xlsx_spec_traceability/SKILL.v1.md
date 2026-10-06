---
schema_version: 1
skill_id: xlsx_spec_traceability
xid: A7C3E9D2F610
summary: extract spreadsheet specifications into Markdown, preserve workbook traceability, and write IDs back into the source workbook
applies_when:
- user needs to convert Excel-based specifications into Markdown artifacts while preserving source traceability and reducing review burden in the original workbook
exclusions:
- Human acceptance or publication approval remains with the requester
- Unsupported facts, claims, or interpretation remain explicit as unknown
inputs:
- source xlsx path, optional target Markdown destination, optional workbook or sheet scope, optional traceability ID prefix
outputs:
- Markdown specification fragments, image-linked screen-item descriptions, traceability ID map, updated xlsx with written-back IDs, unresolved list
criteria:
- id: artifact_traceability
  statement: Produced artifacts retain the source pointers, reproducible inputs, and verification evidence required by this Skill
  verification: Inspect the artifact paths, source links, and verification record
- id: acceptance_boundary
  statement: Human acceptance and publication decisions remain explicit and are not inferred from successful generation
  verification: Check the handoff and acceptance boundary before closure
- id: output_closure
  statement: The declared artifact output exists and unresolved items are returned
  verification: Check output paths, open items, and handoff
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: sources
  query: sources for PDF, Excel, and web ingestion and referencing
  required_when: Required when applying this Skill's source or production guidance
  seed_xids:
  - 2FAD591BF725
control_refs: []
aliases:
- 2D1B6A9E7C40
- 5A7C2D4E9130
---
<!-- xid: A7C3E9D2F610 -->
<a id="xid-A7C3E9D2F610"></a>

# Skill: xlsx_spec_traceability

## Purpose

Convert spreadsheet-based specifications into Markdown artifacts with stable traceability IDs, preserve the source pointer down to sheet and cell/image position, and write those IDs back into the workbook so humans can verify gaps directly in the original Excel file.

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

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: xlsx_spec_traceability

## Purpose

Convert spreadsheet-based specifications into Markdown artifacts with stable traceability IDs, preserve the source pointer down to sheet and cell/image position, and write those IDs back into the workbook so humans can verify gaps directly in the original Excel file.

## Required References (XID)

- [Sources (PDF/Excel/Web): ingestion and referencing](../../docs/reference/020_sources.md#xid-2FAD591BF725)

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

## Reporting Contract (共通報告)



- reporting_profile: artifact_traceability

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: extract spreadsheet specifications into Markdown, assign traceability IDs, connect embedded images to nearby specification text, and write the IDs back into the workbook

- use_when: user needs to convert Excel-based specifications into Markdown artifacts while preserving source traceability and reducing review burden in the original workbook

- input: source xlsx path, optional target Markdown destination, optional workbook or sheet scope, optional traceability ID prefix

- output: Markdown specification fragments, image-linked screen-item descriptions, traceability ID map, updated xlsx with written-back IDs, unresolved list

- constraints: keep the workbook path and sheet/cell/image position explicit; do not separate image-derived items from the source location they came from; write IDs back into the original workbook or the controlled workbook copy used as the source of truth

- lifecycle:
  - startup: confirm source workbook path, target scope, and ID policy
  - planning: map sheets, tables, free-text blocks, and embedded images into extraction units
  - execution: extract textual specification, connect image position to nearby text, create Markdown fragments, assign IDs, and write the IDs back to the workbook
  - monitoring_and_control: record ambiguity when image meaning and surrounding text disagree
  - closure: finalize Markdown outputs, verify workbook write-back, and preserve source pointers

- tags: `xlsx`, `excel`, `specification`, `traceability`, `image`, `import`

- knowledge_slots:
  - name=sources; bind=2FAD591BF725
