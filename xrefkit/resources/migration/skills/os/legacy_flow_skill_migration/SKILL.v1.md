---
schema_version: 1
skill_id: legacy_flow_skill_migration
xid: F8C1A5D3E920
summary: analyze an older Flow or Skill and generate a trial-first migration scaffold with explicit gaps
applies_when:
- a user has a Flow / Skill created on an older XRefKit state and wants to migrate it into the current repository structure without hand-mapping everything from scratch
exclusions:
- Human authority, scope, and final decisions remain explicit
- Missing evidence or ambiguous objectives remain unknown rather than being guessed
inputs:
- source folder or exported artifact from an older XRefKit state, optional target skill id, optional report output location
outputs:
- migration report, source inventory, old-to-new mapping table, current meta scaffold, and explicit migration gaps
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
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: legacy_flow_skill_migration_rules
  query: legacy Flow Skill migration rules
  required_when: Required when applying this Skill's procedure and decision criteria
  seed_xids:
  - 7B3E5D1A6104
control_refs: []
aliases:
- C5E2A7D19F84
- 8F1D7A2C4B63
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

## Additional bound references retained at repository cutover

These references were explicitly bound by the prior repository Skill. Apply them to the relevant method work; resolve their XIDs on demand.

- [Legacy Flow Skill Migration Guide](../../../docs/guides/062_legacy_flow_skill_migration_guide.md#xid-E3B7D5A18C62)

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: legacy_flow_skill_migration

## Purpose

Analyze a Flow / Skill created on an older XRefKit state and generate a
current trial-first migration scaffold.

Use the canonical rules in
`knowledge/operations/130_legacy_flow_skill_migration_rules.md#xid-7B3E5D1A6104`.

## Required Knowledge (XID)

- [Context direction guard rules](../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)
- [Legacy Flow / Skill migration rules](../../../knowledge/operations/130_legacy_flow_skill_migration_rules.md#xid-7B3E5D1A6104)
- [Legacy Flow / Skill migration guide](../../../docs/guides/062_legacy_flow_skill_migration_guide.md#xid-E3B7D5A18C62)

## Optional References

- [Legacy Flow / Skill migration template](references/legacy_flow_skill_migration_template.md#xid-9DD40488BB9D)

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

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: analyze a Flow / Skill from an older XRefKit state and generate a current trial-first migration scaffold

- use_when: a user has a Flow / Skill created on an older XRefKit state and wants to migrate it into the current repository structure without hand-mapping everything from scratch

- input: source folder or exported artifact from an older XRefKit state, optional target skill id, optional report output location

- output: migration report, source inventory, old-to-new mapping table, current meta scaffold, and explicit migration gaps

- constraints: do not overwrite current canonical assets blindly; default migrated targets to trial; keep mixed procedure/facts and missing runtime fields explicit; do not claim flows are machine-readable unless a real control structure exists

- lifecycle:
  - startup: confirm source artifact location and load migration rules
  - planning: inventory source files and identify candidate target skill id and migration gaps
  - execution: generate migration report and trial-first scaffold
  - monitoring_and_control: downgrade unsupported mappings and preserve unresolved gaps
  - closure: return report paths, scaffold paths, and the smallest next migration step

- tags: `operations`, `migration`, `legacy`, `flow`, `skill`

- knowledge_slots:
  - name=legacy_flow_skill_migration_rules; bind=7B3E5D1A6104
  - name=legacy_flow_skill_migration_guide; bind=E3B7D5A18C62

- observation_refs:
  - `../../../observations/2026-05-02_session_legacy_flow_skill_migration_seed.md`
