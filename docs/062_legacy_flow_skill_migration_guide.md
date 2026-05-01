<!-- xid: E3B7D5A18C62 -->
<a id="xid-E3B7D5A18C62"></a>

# Legacy Flow Skill Migration Guide

This page defines how to migrate a Flow / Skill created on an older XRefKit
state into the current repository structure.

The target is not blind copy.
The target is to preserve the old operational intent while rebuilding it into
the current split model and runtime envelope.

## Scope

Use this guide when the source artifact was created on an older XRefKit state
such as:

- a historical checkout of this repository
- an exported folder from an older checkout
- a Flow / Skill bundle copied from an older branch or machine

## Core Rule

Do not treat the old artifact as already current-ready.

Migrate it in two phases:

1. analyze the old structure and create a migration report
2. rebuild the result into the current split model

## Current Target Model

The current target model separates:

- `flows/`
  - machine-readable workflow control
- `docs/`
  - human-readable workflow and guidance
- `skills/<skill_id>/SKILL.md`
  - execution procedure
- `skills/<skill_id>/meta.md`
  - load gate and runtime envelope
- `knowledge/`
  - factual rules, evidence, and domain references

## Migration Direction

When reading an old Flow / Skill:

- old execution procedure stays closest to `skills/<skill_id>/SKILL.md`
- old factual and domain blocks move to `knowledge/`
- old workflow explanation moves to `docs/`
- old workflow control definitions move to `flows/` when a machine-readable form
  exists or can be reconstructed safely
- old ad hoc runtime assumptions become explicit fields in `meta.md`

## Minimum Migration Output

Every migration should produce:

- migration report
- target skill id
- source artifact inventory
- old-to-new mapping table
- current `meta.md` scaffold
- unresolved migration gaps

## Minimum Migration Questions

Before the migrated result is treated as runnable, confirm:

- what was the old business goal?
- what execution procedure belongs in the Skill?
- what factual or domain content should be moved to `knowledge/`?
- what workflow explanation belongs in `docs/`?
- what workflow control belongs in `flows/`?
- which current runtime fields are still missing?

## Runtime Readiness Rule

Old Flow / Skill artifacts should normally migrate first to `trial`, not
directly to `stable`.

Reasons:

- old artifacts often lack explicit `maturity`
- old artifacts often lack `execution_mode`
- old artifacts often lack `guard_policy`
- old artifacts often lack observation linkage
- old artifacts often mix procedure and domain facts

## Suggested Migration Procedure

1. collect the old Flow / Skill folder
2. inventory `SKILL.md`, `meta.md`, flow docs, YAML, and nearby domain files
3. generate a migration report and current `meta` scaffold
4. split facts from procedure
5. rebuild target files under current `skills/`, `docs/`, `flows/`, and
   `knowledge/`
6. validate with `python -m fm xref fix`
7. validate the new target with `python -m fm skill check --level trial`

## Related

- [Skill authoring with xref](013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Skill maturity governance](059_skill_maturity_governance.md#xid-4E7B8D9C1A20)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
