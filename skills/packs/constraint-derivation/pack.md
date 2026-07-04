<!-- xid: 77072E6680DA -->
<a id="xid-77072E6680DA"></a>

# Pack Manifest: constraint-derivation

This manifest is the canonical, machine-checkable definition of the
`constraint-derivation` Business Pack. It declares which assets the pack OWNS
(exclusive) and which it USES (shared, may live anywhere including the OS core).
For the Business Pack concept see
[Business Pack model](../../../docs/core/models/071_business_pack_model.md#xid-40511A8A06CD).

- pack_id: `constraint-derivation`
- summary: from already-built design and code artifacts, derive the use cases and confirmation points they imply and check whether they match the original intent (reverse, intent-alignment verification)
- maturity: `trial`
- depends_on:
  - os_contract_version: `1`
- entry: `skills/packs/constraint-derivation/constraint_derivation_index/SKILL.md`
- owns_skills:
  - `skills/packs/constraint-derivation/constraint_derivation_index`
  - `skills/packs/constraint-derivation/design_constraint_derivation`
  - `skills/packs/constraint-derivation/ui_constraint_derivation`
  - `skills/packs/constraint-derivation/logic_constraint_derivation`
  - `skills/packs/constraint-derivation/integration_constraint_derivation`
  - `skills/packs/constraint-derivation/async_constraint_derivation`
  - `skills/packs/constraint-derivation/auth_constraint_derivation`
  - `skills/packs/constraint-derivation/code_constraint_derivation`
  - `skills/packs/constraint-derivation/cross_constraint_derivation`
  - `skills/packs/constraint-derivation/integration_scenario_derivation`
  - `skills/packs/constraint-derivation/commonality_derivation`
- owns_knowledge:
  - `knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `knowledge/packs/constraint-derivation/120_design_constraint_derivation_catalog.md#xid-2D14F88A6C01`
  - `knowledge/packs/constraint-derivation/130_ui_constraint_derivation_catalog.md#xid-31C5A06B7E22`
  - `knowledge/packs/constraint-derivation/140_logic_constraint_derivation_catalog.md#xid-4E5B8923C912`
  - `knowledge/packs/constraint-derivation/150_integration_constraint_derivation_catalog.md#xid-6F0D7C1A2E44`
  - `knowledge/packs/constraint-derivation/160_async_constraint_derivation_catalog.md#xid-72ECA94D1B35`
  - `knowledge/packs/constraint-derivation/170_auth_constraint_derivation_catalog.md#xid-8B14D9E70326`
  - `knowledge/packs/constraint-derivation/180_commonality_derivation_signals.md#xid-9C27AE51D648`
  - `knowledge/packs/constraint-derivation/190_code_constraint_derivation_catalog.md#xid-A1D4E8C93B71`
  - `knowledge/packs/constraint-derivation/200_cross_constraint_derivation_catalog.md#xid-B2E5F9DA4C82`
  - `knowledge/packs/constraint-derivation/210_integration_scenario_derivation_catalog.md#xid-C3F60AEB5D93`
- uses_knowledge:
  - `knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- inputs: design specifications/diagrams, generated or reviewed C# code, DDL, UI/workflow/API/auth/integration artifacts, optional earlier derivation outputs
- outputs: per-area derived use cases and requirement confirmation gates, cross-cutting commonality candidates, routing note in work/constraint_derivation/
