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
- constraints: never store plaintext passwords or master secrets in Git-tracked files; never ask users to reveal current passwords
- tags: `security`, `password`, `mfa`, `vault`, `checklist`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `./references/confidential_password_state_schema.md`
