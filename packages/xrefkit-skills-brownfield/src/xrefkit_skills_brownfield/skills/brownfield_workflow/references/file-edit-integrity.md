<!-- xid: B4F1C8D2A613 -->
<a id="xid-B4F1C8D2A613"></a>

# Brownfield file-edit integrity

Record original encoding, BOM, newline convention, bytes/hash, and strict
decoded Unicode before editing. Preserve them and verify strict decode/re-encode
after saving. Compare current bytes with the pre-edit revision immediately
before writing; abort on concurrent changes.

Record semantic alignment, authoritative source, protected invariants, and
acceptance checks before writing. Investigate unresolved conflicts in a bounded
history window without treating the newest commit as authority. Preserve and
classify uncommitted state. For new files, inspect same-extension peers and
stop on weak or conflicting conventions or unknown registration.
