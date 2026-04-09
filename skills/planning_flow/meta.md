<!-- xid: E3F2F376922F -->
<a id="xid-E3F2F376922F"></a>

# Skill Meta: planning_flow

- skill_id: `planning_flow`
- summary: execute planning business activity through reusable work-and-policy planning capability grounded in domain knowledge and current-source findings
- use_when: user needs planning after requirements are approved
- input: approved requirements, change target list, current source structure findings, domain knowledge references
- output: work plan, source modification policy, data change policy, data correction tool policy, test policy, test tool policy, release policy, planning basis source list
- guard_policy: `required`
- constraints: draft only; do not finalize priority or resource allocation
- lifecycle:
  - startup: confirm approved requirements, current source findings, and domain knowledge references exist
  - planning: define planning scope, policy targets, and management rows from domain knowledge and current-source findings
  - execution: perform work planning and policy drafting through `CAP-PLN-001`
  - monitoring_and_control: downgrade weak planning assumptions and unsupported source-structure claims to `unknown`
  - closure: finalize states and hand off planning outputs and planning basis source list with unresolved items
- tags: `planning`, `execution`, `policy`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/planning/100_cap_pln_001_task_decomposition_plan_draft.md#xid-F5193313AB79`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001`
  - `../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002`
  - `../../knowledge/csharp/110_custom_framework_analysis_criteria.md#xid-30E6A4F6F3AB`
  - `../../knowledge/operations/100_ipa_release_activity_catalog.md#xid-7B3E5D1A6101`
