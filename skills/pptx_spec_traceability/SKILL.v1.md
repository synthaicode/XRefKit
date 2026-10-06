---
schema_version: 1
skill_id: pptx_spec_traceability
xid: A6D3F8B1C520
summary: extract PowerPoint specifications into traceable Markdown and write IDs back into the deck
applies_when:
- user needs to convert PowerPoint-based specifications into Markdown artifacts while preserving slide-level traceability and reducing review burden in the original deck
exclusions:
- do not separate visual items from their slide context or treat Markdown-only reconciliation as complete
inputs:
- source pptx path, optional target Markdown destination, optional slide scope, optional traceability ID prefix
outputs:
- Markdown specification fragments, slide-item descriptions, traceability ID map, updated pptx with written-back IDs, unresolved list
criteria:
- id: source_traceability
  statement: Every Markdown fragment and written-back ID points to the deck slide and object position.
  verification: Reconcile each fragment and deck ID against the source deck.
- id: visual_context
  statement: Images, shapes, callouts, and nearby explanatory text remain connected.
  verification: Inspect object position, labels, notes, and interpretation evidence.
- id: writeback
  statement: IDs written into the deck match the corresponding Markdown items.
  verification: Perform direct deck verification and preserve unresolved ambiguities.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: sources
  query: sources PDF Excel Web ingestion and referencing
  required_when: Required for source-pointer and evidence handling
  seed_xids:
  - 2FAD591BF725
control_refs: []
aliases:
- 4C8E2B1F6A20
- 7F4C1A2D9E60
---
<!-- xid: A6D3F8B1C520 -->
<a id="xid-A6D3F8B1C520"></a>

# Skill: pptx_spec_traceability

## Purpose
Convert presentation specifications into Markdown with stable traceability IDs and write those IDs back into the PowerPoint deck.

## Method
1. Confirm the source deck is under `sources/` or is the controlled source of truth, plus slide scope and ID policy.
2. Resolve the sources Knowledge.
3. Map slides, text, tables, images, shapes, notes, labels, and callouts into reviewable extraction units.
4. Preserve slide number, object position, nearby textual basis, and visual-only items; assign stable IDs.
5. Write Markdown fragments and IDs back into the deck, then directly verify both sides.

## Stop and handoff
- Record `unknown` when visual and nearby text disagree; do not rely on appearance alone.
- Stop completion when IDs are not written back or source pointers are missing; hand unresolved items to the human reviewer.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: pptx_spec_traceability

## Purpose

Convert presentation-based specifications into Markdown artifacts with stable traceability IDs, preserve the source pointer down to slide and object position, and write those IDs back into the PowerPoint deck so humans can verify omissions directly in the original presentation.

## Required References (XID)

- [Sources (PDF/Excel/Web): ingestion and referencing](../../docs/reference/020_sources.md#xid-2FAD591BF725)

## Inputs

- source pptx path
- optional target Markdown destination
- optional slide scope
- optional traceability ID prefix

## Outputs

- Markdown specification fragments
- source pointer records for each extracted fragment
- slide-item descriptions derived from images, shapes, and callouts
- traceability ID map
- updated pptx with written-back traceability IDs
- unresolved list

## Startup

- Confirm that the source deck is stored under `sources/` or that the deck copy being edited is the controlled source of truth.
- Confirm how traceability IDs should be prefixed and grouped.
- Confirm whether IDs should be written into speaker notes, dedicated traceability text boxes, adjacent callouts, comments, or a separate controlled slide when the existing slide layout has no safe free area.

## Planning

- Map each slide into extraction units:
  - title and section headers
  - text boxes and tables
  - images, shapes, arrows, annotations, and callouts
  - speaker notes when they explain visible content
  - nearby labels and grouped objects
- Decide the target Markdown split so each fragment remains reviewable and can keep a narrow source pointer.
- Define how object-derived items will be connected to nearby text:
  - same grouped object set
  - nearest caption or label
  - same slide region or callout chain
  - speaker notes when they explicitly explain the visible object
- Prepare management rows for extraction units, visual interpretation, ID assignment, deck write-back, and unresolved ambiguities.

## Execution

- Read the deck slide by slide and preserve the original location for every extracted item.
- For images, shapes, and callouts:
  - identify the slide number and object position
  - inspect nearby labels, captions, connector arrows, grouped objects, and notes
  - connect the visual object to the nearest explanatory text that describes the same screen, step, or rule
- Extract slide items that appear only in visuals and record them explicitly in Markdown.
- Assign a stable traceability ID to each requirement, rule, screen item, flow step, and visual-only item.
- Write Markdown fragments that include source pointers such as deck path, slide number, object label, and placement notes.
- Write the assigned traceability IDs back into the deck so the original presentation can be reviewed directly without full side-by-side comparison against Markdown.

## Monitoring and Control

- If nearby text and the visual object imply different meanings, record the item as `unknown` and keep both interpretations visible.
- Do not rely on slide appearance alone when labels, callouts, or speaker notes give a stronger interpretation.
- Keep visual-derived items linked to both:
  - the object position on the slide
  - the surrounding textual basis
- Keep IDs stable across reruns unless the semantic unit itself changed.

## Closure

- Verify that every Markdown fragment has a source pointer back to the deck.
- Verify that every written-back ID in the deck matches the corresponding Markdown item.
- Finalize rows as `done`, `unknown`, or `out_of_scope`.
- Preserve unresolved items where the slide layout or visual context is too weak for safe interpretation.

## Rules

- Do not treat deck extraction as complete unless the IDs are written back into the deck.
- Do not separate visual-derived specification items from their slide position and nearby textual basis.
- Do not collapse multiple controls, steps, or labels into one Markdown item if the slide shows them as separate units.
- Prefer direct deck verification over Markdown-only reconciliation when checking omissions.

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

- summary: extract presentation specifications into Markdown, assign traceability IDs, connect slide images and shapes to nearby explanatory text, and write the IDs back into the deck

- use_when: user needs to convert PowerPoint-based specifications into Markdown artifacts while preserving slide-level traceability and reducing review burden in the original deck

- input: source pptx path, optional target Markdown destination, optional slide scope, optional traceability ID prefix

- output: Markdown specification fragments, slide-item descriptions, traceability ID map, updated pptx with written-back IDs, unresolved list

- constraints: keep slide number and object position explicit; do not separate image-derived or shape-derived items from the slide text that gives them meaning; write IDs back into the original deck or the controlled deck copy used as the source of truth

- lifecycle:
  - startup: confirm source deck path, slide scope, and ID policy
  - planning: map slides, text boxes, shapes, images, notes, and callouts into extraction units
  - execution: extract specification content, connect object position to nearby explanatory text, create Markdown fragments, assign IDs, and write the IDs back to the deck
  - monitoring_and_control: record ambiguity when object meaning and nearby text disagree
  - closure: finalize Markdown outputs, verify deck write-back, and preserve source pointers

- tags: `pptx`, `powerpoint`, `presentation`, `specification`, `traceability`, `image`, `import`

- knowledge_slots:
  - name=sources; bind=2FAD591BF725
