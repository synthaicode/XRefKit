<!-- xid: A08CBDFB082D -->
<a id="xid-A08CBDFB082D"></a>

# Pack Manifest: business-intake

This manifest is the canonical, machine-checkable definition of the
`business-intake` Business Pack. It declares which assets the pack OWNS
(exclusive) and which it USES (shared, may live anywhere including the OS core).
For the human-facing rationale and dependency map see
[Business intake pack dependency design](../../../docs/packs/business-intake/065_business_intake_pack_dependency_design.md#xid-D334C1964342)
and [Business intake pack entry](../../../docs/packs/business-intake/066_business_intake_pack_entry.md#xid-732E41DCA2E8).

- pack_id: `business-intake`
- summary: learn incomplete business fragments and shape them into one scope-ready business unit before later execution design
- maturity: `trial`
- depends_on:
  - os_contract_version: `1`
- entry: `../../../docs/packs/business-intake/066_business_intake_pack_entry.md#xid-732E41DCA2E8`
- owns_skills:
  - `skills/packs/business-intake/business_learning_interview`
  - `skills/packs/business-intake/business_intake_scoping`
  - `skills/packs/business-intake/decision_topology_analysis`
- owns_knowledge:
  - `knowledge/packs/business-intake/120_business_learning_interview_rules.md`
  - `knowledge/packs/business-intake/110_business_intake_scoping_rules.md`
- owns_flows:
  - `flows/packs/business-intake/business_intake_workflow.yaml`
- uses_capabilities:
  - `capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- uses_knowledge:
  - `knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- inputs: user fragments, stated goal or expected result, partial artifacts, partial ownership or handoff knowledge, relevant business rules when available
- outputs: interview-cycle summary, current business hypothesis, explicit open questions, next best question, discovery-first scoped intake note, previous side / current responsibility / next side, smallest next confirmation point
