<!-- xid: A103B5C7D900 -->
<a id="xid-A103B5C7D900"></a>

# Skill Meta: constraint_derivation_index

- skill_id: `constraint_derivation_index`
- summary: route design or implementation artifacts to the correct bidirectional constraint-derivation Skills and sequence the secondary commonality pass
- use_when: design specifications or implementation artifacts need derivation of missing confirmations, hidden assumptions, or boundary scenarios without implicit AI completion
- input: design artifacts, code artifacts, partial specs, expected implementation target, and optional already-derived constraint lists
- output: selected primary Skill set, execution order, shared derivation policy reminder, optional secondary-pass trigger decision, and a routing note written under `work/constraint_derivation/` unless the user specifies another path
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `light`
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
- constraints: do not infer requirement decisions from design prose or code alone; route to all applicable primary Skills before the secondary commonality pass; keep shared rules in knowledge instead of duplicating them across pack Skills; write the routing result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input is design-oriented, implementation-oriented, or mixed and collect the artifact types that must be inspected
  - planning: map artifact types to primary Skills in the downward or upward direction and determine whether a secondary commonality pass will be needed
  - execution: route the request, preserve prefix separation, and sequence `commonality_derivation` only after primary outputs exist
  - monitoring_and_control: stop if the task tries to approve unresolved items or skip derivation for applicable artifact classes
  - closure: return the selected Skill set, routing basis, unresolved gaps, and the next execution handoff
- tags: `design`, `review`, `routing`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
- observation_refs:
  - ../../../../work/sessions/2026-06-21_skill_run_skill_flow_authoring.md
