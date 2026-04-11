# Flow Monitor Dashboard Spec

This page defines the alignment policy and event contract for `projects/flow-monitor-dashboard`.

## Position

The flow monitor contract is a monitor-side specification.

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

### 2. Move recommended monitor events into Flow YAML

Each `flows/*.yaml` should gain a section such as:

```yaml
monitoring:
  decisions:
    - implementation_boundary_review
    - assumption_gap_recording
  checklists:
    - manufacturing_self_check
  paths:
    - handoff_to_quality_review
    - out_of_scope_to_coordinator
```

This should become the canonical source for monitor recommendations.

### 3. Treat `flow-log-presets.json` as migration-only

`flow-log-presets.json` should be one of the following:

- removed after migration, or
- retained temporarily only while Flow YAML files are being updated

It should not remain the long-term source of truth.

### 3a. Dashboard display should prefer observed keys

When a Flow already has monitoring traces, the dashboard display should prefer observed `decision`, `checklist`, and `path` keys from those traces.

Display priority:

1. observed keys from project monitoring traces
2. `flows/*.yaml` `monitoring:` definition
3. `flow-log-presets.json` fallback during migration

### 4. Allow optional Skill-side guidance only when needed

If a Skill needs to mention monitoring explicitly, it should only say that when monitor traces are written for execution evidence, they must follow this monitor-side spec.

It should not redefine its own `output` contract.

## Migration Plan

### Phase 1

Adopt this file as the canonical monitor-side event specification.

### Phase 2

Add `monitoring:` sections to Flow YAML files and mirror current preset values there.

### Phase 3

Update `server.js` to read recommended decisions / checklists / paths from `flows/*.yaml`.

During migration, `flow-log-presets.json` may remain as fallback only when a Flow file does not yet define `monitoring:`.

### Phase 4

Update sample logs under `projects/*/flows/*/monitoring/` to conform exactly to this spec and Flow monitoring definitions.

## Acceptance Criteria

Alignment is complete when all of the following are true:

- the monitor event schema is defined in this monitor-side spec
- dashboard recommendations are derived from Flow YAML, not from a separate manual preset file
- Skill `output` fields remain artifact-oriented
- project monitoring traces under `projects/*/flows/*/monitoring/` conform to this spec
