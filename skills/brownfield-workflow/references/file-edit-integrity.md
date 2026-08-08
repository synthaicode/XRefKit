<!-- xid: B4F1C8D2A603 -->
<a id="xid-B4F1C8D2A603"></a>

# Brownfield file-edit integrity

Before editing an existing text file, record encoding, identification basis,
BOM bytes, newline convention, original bytes or hash, and strict-decoded
Unicode. Preserve the policy and verify strict decode/re-encode after writing.

Immediately before writing, compare the current raw bytes with the pre-edit
revision token. If they differ, abort without writing and classify the item as
`unknown` or `blocked`; never overwrite concurrent edits.

Record a semantic edit contract containing requested outcome, authoritative
source or decision owner, intended changes, protected invariants, out-of-scope
text, and acceptance checks. Confirm semantic alignment before writing; valid
syntax or a passing narrow test does not authorize an unsupported edit.

When alignment conflicts remain, inspect a bounded history window including
uncommitted state. Record the likely source of the conflict, but do not treat
the newest commit as authority.

Classify uncommitted state as `pre_existing_human_or_unknown`,
`ai_owned_current_work`, `non_overlapping_changes`, or `mixed_or_overlapping`.
Do not reset, checkout, clean, stash, or hide it without authorization.

For new files, inspect same-extension peers by coherent scope, select the local
representative majority, record confidence and deviations, and stop on weak or
conflicting conventions or unknown registration.
