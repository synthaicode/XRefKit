<!-- xid: F6923D1E80C8 -->
<a id="xid-F6923D1E80C8"></a>

# Skill Meta: integration_scenario_derivation

- skill_id: `integration_scenario_derivation`
- summary: derive integration-only failure and compensation scenarios from DDL, processing order, and external system boundaries
- use_when: DDL, code, and external-boundary specs together may hide partial-failure, retry, or compensation scenarios that unit-level reasoning misses
- input: DDL or schema definitions, processing-order-aware code, external API or boundary specs, and optional retry or transaction notes
- output: ISD-prefixed derivation file under `work/constraint_derivation/` by default, plus compensation-design items, partial-failure matrices, and post-confirmation test candidates
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `heavy`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: derive integration-only failure and compensation scenarios from DDL, processing order, and external system boundaries
- role_responsibilities:
  - executor: DDL, code, and external-boundary specs together may hide partial-failure, retry, or compensation scenarios that unit-level reasoning misses
- os_contract: v1
- constraints: focus on boundary-crossing state progression rather than isolated method correctness; keep compensation and retry questions explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm DDL, code, and boundary inputs exist and load the framework plus the integration-scenario catalog
  - planning: identify ordered boundary crossings, persistence points, and retry surfaces
  - execution: derive partial-failure scenarios, compensation questions, and write the ISD result file
  - monitoring_and_control: stop if unit-level success is being mistaken for boundary-level correctness
  - closure: return the written derivation path, compensation-design items, and remaining gaps
- tags: `review`, `integration`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA`
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/210_integration_scenario_derivation_catalog.md#xid-C3F60AEB5D93`
- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
