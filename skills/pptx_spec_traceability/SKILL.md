<!-- xid: 4C8E2B1F6A20 -->
<a id="xid-4C8E2B1F6A20"></a>

# Skill: pptx_spec_traceability

## Purpose

Convert presentation-based specifications into Markdown artifacts with stable traceability IDs, preserve the source pointer down to slide and object position, and write those IDs back into the PowerPoint deck so humans can verify omissions directly in the original presentation.

## Required References (XID)

- [Sources (PDF/Excel/Web): ingestion and referencing](../../docs/020_sources.md#xid-2FAD591BF725)

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
