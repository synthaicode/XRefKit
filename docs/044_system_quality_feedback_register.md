<!-- xid: 8B31F02A4013 -->
<a id="xid-8B31F02A4013"></a>

# System Quality Feedback Register

This page defines where structural quality feedback is stored and how it is referenced in later cycles.

This page defines the canonical register only.
For the overall structural feedback process, see [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012).
For the broader split across record types, see [Work record types](019_work_record_types.md#xid-4F8C21B7D4A2).

## Purpose

Make system-level quality feedback reloadable for the next Planning Group cycle instead of leaving it as isolated event history.

## Storage Split

Structural quality feedback is stored in two layers:

1. detailed feedback record:
   - location: `work/retrospectives/`
   - purpose: preserve the full event, diagnosis, and immediate correction context
2. canonical feedback register:
   - location: this page in `docs/`
   - purpose: give later cycles a stable place to find open and important structural issues

## Detailed Feedback Record

Use `work/retrospectives/` for the full feedback record.

Filename rule:

- `YYYY-MM-DD_feedback_<topic>.md`

Example:

- `2026-03-17_feedback_repeated-closure-leak-on-target-tracking.md`

The detailed record should contain:

- triggering workflow
- observed defect pattern
- affected owner group
- suspected root workflow
- suspected failed lifecycle layer
- evidence
- immediate containment action
- upstream corrective action
- next responsible group
- human approval need

## Canonical Feedback Register

This page is the stable entry point for later workflow cycles.

Each structural issue that remains relevant beyond a single session should be summarized here as one row.

## Register Columns

| Column | Meaning |
|------|------|
| `feedback_id` | stable local identifier for the structural issue |
| `status` | `open`, `in_progress`, `closed`, or `watch` |
| `triggered_from` | workflow where the issue was detected |
| `root_workflow` | workflow suspected to need upstream correction |
| `failed_layer` | Startup, Planning, Execution, Monitoring and Control, or Closure |
| `owner_group` | group expected to drive correction |
| `summary` | short description of the structural issue |
| `latest_record` | path to the latest detailed feedback record in `work/retrospectives/` |
| `next_action` | next required corrective action |

## Register

| feedback_id | status | triggered_from | root_workflow | failed_layer | owner_group | summary | latest_record | next_action |
|------|------|------|------|------|------|------|------|------|
| `none_yet` | `watch` | - | - | - | - | no structural feedback has been promoted yet | - | add first record when a recurring or upstream issue is identified |

## Read Path For Later Cycles

When Planning Group starts a new cycle, read in this order:

1. this register
2. any `open` or `in_progress` feedback rows
3. the linked detailed record in `work/retrospectives/`
4. the affected workflow pages by XID

## Write Path

When CAB or Closure emits structural feedback:

1. write the detailed record to `work/retrospectives/`
2. add or update the corresponding row in this register
3. update the affected workflow or policy document if the corrective rule becomes stable

## Ownership Rule

- Quality Group detects and writes the structural feedback trigger.
- Planning Group must consult this register before prioritizing a new cycle.
- Coordinator does not own the register; Coordinator only routes reassignment when needed.

## Related

- [Work record types](019_work_record_types.md#xid-4F8C21B7D4A2)
- [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012)
- [Working area policy](014_working_area_policy.md#xid-111D282CA0EA)
- [Shared memory operations](015_shared_memory_operations.md#xid-4A423E72D2ED)
