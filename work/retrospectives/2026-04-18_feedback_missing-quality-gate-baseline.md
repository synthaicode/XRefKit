# Structural Feedback Record

- feedback_id: `FB-PLAN-001`
- triggered_from: `closure_workflow`
- observed_defect_pattern: the repository defined quality expectations but did not yet enforce them consistently for `fm` and bundled executable projects
- affected_owner_group: `Planning Group`
- suspected_root_workflow: `planning_workflow`
- suspected_failed_lifecycle_layer: `Planning`
- severity: `medium`
- evidence:
  - CI only executed `python -m fm xref check`
  - `fm` had no unit tests before the quality-gate strengthening work
  - bundled `projects/*` applications did not share a single documented quality baseline
- immediate_containment_action:
  - add `fm` unit tests
  - expand CI to include `fm` tests, skill metadata checks, and project-level checks
- upstream_corrective_action:
  - define a reusable project quality baseline
  - align local and CI execution behind one quality-gate runner
  - require future executable projects under `projects/` to expose `scripts.check`
- next_responsible_group: `Planning Group`
- or_improvement_id_and_execution_owner: `OR-QG-001 / Engineering owner`
- approval_owner: `Human decision layer`
- first_seen: `2026-04-18`
- last_updated: `2026-04-18`
- recovery_condition:
  - repository quality gate covers `fm` contract checks and baseline checks for bundled executable projects
- re_observation_condition:
  - observe at least one further project addition or quality-gate change without recurrence of undocumented or uncheckable project entry points
- human_approval_required: `no`

## Diagnosis

The repository already described strong quality-management rules, but the executable enforcement path lagged behind the policy model.

This made it too easy for bundled tools or apps to exist without a stable validation entry point and made `fm` itself under-protected despite being a control-plane dependency.

## Containment Result

The following corrective work has been applied:

- `fm` unit tests and CLI contract tests were added
- CI now runs `fm` checks and project checks through a shared quality-gate runner
- bundled Node projects now have a documented and machine-checked baseline

## Remaining Risk

The baseline currently checks structural readiness, not full behavior coverage.

Future projects can still pass the baseline with shallow checks unless their `scripts.check` is kept meaningful through review.
