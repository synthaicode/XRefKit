<!-- xid: E4B61C9027AF -->
<a id="xid-E4B61C9027AF"></a>

# Skill: doc_ship

## Purpose

Take approved promotion candidates from `work/` and apply them to canonical repository assets with explicit traceability.

## Required Knowledge (XID)

- [Skill authoring with Xref](../../docs/013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Working area policy](../../docs/014_working_area_policy.md#xid-111D282CA0EA)
- [Shared memory operations](../../docs/015_shared_memory_operations.md#xid-4A423E72D2ED)

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

- Run `python -m fm xref init` when new managed files were added.
- Run `python -m fm xref fix`.
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
