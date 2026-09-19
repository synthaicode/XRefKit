---
schema_version: 1
skill_id: legacy_flow_skill_migration
xid: F8C1A5D3E920
aliases:
  - C5E2A7D19F84
  - 8F1D7A2C4B63
summary: analyze an older Flow or Skill and generate a trial-first migration scaffold with explicit gaps
applies_when:
  - an older XRefKit Flow or Skill must be migrated without manual mapping from scratch
exclusions:
  - Human authority, scope, and final decisions remain explicit
  - Missing evidence or ambiguous objectives remain unknown rather than being guessed
inputs:
  - source folder or exported legacy artifact, optional target skill id, optional report output path
outputs:
  - migration report, source inventory, old-to-new mapping, current scaffold, explicit migration gaps
criteria:
  - id: boundary_preservation
    statement: The Skill preserves its human decision boundary and keeps missing evidence or ambiguity explicit
    verification: Inspect the method output, unknowns, and handoff for unsupported closure
  - id: evidence_traceability
    statement: Non-trivial conclusions retain source or state evidence
    verification: Check the result for source pointers and recorded evidence
  - id: output_closure
    statement: The declared artifact and next action or handoff are returned
    verification: Check output paths, unresolved items, and ownership before closure
knowledge_needs:
  - id: legacy_flow_skill_migration_rules
    query: legacy Flow Skill migration rules
    required_when: Required when applying this Skill's procedure and decision criteria
    seed_xids:
      - 7B3E5D1A6104
control_refs: []
---
<!-- xid: F8C1A5D3E920 -->
<a id="xid-F8C1A5D3E920"></a>

# Skill: legacy_flow_skill_migration

## Purpose

Analyze a Flow / Skill created on an older XRefKit state and generate a
current trial-first migration scaffold.

Use the canonical rules in
`knowledge/operations/130_legacy_flow_skill_migration_rules.md#xid-7B3E5D1A6104`.

## Inputs

- source folder or exported artifact from an older XRefKit state
- optional target skill id
- optional report output path

## Outputs

- migration report
- source inventory
- old-to-new mapping table
- current `meta` scaffold
- explicit migration gaps

## Startup

- Confirm source artifact location exists.
- Confirm whether the source is:
  - older checkout folder
  - exported skill folder
  - copied flow/skill bundle
- Load migration rules and template.

## Planning

- Inventory source files such as:
  - `SKILL.md`
  - `meta.md`
  - flow docs
  - YAML workflow control
  - nearby domain/reference files
- Identify the candidate target skill id.
- Classify content into:
  - execution procedure
  - factual/domain content
  - workflow explanation
  - workflow control
  - runtime assumptions
- Identify migration gaps.

## Execution

1. Produce a source inventory.
2. Produce an old-to-new mapping table.
3. Generate a current `meta` scaffold that defaults to `trial`.
4. Record explicit migration gaps.
5. If using the helper tool, run:

```powershell
python tools/migrate_legacy_flow_skill.py --source-dir <old-skill-dir> --out-dir <workspace-or-target-dir>
```

6. Use the template in
   `references/legacy_flow_skill_migration_template.md` or equivalent
   structure.

## Monitoring and Control

- Downgrade any unsupported mapping into an explicit gap.
- Do not claim `flows/` output unless a real machine-readable control structure
  exists.
- Do not claim `stable` readiness from old artifacts alone.
- Keep mixed procedure/fact content visible until split.

## Closure

- Return report paths and scaffold paths.
- Return migration gaps.
- Return the smallest next step, such as:
  - split facts from procedure
  - move workflow explanation to docs
  - add current meta fields
  - validate trial readiness

## Rules

- Do not overwrite current canonical assets blindly.
- Do not erase legacy intent while normalizing structure.
- Default to `trial`, not `stable`.
- Keep migration evidence and unresolved gaps explicit.
