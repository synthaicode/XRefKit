<!-- xid: C325D7E9F122 -->
<a id="xid-C325D7E9F122"></a>

# Skill Meta: ui_constraint_derivation

- skill_id: `ui_constraint_derivation`
- summary: derive requirement confirmation gates from UI structure, interaction states, and screen transitions
- use_when: screen specifications, wireframes, or UI behavior notes may leave states or transitions to implicit AI completion
- input: screen specs, wireframes, UI notes, interaction flows, and client-side validation descriptions
- output: UCD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and explicit design-time UI decisions
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: derive requirement confirmation gates from UI structure, interaction states, and screen transitions
- role_responsibilities:
  - executor: screen specifications, wireframes, or UI behavior notes may leave states or transitions to implicit AI completion
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
- constraints: derive from visible UI structure instead of expected happy-path behavior; keep transition and validation gaps explicit; do not silently align UI behavior with backend assumptions; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input contains UI structure and load the shared framework plus the UI catalog
  - planning: identify inputs, actions, screen transitions, and asynchronous UI behaviors
  - execution: derive UCD items, group them by screen element, and keep unsupported behavior unresolved
  - monitoring_and_control: stop if UI edge states are being collapsed into vague happy-path handling
  - closure: return the derivation table, grouped confirmation items, and explicit UI design decisions
- tags: `design`, `ui`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/130_ui_constraint_derivation_catalog.md#xid-31C5A06B7E22`
- observation_refs:
  - ../../../../work/sessions/2026-06-21_skill_run_skill_flow_authoring.md
