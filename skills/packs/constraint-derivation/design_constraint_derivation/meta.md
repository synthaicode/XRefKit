<!-- xid: B214C6D8E011 -->
<a id="xid-B214C6D8E011"></a>

# Skill Meta: design_constraint_derivation

- skill_id: `design_constraint_derivation`
- summary: derive requirement confirmation gates from data-structure, database, relationship, and operation design
- use_when: DDL, schema, ER, or CRUD-oriented design structures may hide unresolved behavior that AI would otherwise complete implicitly
- input: DDL, schema definitions, ER models, CRUD design notes, and related operation descriptions
- output: DCD-prefixed derivation file under `work/constraint_derivation/` by default, plus design-time decision list and any required combination-expansion matrix
- maturity: `draft`
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
- constraints: keep derivation mechanical and structure-driven; do not invent missing business behavior; separate design-time decisions from requirement confirmations; expand combinations only when structural axes are present; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input contains data or operation structure and load the shared framework plus the design catalog
  - planning: identify design elements and likely combination axes
  - execution: enumerate elements, derive DCD items, expand matrices where required, and emit unresolved items explicitly
  - monitoring_and_control: downgrade unsupported assumptions to unresolved and stop if the user tries to bypass unconfirmed structural cases
  - closure: return the derivation table, grouped confirmation items, design-time decisions, and remaining gaps
- tags: `design`, `data-structure`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/120_design_constraint_derivation_catalog.md#xid-2D14F88A6C01`
