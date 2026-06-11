<!-- xid: F6580A1C2345 -->
<a id="xid-F6580A1C2345"></a>

# Skill Meta: async_constraint_derivation

- skill_id: `async_constraint_derivation`
- summary: derive requirement confirmation gates from asynchronous jobs, queues, schedules, and batch execution structure
- use_when: queue, job, or batch specs may leave retry, restart, duplicate-run, or partial-failure behavior to implicit AI completion
- input: job definitions, batch designs, queue models, schedule rules, and async processing notes
- output: ACD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and rerun or restart matrices where required
- maturity: `draft`
- execution_mode: `local_default`
- model_tier: `standard`
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
- constraints: derive from execution model and state management, not nominal completion paths; keep restart, duplicate-run, schedule-boundary, and partial-failure gaps explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input contains async or batch execution structure and load the shared framework plus the async catalog
  - planning: identify queues, jobs, batches, schedule rules, and execution-state surfaces
  - execution: derive ACD items, expand rerun matrices where needed, and keep unsupported recovery behavior unresolved
  - monitoring_and_control: stop if rerun or multi-start behavior is being guessed from platform expectations rather than explicit rules
  - closure: return the derivation table, grouped confirmation items, and blocking restart or schedule gaps
- tags: `design`, `async`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/160_async_constraint_derivation_catalog.md#xid-72ECA94D1B35`
