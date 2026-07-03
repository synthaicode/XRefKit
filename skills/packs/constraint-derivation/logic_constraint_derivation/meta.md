<!-- xid: D436E8FA0123 -->
<a id="xid-D436E8FA0123"></a>

# Skill Meta: logic_constraint_derivation

- skill_id: `logic_constraint_derivation`
- summary: derive requirement confirmation gates from branching, calculations, state transitions, and approval logic
- use_when: business-logic specs may leave boundary, exception, or transition behavior to implicit AI completion
- input: flowcharts, calculation rules, state models, approval rules, and logic design notes
- output: LCD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and any required state-transition matrix
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: derive requirement confirmation gates from branching, calculations, state transitions, and approval logic
- responsibility: business-logic specs may leave boundary, exception, or transition behavior to implicit AI completion
- os_contract: v1
- constraints: derive all structurally implied branches and boundaries; do not infer unspecified else-paths; keep state-transition and calculation edge cases explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input contains business logic structure and load the shared framework plus the logic catalog
  - planning: identify branching, calculations, transitions, and approval-flow areas
  - execution: derive LCD items, expand transition matrices where required, and keep unresolved logic explicit
  - monitoring_and_control: stop if unsupported business rules are being guessed from examples or happy paths
  - closure: return the derivation table, grouped confirmation items, and any transition matrices requiring approval
- tags: `design`, `logic`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
- knowledge_refs:
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/140_logic_constraint_derivation_catalog.md#xid-4E5B8923C912`
- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
