<!-- xid: A64F73C7D8B1 -->
<a id="xid-A64F73C7D8B1"></a>

# ADR 0002: Keep target documents current-state only

- Status: Accepted
- Date: 2026-06-26

## Context

When historical information, superseded options, and current rules remain in the
same document, AI agents can treat stale text as still authoritative. This causes
routing errors, duplicated concepts, and uncertainty about which rule is the
latest one.

The repository already separates operational history, judgments, retrospectives,
and ADRs from canonical documentation. That separation should be explicit for all
documentation updates.

## Decision

Target documents must contain only the latest authoritative information.

Decision history and rationale must be stored in separate files. Architecture and
policy decisions use ADRs. Execution history, reasoning history, and structural
feedback use the existing `work/` record types.

The current operational rule is documented in
[Document Update Policy](../074_document_update_policy.md#xid-B1D42A6F90C3).

## Consequences

- Readers and agents can treat target files as the current source of truth.
- Historical context remains available, but it does not compete with current
  rules inside the same file.
- Updates that need traceability must create or update the appropriate separate
  record instead of appending history to the target document.

## Alternatives considered

- **Keep history inline with labels such as "old" or "superseded"**: rejected
  because AI agents may still retrieve and act on stale nearby text.
- **Remove history entirely**: rejected because accepted decisions and useful
  operational evidence still need traceable homes.
