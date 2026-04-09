<!-- xid: 3C06EF778A20 -->
<a id="xid-3C06EF778A20"></a>

# Skill Meta: investigation_flow

- skill_id: `investigation_flow`
- summary: execute the investigation workflow from service catalog analysis through change-target summary using reusable investigation capabilities
- use_when: user needs impact investigation before estimation or design
- input: request, optional service candidates, optional service catalog path, optional repository or document paths
- output: in-scope service list, out-of-scope service list with reasons, change viewpoints, test viewpoints, change target list, uncertainty list
- execution_mode: `local_default`
- guard_policy: `required`
- constraints: do not decide design or implementation policy; record unknowns explicitly
- lifecycle:
  - startup: confirm request, service catalog, analysis targets, and coverage checklist exist
  - planning: define investigation targets, coverage areas, and management rows
  - execution: run service catalog analysis, source and dependency analysis, and change-target summarization through `CAP-INV-001 -> CAP-INV-002 -> CAP-INV-003`
  - monitoring_and_control: treat unrecorded coverage areas as leaks; downgrade weak evidence to `unknown`
  - closure: finalize states and hand off unresolved or out-of-scope items
- tags: `investigation`, `scope`, `planning`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/investigation/100_cap_inv_001_service_catalog_analysis.md#xid-867B78FF702F`
  - `../../capabilities/investigation/110_cap_inv_002_source_dependency_analysis.md#xid-E994FCDA8CD1`
  - `../../capabilities/investigation/120_cap_inv_003_change_target_summary.md#xid-6AB17163C9BF`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/investigation/100_investigation_coverage_checklist.md#xid-91E2A7C56101`
