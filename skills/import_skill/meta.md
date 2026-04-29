<!-- xid: 1DF4555E1B02 -->
<a id="xid-1DF4555E1B02"></a>

# Skill Meta: import_skill

- skill_id: `import_skill`
- summary: import external skill content into this repository split model
- use_when: external skill needs to be made runnable in this repo
- input: source URL or ZIP path, optional target skill id
- output: normalized `skills/<skill_id>/SKILL.md` and index registration
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
- constraints: keep domain facts out of skill body; use `knowledge/...#xid-...`; run policy inspection before import; compose the context-direction guard by default unless the imported skill explicitly qualifies for the closed-world exception
- tags: `import`, `normalization`, `xref`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
