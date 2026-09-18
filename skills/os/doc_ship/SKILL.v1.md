---
schema_version: 1
skill_id: doc_ship
xid: B4E8A1C7D260
aliases: [E4B61C9027AF, 9F38C7A15D4E]
summary: apply approved promotion candidates from work into canonical repository assets with traceable pointers
applies_when: [retro or equivalent review identified stable promotion candidates and the user wants canonical updates]
exclusions: [do not ship unstable notes, duplicate canonical content, or mix procedure and domain fact into the wrong destination]
inputs: [approved promotion report, work records, target canonical files or classes, optional wording constraints]
outputs: [updated canonical files, work pointers, skipped candidates with reasons, xref validation result]
criteria:
  - id: approval
    statement: Every shipped candidate is approved and supported by a work evidence record.
    verification: Check approval and source evidence before editing.
  - id: destination
    statement: Each shipped item has exactly one canonical destination class.
    verification: Inspect the destination mapping and duplication check.
  - id: traceability
    statement: Work pointers, XIDs, and xref validation preserve shipping traceability.
    verification: Run xref maintenance and inspect moved-to pointers.
knowledge_needs:
  - id: skill_authoring_with_xref
    query: skill authoring with Xref
    required_when: Required when promoting reusable Skill procedures
    seed_xids: [3DB05A0F5F5B]
  - id: working_area_policy
    query: working area policy
    required_when: Required when reading or updating work records
    seed_xids: [111D282CA0EA]
  - id: shared_memory_operations
    query: shared memory operations
    required_when: Required when promotion affects shared memory records
    seed_xids: [4A423E72D2ED]
control_refs: [111D282CA0EA]
---
<!-- xid: B4E8A1C7D260 -->
<a id="xid-B4E8A1C7D260"></a>

# Skill: doc_ship

## Purpose
Apply approved promotion candidates from `work/` to canonical assets with explicit traceability.

## Method
1. Confirm approved candidates, evidence records, source work files, and target destinations.
2. Resolve the authoring, working-area, and shared-memory Knowledge needs as applicable.
3. Map each item to exactly one destination class and skip unstable, duplicate, or insufficiently evidenced items.
4. Read destination files, apply approved content, and update the source work pointer with path, date, and full or partial status.
5. Run xref maintenance and report applied, skipped, changed files, and validation.

## Stop and handoff
- Never ship unapproved or unstable candidates; preserve skipped reasons.
- Hand unresolved destination or approval decisions to the human owner.
