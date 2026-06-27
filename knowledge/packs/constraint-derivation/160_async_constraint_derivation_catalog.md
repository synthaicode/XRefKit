<!-- xid: 72ECA94D1B35 -->
<a id="xid-72ECA94D1B35"></a>

# Async Constraint Derivation Catalog

## Derivation Areas

| Design element | Confirm as requirement | Decision class |
|---|---|---|
| queue processing | requeue policy, retry limit, duplicate-run handling | requirement |
| retry exhaustion | dead-letter, discard, or notify behavior | requirement |
| queue lag | alert threshold and handling | requirement |
| async job | cancellation behavior and result-notification method | requirement |
| batch | partial-failure behavior and rerun idempotency | requirement |
| batch rerun | restart unit such as full rerun vs failed segment only | requirement |
| zero-target batch | success vs warning behavior | requirement |
| execution log | audit retention and observability needs | requirement |
| large batch | chunk size or memory-limit handling | design |
| schedule | overlapping runs, skipped-run recovery, failure notification | requirement |
| manual plus scheduled run | duplicate-start behavior | requirement |
| date-bound batch | timezone, month-end, and leap-year behavior | requirement |
| job-state model | complete state-transition coverage and stuck-running recovery | requirement |
| result retention | retention period and cleanup timing | requirement |
| progress reporting | timing and granularity of progress notifications | requirement |

## Matrix Guidance

- Expand a rerun matrix whenever partially completed work can be retried.
- Keep already-completed and not-yet-run segments separate in rerun analysis.

## Output Shape

- derivation basis table with `ACD-` ids
- grouped confirmation items by processing unit
- explicit rerun or restart matrix when required

## Knowledge Relations

- part_of: [Constraint Derivation Framework](110_constraint_derivation_framework.md#xid-81A6C4E2B190)
