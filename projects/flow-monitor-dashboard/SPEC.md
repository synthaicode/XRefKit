# Flow Monitor Dashboard Spec

This page defines the alignment policy and event contract for `projects/flow-monitor-dashboard`.

## Position

The flow monitor contract is a monitor-side specification.

This dashboard is the human-facing viewer for AI behavior logs and related Flow
evidence.
Reorganization of the repository or AI agent OS layers must not silently break
that viewing function.

It should not be treated as shared domain knowledge in `knowledge/`.

Reason:

- it is owned by the monitoring tool
- it exists to support dashboard ingestion and visualization
- it may evolve with monitor implementation details without changing business-domain knowledge

## Problem Summary

The repository currently has three separate representations:

- Flow definitions in `flows/*.yaml`
- Skill outputs in `skills/*/meta.md`
- monitoring events consumed by `projects/flow-monitor-dashboard`

These layers are only partially connected.

Current mismatch points:

- the dashboard reads event files under `projects/` in JSONL / JSON form
- the dashboard expects `step`, `decision`, `checklist`, and `path` events
- Skill metadata mostly defines artifact outputs, not monitoring-event outputs
- `flow-log-presets.json` is maintained manually and is not derived from Flow / Skill definitions

## Goal

Define one canonical monitoring-event schema for the monitor and make the following layers refer to it explicitly:

- dashboard ingestion
- Flow logging recommendations
- project-side monitoring traces written under `projects/`

The dashboard must continue to let a human inspect:

- Flow run progression
- observed steps, decisions, checklists, and paths
- Skill runtime log status such as execution, check, concerns, closure, and handoff

Skill metadata should remain artifact-oriented.

## Canonical Monitoring Event Schema

The canonical event schema for the monitor is the JSONL / JSON event model already consumed by this dashboard.

Required shared fields:

| Field | Meaning |
|------|------|
| `timestamp` | event time in ISO 8601 |
| `project` | project identifier under `projects/` |
| `flow_name` | Flow name such as `manufacturing_workflow` |
| `run_id` | execution unit identifier for one Flow run |
| `type` | `step`, `decision`, `checklist`, or `path` |

Type-specific fields:

| Type | Required fields |
|------|------|
| `step` | `step`, optional `status` |
| `decision` | `decision`, `decision_result` |
| `checklist` | `checklist`, `checklist_used`, optional `completed_items`, optional `total_items` |
| `path` | `path`, optional `status` |

Optional shared fields:

- `notes`
- `source_file`
- `flow_id`
- `execution_id`

## Placement Rule

Recommended placement:

```text
projects/<project>/flows/<flow_name>/monitoring/flow-events.jsonl
```

Allowed collected filenames remain:

- `flow-events.jsonl`
- `trace.jsonl`
- `events.jsonl`
- `flow-monitor.json`
- `flow-monitoring.json`

## Ownership Boundaries

- monitor event schema:
  - `projects/flow-monitor-dashboard/SPEC.md`
- dashboard parser and visualization:
  - `projects/flow-monitor-dashboard/*`
- per-Flow monitoring recommendation:
  - `flows/*.yaml`
- Skill artifact outputs:
  - `skills/*/meta.md`

This keeps the contract boundaries clear:

- monitor owns monitor schema
- Flow owns recommended observability points
- Skill owns work results

## Alignment Policy

### 1. Keep Skill outputs and monitoring events separate

Skill `output` fields must continue to describe artifact outputs such as:

- `unit_test_results`
- `self_check_result`
- `quality_gate_result`

They should not be redefined as monitor event logs.

### 2. Derive monitor recommendations from the deterministic flow schema

`flows/*.yaml` now uses the deterministic-control schema (`docs/018`,
`docs/073`): a `steps:` mapping plus per-step `on`/`handback` transitions and a
`handoff.escalation` list. The monitor derives recommendations directly from
this schema instead of a separate `monitoring:` block:

- step sequence: keys of the `steps:` mapping (legacy `sequence:` is read only
  for any not-yet-migrated flow)
- recommended paths: `handoff.escalation` entries (legacy `monitoring.paths`
  is still merged when present)

```yaml
steps:
  implementation:
    ...
handoff:
  escalation:
    - out_of_scope_to_coordinator
    - quality_feedback_tradeoff_or_scope_conflict_to_coordinator
```

The schema is the canonical source for steps and paths.

### 3. Treat `flow-log-presets.json` as the source for decisions and checklists

The deterministic schema does not model domain decision or checklist labels, so
`flow-log-presets.json` is retained as the curated source for those two kinds.
It is no longer the source of truth for steps or paths (those come from the
schema), and it remains the fallback for paths only when a flow defines no
escalation.

### 3a. Dashboard display should prefer observed keys

When a Flow already has monitoring traces, the dashboard display should prefer observed `decision`, `checklist`, and `path` keys from those traces.

Display priority:

1. observed keys from project monitoring traces
2. flow YAML schema (`steps:` for steps, `handoff.escalation` for paths)
3. `flow-log-presets.json` (source for decisions and checklists; path fallback)

For Skill runtime logs, the dashboard should also surface the observed output
structure that humans need for review:

- output artifacts
- evidence artifacts
- handoff artifacts
- unknown / risk / judgment concerns

### 4. Allow optional Skill-side guidance only when needed

If a Skill needs to mention monitoring explicitly, it should only say that when monitor traces are written for execution evidence, they must follow this monitor-side spec.

It should not redefine its own `output` contract.

## Migration Plan

### Phase 1

Adopt this file as the canonical monitor-side event specification.

### Phase 2

Flow YAML adopted the deterministic-control schema (`steps:` mapping and
`handoff.escalation`) instead of a separate `monitoring:` block.

### Phase 3

Update `server.js` to read the step sequence from `steps:` and recommended
paths from `handoff.escalation`, keeping `flow-log-presets.json` as the source
for decisions and checklists (and the fallback for paths).

### Phase 4

Update sample logs under `projects/*/flows/*/monitoring/` to conform exactly to this spec and Flow monitoring definitions.

## Acceptance Criteria

Alignment is complete when all of the following are true:

- the monitor event schema is defined in this monitor-side spec
- dashboard step and path recommendations are derived from the Flow YAML schema, with `flow-log-presets.json` owning only decisions and checklists
- Skill `output` fields remain artifact-oriented
- project monitoring traces under `projects/*/flows/*/monitoring/` conform to this spec
- the dashboard still detects at least one project-side Flow run and at least one Skill runtime log from repository data during local checks
