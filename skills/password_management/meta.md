<!-- xid: AFA67C6DEC22 -->
<a id="xid-AFA67C6DEC22"></a>

# Skill Meta: password_management

- skill_id: `password_management`
- summary: assess and improve password hygiene with vault, MFA, and prioritized remediation
- use_when: user asks to build, review, or migrate password management practices for personal or team accounts
- input: account inventory, current password habits/tools, security incidents, constraints, confidential password state file
- output: risk findings, prioritized fixes, vault/MFA rollout plan, recovery checklist, updated confidential state record
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
- constraints: never store plaintext passwords or master secrets in Git-tracked files; never ask users to reveal current passwords
- tags: `security`, `password`, `mfa`, `vault`, `checklist`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `./references/confidential_password_state_schema.md`
