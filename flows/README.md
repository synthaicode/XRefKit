# Flow Models

This directory stores machine-readable workflow control structures in YAML.

## Purpose

- keep workflow control structures in a normalized format
- support validation, matrix generation, and future tooling
- keep `docs/` focused on human-readable explanation

## Position

- `flows/`: machine-readable workflow source of truth
- `docs/`: human-readable workflow explanation and governance

## Common Fields

- `flow_id`: stable workflow identifier
- `name`: workflow name
- `doc_xid`: corresponding human-facing workflow document
- `owner`:
  - `primary`
  - optional `support`
- `phase`:
  - `bootstrap`
  - `normal`
  - `control`
- `runs_before` or `runs_after`
- `inputs`
- `outputs`
- `handoff`:
  - `output_to`
  - `artifacts`
  - `escalation`
- `sequence`
- `control_rules`

## Notes

- YAML files here are not XID-managed.
- Human-readable workflow interpretation remains in `docs/`.
- When updating a workflow, update both the YAML model and the matching `docs/` page.
