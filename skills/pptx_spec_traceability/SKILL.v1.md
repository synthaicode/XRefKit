---
schema_version: 1
skill_id: pptx_spec_traceability
xid: A6D3F8B1C520
aliases: [4C8E2B1F6A20, 7F4C1A2D9E60]
summary: extract PowerPoint specifications into traceable Markdown and write IDs back into the deck
applies_when: [user needs slide-level specification extraction with source traceability]
exclusions: [do not separate visual items from their slide context or treat Markdown-only reconciliation as complete]
inputs: [source pptx path, optional Markdown destination, slide scope, traceability ID prefix]
outputs: [Markdown fragments, source pointers, slide-item descriptions, ID map, updated deck, unresolved list]
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
knowledge_needs:
  - id: sources
    query: sources PDF Excel Web ingestion and referencing
    required_when: Required for source-pointer and evidence handling
    seed_xids: [2FAD591BF725]
control_refs: []
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
