<!-- xid: 8F1D7A2C4B63 -->
<a id="xid-8F1D7A2C4B63"></a>

# Skill Meta: legacy_flow_skill_migration

- skill_id: `legacy_flow_skill_migration`
- summary: analyze a Flow / Skill from an older XRefKit state and generate a current trial-first migration scaffold
- use_when: a user has a Flow / Skill created on an older XRefKit state and wants to migrate it into the current repository structure without hand-mapping everything from scratch
- input: source folder or exported artifact from an older XRefKit state, optional target skill id, optional report output location
- output: migration report, source inventory, old-to-new mapping table, current meta scaffold, and explicit migration gaps
- maturity: `trial`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: analyze a Flow / Skill from an older XRefKit state and generate a current trial-first migration scaffold
- responsibility: a user has a Flow / Skill created on an older XRefKit state and wants to migrate it into the current repository structure without hand-mapping everything from scratch
- os_contract: v1
- constraints: do not overwrite current canonical assets blindly; default migrated targets to trial; keep mixed procedure/facts and missing runtime fields explicit; do not claim flows are machine-readable unless a real control structure exists
- lifecycle:
  - startup: confirm source artifact location and load migration rules
  - planning: inventory source files and identify candidate target skill id and migration gaps
  - execution: generate migration report and trial-first scaffold
  - monitoring_and_control: downgrade unsupported mappings and preserve unresolved gaps
  - closure: return report paths, scaffold paths, and the smallest next migration step
- tags: `operations`, `migration`, `legacy`, `flow`, `skill`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../../knowledge/operations/130_legacy_flow_skill_migration_rules.md#xid-7B3E5D1A6104`
  - `../../../docs/guides/062_legacy_flow_skill_migration_guide.md#xid-E3B7D5A18C62`
- observation_refs:
  - `../../../observations/2026-05-02_session_legacy_flow_skill_migration_seed.md`
