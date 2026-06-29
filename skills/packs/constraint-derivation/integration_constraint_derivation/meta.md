<!-- xid: E547F90B1234 -->
<a id="xid-E547F90B1234"></a>

# Skill Meta: integration_constraint_derivation

- skill_id: `integration_constraint_derivation`
- summary: derive requirement confirmation gates from external APIs, webhooks, files, and messaging integration structure
- use_when: external integration specs may leave failure, timing, retry, or idempotency behavior to implicit AI completion
- input: API specs, integration flow diagrams, webhook notes, file exchange definitions, and messaging contracts
- output: ICD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and idempotency or retry matrices where required
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: derive requirement confirmation gates from external APIs, webhooks, files, and messaging integration structure
- role_responsibilities:
  - executor: external integration specs may leave failure, timing, retry, or idempotency behavior to implicit AI completion
  - quality_reviewer: independently review output acceptance when this Skill run requires a quality gate
  - handoff_owner: record outputs, unresolved items, next owner, and handoff boundary for this Skill run
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
- constraints: derive from integration structure and failure modes, not nominal success cases; keep retry, timeout, idempotency, and ordering gaps explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input contains external integration structure and load the shared framework plus the integration catalog
  - planning: identify synchronous, asynchronous, file, webhook, and messaging surfaces
  - execution: derive ICD items, expand idempotency matrices where needed, and emit unresolved behavior explicitly
  - monitoring_and_control: stop if failure handling is being assumed from generic platform norms rather than design evidence
  - closure: return the derivation table, grouped confirmation items, and blocking retry or idempotency gaps
- tags: `design`, `integration`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/150_integration_constraint_derivation_catalog.md#xid-6F0D7C1A2E44`
- observation_refs:
  - ../../../../work/sessions/2026-06-21_skill_run_skill_flow_authoring.md
