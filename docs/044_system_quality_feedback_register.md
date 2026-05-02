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

- feedback ID
- triggering workflow
- observed defect pattern
- affected owner group
- suspected root workflow
- suspected failed lifecycle layer
- severity:
  - `critical`
  - `high`
  - `medium`
  - `low`
- evidence
- immediate containment action
- upstream corrective action
- next responsible group
- approval owner
- first seen date
- last updated date
- human approval need

## Feedback ID Rule

Use a stable but lightly structured identifier so the issue can be referenced consistently across discussion, reviews, and related documents.

Preferred format:

- `FB-001`
- `FB-REQ-001`
- `FB-PLAN-002`

Rules:

- keep the `FB-` prefix
- optionally insert a short workflow code such as `REQ`, `PLAN`, `CAB`, or `CLOSE`
- keep the numeric suffix zero-padded within the local series
- do not rename an existing ID after it has been referenced by other records

## Canonical Feedback Register

This page is the stable entry point for later workflow cycles.

Each structural issue that remains relevant beyond a single session should be summarized here as one row.

## Register Columns

| Column | Meaning |
|------|------|
| `feedback_id` | stable identifier for the structural issue using the `FB-...` rule |
| `status` | `open`, `in_progress`, `closed`, or `watch` |
| `severity` | `critical`, `high`, `medium`, or `low` to stabilize Planning Group pickup order |
| `triggered_from` | workflow where the issue was detected |
| `root_workflow` | workflow suspected to need upstream correction |
| `failed_layer` | Startup, Planning, Execution, Monitoring and Control, or Closure |
| `owner_group` | group expected to drive correction |
| `approval_owner` | role or group that must approve the structural corrective direction when approval is needed |
| `first_seen` | date when the structural issue was first recognized as a register candidate |
| `last_updated` | date when the row or linked detailed record was last materially updated |
| `summary` | short description of the structural issue |
| `latest_record` | path to the latest detailed feedback record in `work/retrospectives/` |
| `next_action` | next required corrective action |

## Register

| feedback_id | status | severity | triggered_from | root_workflow | failed_layer | owner_group | approval_owner | first_seen | last_updated | summary | latest_record | next_action |
|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `FB-PLAN-001` | `in_progress` | `medium` | `closure_workflow` | `planning_workflow` | `Planning` | `Planning Group` | `Human decision layer` | `2026-04-18` | `2026-04-18` | repository quality expectations were not yet enforced consistently across `fm` and bundled executable projects | `work/retrospectives/2026-04-18_feedback_missing-quality-gate-baseline.md` | re-observe the next bundled project or quality-gate change and confirm the baseline remains explicit and enforced |
| `FB-MKT-001` | `open` | `high` | `marketing_video_production_review` | `marketing_video_production_workflow` | `Monitoring and Control` | `Marketing Group` | `Human decision layer` | `2026-04-30` | `2026-04-30` | the Marketing Group video-production function has broad written scope, but package defaults, QA enforcement, and output capability are inconsistent | `work/retrospectives/2026-04-30_feedback_marketing-video-production-gaps.md` | define a canonical production contract and add machine-checkable QA for marketing video packages |

## Pickup Order

When multiple rows are active at once, Planning Group should triage in this order:

1. `open` rows before `in_progress` rows unless an `in_progress` row blocks current delivery
2. within the same status, higher `severity` first:
   - `critical`
   - `high`
   - `medium`
   - `low`
3. within the same severity, older `first_seen` first unless there is a clear business reason to override
4. use `last_updated` to detect stale issues that need explicit review or closure pressure

## Status Closure Rule

Do not mark a structural issue as `closed` only because one corrective change was merged.

Mark a row as `closed` only when all of the following are true:

1. corrective action has been implemented
2. the defined recovery condition has been satisfied
3. the defined re-observation period has completed with no recurrence

If corrective action is implemented but recovery or re-observation is still pending, keep the row as `in_progress`.

## Read Path For Later Cycles

When Planning Group starts a new cycle, read in this order:

1. this register
2. any `open` or `in_progress` feedback rows, ordered by `severity`, `first_seen`, and `last_updated`
3. the linked detailed record in `work/retrospectives/`
4. the affected workflow pages by XID

## Write Path

When CAB or Closure emits structural feedback:

1. write the detailed record to `work/retrospectives/`
2. add or update the corresponding row in this register, including `severity`, `approval_owner`, `first_seen`, and `last_updated`
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
