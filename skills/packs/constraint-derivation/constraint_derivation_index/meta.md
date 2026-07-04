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
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: route design or implementation artifacts to the correct bidirectional constraint-derivation Skills and sequence the secondary commonality pass
- responsibility: design specifications or implementation artifacts need derivation of missing confirmations, hidden assumptions, or boundary scenarios without implicit AI completion
- os_contract: v1
- constraints: do not infer requirement decisions from design prose or code alone; route to all applicable primary Skills before the secondary commonality pass; keep shared rules in knowledge instead of duplicating them across pack Skills; write the routing result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input is design-oriented, implementation-oriented, or mixed and collect the artifact types that must be inspected
  - planning: map artifact types to primary Skills in the downward or upward direction and determine whether a secondary commonality pass will be needed
  - execution: route the request, preserve prefix separation, and sequence `commonality_derivation` only after primary outputs exist
  - monitoring_and_control: stop if the task tries to approve unresolved items or skip derivation for applicable artifact classes
  - closure: return the selected Skill set, routing basis, unresolved gaps, and the next execution handoff
- tags: `design`, `review`, `routing`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
