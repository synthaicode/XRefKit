<!-- xid: F6580A1C2345 -->
<a id="xid-F6580A1C2345"></a>

# Skill Meta: async_constraint_derivation

- skill_id: `async_constraint_derivation`
- summary: derive requirement confirmation gates from asynchronous jobs, queues, schedules, and batch execution structure
- use_when: queue, job, or batch specs may leave retry, restart, duplicate-run, or partial-failure behavior to implicit AI completion
- input: job definitions, batch designs, queue models, schedule rules, and async processing notes
- output: ACD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and rerun or restart matrices where required
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: derive requirement confirmation gates from asynchronous jobs, queues, schedules, and batch execution structure
- responsibility: queue, job, or batch specs may leave retry, restart, duplicate-run, or partial-failure behavior to implicit AI completion
- os_contract: v1
- constraints: derive from execution model and state management, not nominal completion paths; keep restart, duplicate-run, schedule-boundary, and partial-failure gaps explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input contains async or batch execution structure and load the shared framework plus the async catalog
  - planning: identify queues, jobs, batches, schedule rules, and execution-state surfaces
  - execution: derive ACD items, expand rerun matrices where needed, and keep unsupported recovery behavior unresolved
  - monitoring_and_control: stop if rerun or multi-start behavior is being guessed from platform expectations rather than explicit rules
  - closure: return the derivation table, grouped confirmation items, and blocking restart or schedule gaps
- tags: `design`, `async`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/160_async_constraint_derivation_catalog.md#xid-72ECA94D1B35`
- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
