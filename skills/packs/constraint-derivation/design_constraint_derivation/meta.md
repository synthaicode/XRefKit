<!-- xid: B214C6D8E011 -->
<a id="xid-B214C6D8E011"></a>

# Skill Meta: design_constraint_derivation

- skill_id: `design_constraint_derivation`
- summary: derive requirement confirmation gates from data-structure, database, relationship, and operation design
- use_when: DDL, schema, ER, or CRUD-oriented design structures may hide unresolved behavior that AI would otherwise complete implicitly
- input: DDL, schema definitions, ER models, CRUD design notes, and related operation descriptions
- output: DCD-prefixed derivation file under `work/constraint_derivation/` by default, plus design-time decision list and any required combination-expansion matrix
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: derive requirement confirmation gates from data-structure, database, relationship, and operation design
- responsibility: DDL, schema, ER, or CRUD-oriented design structures may hide unresolved behavior that AI would otherwise complete implicitly
- os_contract: v1
- constraints: keep derivation mechanical and structure-driven; do not invent missing business behavior; separate design-time decisions from requirement confirmations; expand combinations only when structural axes are present; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the input contains data or operation structure and load the shared framework plus the design catalog
  - planning: identify design elements and likely combination axes
  - execution: enumerate elements, derive DCD items, expand matrices where required, and emit unresolved items explicitly
  - monitoring_and_control: downgrade unsupported assumptions to unresolved and stop if the user tries to bypass unconfirmed structural cases
  - closure: return the derivation table, grouped confirmation items, design-time decisions, and remaining gaps
- tags: `design`, `data-structure`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=design_constraint_derivation_catalog; bind=2D14F88A6C01
- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
