---
schema_version: 1
skill_id: doc_ship
xid: B4E8A1C7D260
summary: apply approved promotion candidates from work into canonical repository assets with traceable pointers
applies_when:
- retro` or an equivalent review has identified stable promotion candidates and the user wants those candidates reflected in `docs/`, `knowledge/`, `skills/`, or `agent/
exclusions:
- do not ship unstable notes
- duplicate canonical content
- or mix procedure and domain fact into the wrong destination
inputs:
- approved promotion report, related `work/` records, target canonical files or target classes, optional user wording constraints
outputs:
- updated canonical files, `work/` pointer updates, unresolved or skipped candidate list, xref validation result
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
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: skill_authoring_with_xref
  query: skill authoring with Xref
  required_when: Required when promoting reusable Skill procedures
  seed_xids:
  - 3DB05A0F5F5B
- id: working_area_policy
  query: working area policy
  required_when: Required when reading or updating work records
  seed_xids:
  - 111D282CA0EA
- id: shared_memory_operations
  query: shared memory operations
  required_when: Required when promotion affects shared memory records
  seed_xids:
  - 4A423E72D2ED
control_refs:
- 111D282CA0EA
aliases:
- E4B61C9027AF
- 9F38C7A15D4E
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

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: doc_ship

## Purpose

Take approved promotion candidates from `work/` and apply them to canonical repository assets with explicit traceability.

## Required Knowledge (XID)

- [Skill authoring with Xref](../../../docs/guides/013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Working area policy](../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)
- [Shared memory operations](../../../docs/core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED)

## Inputs

- approved promotion candidate report
- relevant `work/sessions/` or `work/retrospectives/` files
- target canonical files or target classes
- optional user wording or structure constraints

## Outputs

- updated canonical files in exactly one target area per item:
  - `docs/`
  - `knowledge/`
  - `skills/` or `skills_private/`
  - `agent/`
- updated `work/` record with a short moved-to pointer
- skipped item list with reasons
- xref validation result

## Startup

- Confirm the promotion candidates are approved for shipping.
- Confirm the source `work/` records exist.
- Confirm the intended canonical destination for each item.
- Load the authoring and working-area rules before editing.

## Planning

- For each approved item, choose exactly one destination class:
  - `docs/` for stable operational or design policy
  - `knowledge/` for stable domain facts or reusable review knowledge
  - `skills/` or `skills_private/` for reusable procedures
  - `agent/` for stable contract, routing, or role definitions
- Select the smallest existing target file that can absorb the change cleanly.
- If no suitable managed file exists, create a new target file in the correct area.
- Prepare a skipped list for any item that is still unstable, duplicate, or insufficiently evidenced.

## Execution

- Read the destination files before editing them.
- Apply the approved content to the selected canonical files.
- Keep procedure content in skills and factual content in knowledge.
- When new managed files are added, assign XIDs.
- Update the source `work/` record with a short pointer that states:
  - moved-to path
  - moved date
  - whether the item was fully or partially shipped

## Monitoring and Control

- Verify the same content was not already recorded canonically.
- Verify each shipped item has exactly one primary destination.
- Downgrade any candidate to skipped if the wording is still unstable or the evidence is too weak.
- Confirm no new XID-managed link is missing `#xid-...`.

## Closure

- Run `python -m xrefkit xref init` when new managed files were added.
- Run `python -m xrefkit xref fix`.
- Report:
  - applied items
  - skipped items
  - target files changed
  - validation result

## Rules

- Never treat `work/` as canonical source of truth.
- Never ship an unapproved candidate as canonical content.
- Never duplicate the same stable rule across multiple canonical areas without a clear boundary.
- Prefer updating an existing canonical file over creating a new fragment when the concept already has a natural home.
- Keep the moved-to pointer short and factual.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: apply approved promotion candidates from `work/` into canonical repository assets and leave traceable moved-to pointers

- use_when: `retro` or an equivalent review has identified stable promotion candidates and the user wants those candidates reflected in `docs/`, `knowledge/`, `skills/`, or `agent/`

- input: approved promotion report, related `work/` records, target canonical files or target classes, optional user wording constraints

- output: updated canonical files, `work/` pointer updates, unresolved or skipped candidate list, xref validation result

- constraints: do not ship unstable notes; do not duplicate existing canonical content; do not mix procedure and domain fact into the wrong destination

- lifecycle:
  - startup: confirm approved candidates, evidence records, and canonical targets
  - planning: map each approved item to exactly one canonical destination and update scope
  - execution: update canonical files, add new managed files when needed, and update the source `work/` pointer
  - monitoring_and_control: verify duplication, missing XIDs, and destination mismatch before completion
  - closure: run xref maintenance, summarize applied and skipped items, and preserve traceability

- tags: `documentation`, `promotion`, `knowledge-ops`

- knowledge_slots:
  - name=skill_authoring_with_xref; bind=3DB05A0F5F5B
  - name=working_area_policy; bind=111D282CA0EA
  - name=shared_memory_operations; bind=4A423E72D2ED
