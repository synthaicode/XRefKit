<!-- xid: E5812C0D7FB6 -->
<a id="xid-E5812C0D7FB6"></a>

# Skill Meta: cross_constraint_derivation

- skill_id: `cross_constraint_derivation`
- summary: compare DDL structure and C# processing structure to surface missing flows, implicit assumptions, and duplicated rule ownership
- use_when: DDL and corresponding C# code both exist and their mismatch may expose missing use-case handling or undocumented assumptions
- input: DDL or schema definitions, corresponding C# code, and optional mapping hints between tables and code paths
- output: XCD-prefixed derivation file under `work/constraint_derivation/` by default, plus missing-flow and implicit-assumption confirmations
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `heavy`
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
- constraints: compare valid DDL variations against actual code handling instead of assuming one side is authoritative; keep mismatches explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm both DDL and code inputs exist and load the framework plus the cross-constraint catalog
  - planning: identify the entities, fields, states, and flows that must be compared
  - execution: compare DDL and code structures, classify mismatches, and write the XCD result file
  - monitoring_and_control: stop if the comparison drifts into guessed business meaning without structural support
  - closure: return the written derivation path, highest-priority mismatches, and remaining gaps
- tags: `review`, `cross-check`, `.NET`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../docs/014_working_area_policy.md#xid-111D282CA0EA`
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/200_cross_constraint_derivation_catalog.md#xid-B2E5F9DA4C82`
- observation_refs:
  - ../../../../work/sessions/2026-06-21_skill_run_skill_flow_authoring.md
