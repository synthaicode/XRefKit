<!-- xid: 7B3E5D1A6104 -->
<a id="xid-7B3E5D1A6104"></a>

# Legacy Flow Skill Migration Rules

This fragment defines how to migrate a Flow / Skill created on an older
XRefKit state into the current repository structure.

## Core Rules

- do not treat old artifacts as already current-ready
- inventory before rewriting
- separate procedure from facts
- separate human-readable workflow from machine-readable workflow control
- default migrated artifacts to `trial`, not `stable`
- preserve unresolved mapping gaps explicitly

## Required Migration Outputs

Every migration must produce:

- `migration_report`
- `source_inventory`
- `target_skill_id`
- `mapping_table`
- `meta_scaffold`
- `migration_gaps`

## Old-To-New Mapping

- old `SKILL.md` procedure
  - target: `skills/<skill_id>/SKILL.md`
- old factual and domain blocks
  - target: `knowledge/`
- old workflow explanation
  - target: `docs/`
- old workflow control structure
  - target: `flows/` when reconstructable
- old runtime assumptions
  - target: `skills/<skill_id>/meta.md`

## Trial-First Rule

When old artifacts are migrated:

- `maturity` should default to `trial`
- `execution_mode` should default to `local_default`
- `guard_policy` should default to `required`
- observation linkage should be added

Do not promote directly to `stable` unless the migrated result already meets
current operational completeness.

## Migration Gap Types

Keep these gap types explicit:

- `missing_goal`
- `mixed_procedure_and_facts`
- `missing_runtime_fields`
- `missing_workflow_control`
- `missing_domain_sources`
- `unclear_target_skill_id`
- `unclear_flow_boundary`

## Completion Boundary

The migration is ready for current use only when:

- target skill id is explicit
- procedure and facts are separated
- current `meta.md` scaffold exists
- unresolved gaps are visible
- `trial` validation can be attempted

## Sources

- source_type: repo_doc
- source_path: ../../docs/062_legacy_flow_skill_migration_guide.md
- source_locator: whole_page
- extracted_at: 2026-05-02
