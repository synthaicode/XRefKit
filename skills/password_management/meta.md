# Skill Meta: password_management

- skill_id: `password_management`
- summary: assess and improve password hygiene with vault, MFA, and prioritized remediation
- use_when: user asks to build, review, or migrate password management practices for personal or team accounts
- input: account inventory, current password habits/tools, security incidents, constraints, confidential password state file
- output: risk findings, prioritized fixes, vault/MFA rollout plan, recovery checklist, updated confidential state record
- constraints: never store plaintext passwords or master secrets in Git-tracked files; never ask users to reveal current passwords
- tags: `security`, `password`, `mfa`, `vault`, `checklist`
- skill_doc: `./SKILL.md`
- knowledge_refs: `./references/confidential_password_state_schema.md`
