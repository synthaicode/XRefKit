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
- guard_policy: `required`
- os_contract:
  - version: `1`
  - worklist_policy: `required`
  - execution_role: `required`
  - check_role: `required`
  - logging_policy: `session_required`
  - judgment_log_policy: `required_when_non_trivial`
  - unknown_risk_policy: `explicit`
  - closure_gate: `required`
  - handoff_policy: `explicit`
- constraints: do not overwrite current canonical assets blindly; default migrated targets to trial; keep mixed procedure/facts and missing runtime fields explicit; do not claim flows are machine-readable unless a real control structure exists
- lifecycle:
  - startup: confirm source artifact location and load migration rules
  - planning: inventory source files and identify candidate target skill id and migration gaps
  - execution: generate migration report and trial-first scaffold
  - monitoring_and_control: downgrade unsupported mappings and preserve unresolved gaps
  - closure: return report paths, scaffold paths, and the smallest next migration step
- tags: `operations`, `migration`, `legacy`, `flow`, `skill`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/operations/130_legacy_flow_skill_migration_rules.md#xid-7B3E5D1A6104`
  - `../../docs/062_legacy_flow_skill_migration_guide.md#xid-E3B7D5A18C62`
- observation_refs:
  - `../../work/sessions/2026-05-02_session_legacy_flow_skill_migration_seed.md`
