<!-- xid: 1B28D96E4C11 -->
<a id="xid-1B28D96E4C11"></a>

# Skill Meta: design_flow

- skill_id: `design_flow`
- summary: execute design business activity through reusable solution-design capability
- use_when: user needs implementation-ready design after planning outputs are approved
- input: approved requirements, work plan, source modification policy, data change policy, planning basis source list
- output: approved design, target paths, source modification design, data change design, design basis policy reference
- constraints: preserve unresolved design assumptions explicitly; do not redefine business scope
- lifecycle:
  - startup: confirm planning outputs and source modification policy exist
  - planning: define design scope and management rows
  - execution: perform solution design drafting through `CAP-DSN-001`
  - monitoring_and_control: downgrade weak design assumptions to `unknown`
  - closure: finalize states and hand off the approved design package and design basis policy reference with unresolved items
- tags: `design`, `execution`, `implementation-preparation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501`
- knowledge_refs: none
