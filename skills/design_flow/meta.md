<!-- xid: 1B28D96E4C11 -->
<a id="xid-1B28D96E4C11"></a>

# Skill Meta: design_flow

- skill_id: `design_flow`
- summary: execute design business activity through reusable solution-design capability
- use_when: user needs implementation-ready design after planning outputs are approved
- input: approved requirements, work plan, source modification policy, data change policy, planning basis source list
- output: approved design, target paths, source modification design, data change design, design basis policy reference, and referenced constraint-derivation output paths when derivation was required
- maturity: `draft`
- execution_mode: `local_default`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute design business activity through reusable solution-design capability
- role_responsibilities:
  - executor: user needs implementation-ready design after planning outputs are approved
- os_contract: v1
- constraints: preserve unresolved design assumptions explicitly; do not redefine business scope; express the change method clearly enough for pre-code review; when structural design artifacts still imply unresolved behavior, route through the constraint-derivation pack before freezing implementation-facing design
- lifecycle:
  - startup: confirm planning outputs and source modification policy exist; if the input still includes unresolved structural design behavior, require constraint derivation before design closure
  - planning: define design scope, change-design boundaries, management rows, and whether constraint derivation is required before implementation-facing decisions
  - execution: perform solution design drafting through `CAP-DSN-001`, preserve the intended change method explicitly, and incorporate confirmed derivation outputs where structural ambiguity existed
  - monitoring_and_control: downgrade weak design assumptions or unclear change methods to `unknown`; stop if implementation-facing behavior is being fixed without prior confirmation where constraint derivation should have run
  - closure: finalize states and hand off the approved design package and design basis policy reference with unresolved items
- tags: `design`, `execution`, `implementation-preparation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701`
  - `../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711`
  - `../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
