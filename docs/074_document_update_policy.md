<!-- xid: B1D42A6F90C3 -->
<a id="xid-B1D42A6F90C3"></a>

# Document Update Policy

This policy applies to repository documentation, knowledge pages, Skill-facing
instructions, capability definitions, workflow definitions, and agent startup or
routing documents.

## Rule

Target documents must describe the current authoritative state only.

Do not keep obsolete alternatives, superseded wording, migration notes, or
decision history in the same file merely to preserve context. Historical context
belongs in a separate record.

Use:

- ADRs for accepted architecture or policy decisions
- `work/sessions/` for factual execution history
- `work/judgments/` for non-trivial reasoning history
- `work/retrospectives/` for structural feedback and corrective context
- canonical register pages in `docs/` for current open/closed state

## Update Procedure

When updating a target document:

1. Replace outdated content with the latest authoritative content.
2. Move decision history or rationale that must be retained into a separate ADR
   or work record.
3. Link to the separate record only when the current reader needs traceability.
4. Keep the target document readable as the latest-state source without requiring
   the reader to resolve old-versus-new wording.

## Stop Condition

If the correct historical destination is unclear, do not store the history in the
target document as a workaround. Mark the destination as missing and propose
whether it belongs in an ADR, work record, canonical register, Skill, knowledge
page, or workflow definition.

## Related

- [ADR 0002](adr/0002-document-update-current-state-only.md#xid-A64F73C7D8B1)
- [Work record types](019_work_record_types.md#xid-4F8C21B7D4A2)
- [Page naming conventions](023_page_naming_conventions.md#xid-7B2D4E6A1C90)
