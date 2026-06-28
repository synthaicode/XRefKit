<!-- xid: 6F0D7C1A2E44 -->
<a id="xid-6F0D7C1A2E44"></a>

# Integration Constraint Derivation Catalog

## Derivation Areas

| Design element | Confirm as requirement | Decision class |
|---|---|---|
| API call | timeout value, retry policy, idempotency, circuit breaker | requirement |
| synchronous API | user-visible behavior on timeout or failure | requirement |
| asynchronous API | completion-check method | requirement |
| paged API | behavior on partial page-fetch failure | requirement |
| authenticated API | token refresh and expired-token behavior | requirement |
| webhook | duplicate delivery, ordering inversion, missing-event detection | requirement |
| webhook signature | behavior on signature validation failure | requirement |
| webhook failure response | whether to return success upstream on internal failure | requirement |
| file intake | encoding, newline, empty-file, broken-file behavior | requirement |
| CSV or TSV | row-width mismatch and partial-import failure behavior | requirement |
| file send | resend unit and duplicate-send behavior | requirement |
| messaging send | retry, dead-letter, and send-failure behavior | requirement |
| messaging receive | requeue policy, ordering guarantee, duplicate-delivery handling | requirement |
| event send | behavior when the receiver is unavailable | requirement |
| external payment or notification service | status reconciliation, duplicate prevention, delivery confirmation | requirement |

## Matrix Guidance

- Expand an idempotency matrix whenever retry or duplicate delivery is possible.
- Keep retry-success and retry-after-success cases distinct.

## Output Shape

- derivation basis table with `ICD-` ids
- grouped confirmation items by integration surface
- explicit retry or idempotency matrix when required

## Knowledge Relations

- part_of: [Constraint Derivation Framework](110_constraint_derivation_framework.md#xid-81A6C4E2B190)
