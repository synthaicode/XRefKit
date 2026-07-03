<!-- xid: A7691B2D3456 -->
<a id="xid-A7691B2D3456"></a>

# Skill Meta: auth_constraint_derivation

- skill_id: `auth_constraint_derivation`
- summary: derive requirement confirmation gates from authentication, authorization, and account-governance structure
- use_when: auth or permission specs may leave session, role, or access-boundary behavior to implicit AI completion
- input: auth design docs, role matrices, permission models, API-client auth notes, and account-governance rules
- output: AACD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and permission or session matrices where required
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: derive requirement confirmation gates from authentication, authorization, and account-governance structure
- responsibility: auth or permission specs may leave session, role, or access-boundary behavior to implicit AI completion
- os_contract: v1
- constraints: derive from explicit access structure and account state, not nominal successful access; keep session, role, tenant-boundary, and account-lifecycle gaps explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input contains auth or permission structure and load the shared framework plus the auth catalog
  - planning: identify authentication, authorization, client-auth, and account-lifecycle surfaces
  - execution: derive AACD items, expand permission or session matrices where needed, and keep unresolved security behavior explicit
  - monitoring_and_control: stop if auth behavior is being softened into generic best-effort wording or hidden defaults
  - closure: return the derivation table, grouped confirmation items, and blocking session or permission gaps
- tags: `design`, `security`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/170_auth_constraint_derivation_catalog.md#xid-8B14D9E70326`
- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
