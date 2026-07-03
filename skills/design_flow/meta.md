<!-- xid: 1B28D96E4C11 -->
<a id="xid-1B28D96E4C11"></a>

# Skill Meta: design_flow

- skill_id: `design_flow`
- summary: execute design business activity through reusable solution-design capability
- use_when: user needs implementation-ready design after planning outputs are approved
- input: approved requirements, work plan, source modification policy, current source structure findings from canonical knowledge for each implementation target, data change policy, planning basis source list
- output: approved design, target paths, source modification design, data change design, source analysis basis reference, design basis policy reference, and referenced constraint-derivation output paths when derivation was required
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute design business activity through reusable solution-design capability
- responsibility: user needs implementation-ready design after planning outputs are approved
- os_contract: v1
- constraints: preserve unresolved design assumptions explicitly; do not redefine business scope; express the change method clearly enough for pre-code review; when a source target lacks current source structure findings in canonical knowledge, create them with `dotnet_change_analysis` and publish them through `knowledge_ontology_management` before freezing implementation-facing design; when structural design artifacts still imply unresolved behavior, route through the constraint-derivation pack before freezing implementation-facing design
- lifecycle:
  - startup: confirm planning outputs, source modification policy, and current source structure findings in canonical knowledge for each implementation target exist; if current source findings are missing, require `dotnet_change_analysis` plus `knowledge_ontology_management` publication; if unresolved structural design behavior remains, require constraint derivation before design closure
  - planning: define design scope, change-design boundaries, management rows, whether canonical source analysis is missing, and whether constraint derivation is required before implementation-facing decisions
  - execution: perform solution design drafting through `CAP-DSN-001`, create missing current source structure findings with `dotnet_change_analysis`, publish or refresh the canonical finding through `knowledge_ontology_management`, preserve the intended change method explicitly, and incorporate confirmed derivation outputs where structural ambiguity existed
  - monitoring_and_control: downgrade weak design assumptions or unclear change methods to `unknown`; stop if implementation-facing design would be frozen for a source target without canonical current source structure findings or where constraint derivation should have run
  - closure: finalize states and hand off the approved design package and design basis policy reference with unresolved items
- tags: `design`, `execution`, `implementation-preparation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501`
- knowledge_refs:
  - `../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701`
  - `../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711`
  - `../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../knowledge/source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0`
