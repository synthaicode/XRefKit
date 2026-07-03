<!-- xid: 3C06EF778A20 -->
<a id="xid-3C06EF778A20"></a>

# Skill Meta: investigation_flow

- skill_id: `investigation_flow`
- summary: execute the investigation workflow from service catalog analysis through change-target summary using reusable investigation capabilities
- use_when: user needs impact investigation before estimation or design
- input: request, optional service candidates, optional service catalog path, optional repository or document paths
- output: in-scope service list, out-of-scope service list with reasons, change viewpoints, test viewpoints, change target list, uncertainty list
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute the investigation workflow from service catalog analysis through change-target summary using reusable investigation capabilities
- responsibility: user needs impact investigation before estimation or design
- os_contract: v1
- constraints: do not decide design or implementation policy; record unknowns explicitly; preserve requested difference and impacted-target discovery explicitly
- lifecycle:
  - startup: confirm request, service catalog, analysis targets, and coverage checklist exist
  - planning: define investigation targets, requested difference, coverage areas, and management rows
  - execution: run service catalog analysis, source and dependency analysis, and change-target summarization through `CAP-INV-001 -> CAP-INV-002 -> CAP-INV-003`, including selective spec-out when needed
  - monitoring_and_control: treat unrecorded coverage areas as leaks and downgrade weak impact evidence to `unknown`
  - closure: finalize states and hand off unresolved or out-of-scope items with impacted-target notes
- tags: `investigation`, `scope`, `planning`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701`
  - `../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711`
  - `../../knowledge/investigation/100_investigation_coverage_checklist.md#xid-91E2A7C56101`
