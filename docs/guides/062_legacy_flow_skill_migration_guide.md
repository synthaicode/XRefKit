<!-- xid: E3B7D5A18C62 -->
<a id="xid-E3B7D5A18C62"></a>

# Legacy Flow Skill Migration Guide

This page defines how to migrate a Flow / Skill created on an older XRefKit
state into the current repository structure.

The target is not blind copy.
The target is to preserve the old operational intent while rebuilding it into
the current one-document `skill_definition_v1` model and runtime envelope.
The legacy split form remains a compatibility source during migration; it is
not the canonical target for new authoring.

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
2. rebuild the result into the current one-document SkillDefinition model

## Current Target Model

The current target model uses one canonical SkillDefinition document for the
reusable method and keeps shared facts and runtime control in their owning
layers:

- `skills/<skill_id>/SKILL.v1.md`
  - one-document SkillDefinition with method, applicability, inputs, outputs,
    criteria, Knowledge needs, and Skill-specific boundaries
- `knowledge/`
  - factual rules, evidence, and domain references resolved by XID on demand
- `docs/` and `flows/`
  - human guidance and machine-readable workflow control where applicable
- Workflow Protocol and runtime binding
  - common phases, roles, logging, closure, and instruction-derived runtime
    fields such as `capability`, `tuning`, `responsibility`, and `execution_mode`;
    their meanings and derivation belong to the [Workflow Runtime Binding
    contract](../core/contracts/111_workflow_runtime_binding.md#xid-8D50A972BA9F)

Existing `skills/<skill_id>/meta.md` plus `SKILL.md` pairs are
`legacy_split_v1` compatibility inputs. Keep them readable until their
replacement has been explicitly adopted.

## Migration Direction

When reading an old Flow / Skill:

- old execution procedure becomes the method in
  `skills/<skill_id>/SKILL.v1.md`
- old factual and domain blocks move to `knowledge/`
- old workflow explanation moves to `docs/`
- old workflow control definitions move to `flows/` when a machine-readable form
  exists or can be reconstructed safely
- old ad hoc runtime assumptions become Workflow Protocol runtime binding
  inputs or records; do not copy their semantics into the v1 method as fixed
  Skill identity

## Minimum Migration Output

Every migration should produce:

- migration report
- target skill id
- source artifact inventory
- old-to-new mapping table
- current `SKILL.v1.md` scaffold
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
- old artifacts often repeat runtime role prose that is now protocol-owned
- old artifacts often lack observation linkage
- old artifacts often mix procedure and domain facts

## Suggested Migration Procedure

1. collect the old Flow / Skill folder
2. inventory `SKILL.md`, `meta.md`, flow docs, YAML, and nearby domain files
3. generate a migration report and a `SKILL.v1.md` scaffold; retain the old
   `meta.md` and `SKILL.md` as compatibility evidence
4. split facts from procedure
5. rebuild target files under current `skills/`, `docs/`, `flows/`, and
   `knowledge/`
6. remove common `checker`, `quality_reviewer`, and `handoff_owner` role prose
   from the v1 document; Workflow Protocol owns those roles, while
   Skill-specific executor boundaries remain in the method
7. validate with `python -m xrefkit xref fix`
8. validate the v1 document with
   `python -m xrefkit skill definition-check --path <SKILL.v1.md> --json`,
   then run it explicitly with
   `python -m xrefkit skill run --definition <SKILL.v1.md> ... --json`

## Related

- [Skill authoring with xref](013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Skill operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Skill maturity governance](../core/contracts/059_skill_maturity_governance.md#xid-4E7B8D9C1A20)
- [Skill and Knowledge operating model](../core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
