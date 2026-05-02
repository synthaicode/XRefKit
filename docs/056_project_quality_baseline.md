<!-- xid: 1C4B72D5E901 -->
<a id="xid-1C4B72D5E901"></a>

# Project Quality Baseline

This page defines the minimum quality baseline for executable subprojects stored under `projects/`.

## Purpose

Keep bundled applications reviewable and reproducible even when they are secondary to the repository's document and AI-control functions.

## Scope

Apply this baseline to each top-level project under `projects/` that has its own `package.json`.

## Minimum Baseline

Each in-repo executable project must provide:

1. a `README.md` that explains purpose, startup, and quality-check entry points
2. an explicit `scripts.check` entry in `package.json`
3. an explicit `engines.node` declaration in `package.json`
4. a lockfile when the project declares runtime or development dependencies

## Quality-Check Rule

`scripts.check` is the stable entry point for project validation.

The exact internal commands may vary by project, but the baseline intent is:

- compile or build validation when the project has a compiler or bundler
- linter or equivalent static validation when available
- type-check or parse validation when the project language supports it

## Current Standardization

- `projects/slides-app/`
  - `check`: lint + typecheck + build
- `projects/flow-monitor-dashboard/`
  - `check`: JavaScript syntax check + JSON parse validation

## Enforcement

The repository quality gate should reject a project that lacks the baseline structure.

Use:

```powershell
python tools/check_project_quality_baseline.py
```

This metadata check complements, but does not replace, each project's own `npm run check`.

## Related

- [Flow Quality Assurance Mechanism](042_flow_quality_assurance_mechanism.md#xid-8B31F02A4011)
- [System Quality Feedback Loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012)
- [System Quality Feedback Register](044_system_quality_feedback_register.md#xid-8B31F02A4013)
