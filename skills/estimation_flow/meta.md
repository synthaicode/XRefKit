<!-- xid: EA208AA244DF -->
<a id="xid-EA208AA244DF"></a>

# Skill Meta: estimation_flow

- skill_id: `estimation_flow`
- summary: execute estimation business activities through reusable comparison, projection, option-structuring, and ambiguity-classification capabilities
- use_when: user needs estimate options, supplier checks, or assumption clarification before requirements
- input: request, change target list, supplier definitions, optional budget definition
- output: supplier check results, cost patterns, solution options, assumption list, ambiguity classification
- execution_mode: `local_default`
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
- constraints: do not approve supplier adoption, budget, or final direction
- lifecycle:
  - startup: confirm request, change targets, supplier definitions, and budget evidence as needed
  - planning: define estimation scope and management rows
  - execution: perform supplier four-condition check, cost estimation, solution option generation, consultation on option tradeoffs when needed, and assumption ambiguity classification through `CAP-SUP-001 -> CAP-SUP-002 -> CAP-EST-001 -> CAP-EST-002`
  - monitoring_and_control: downgrade weak assumptions to `unknown`; preserve confirmation items
  - closure: finalize states and hand off unresolved assumptions
- tags: `estimation`, `planning`, `supplier`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/supply/100_cap_sup_001_supplier_four_condition_check.md#xid-2DC9A90A6508`
  - `../../capabilities/supply/110_cap_sup_002_cost_estimation.md#xid-754A17D69C7C`
  - `../../capabilities/estimation/100_cap_est_001_solution_option_generation.md#xid-BDB6B54A3571`
  - `../../capabilities/estimation/110_cap_est_002_assumption_ambiguity_classification.md#xid-B362EA06B9C2`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
