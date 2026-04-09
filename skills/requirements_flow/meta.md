<!-- xid: 6720268498FD -->
<a id="xid-6720268498FD"></a>

# Skill Meta: requirements_flow

- skill_id: `requirements_flow`
- summary: execute requirements business activities through reusable requirement and performance-constraint structuring capabilities
- use_when: user needs requirement drafting after investigation and estimation
- input: confirmed assumptions, change target list, test viewpoints, request, optional performance constraints
- output: requirement draft, performance requirement definition, load-test draft plan, unresolved list
- execution_mode: `local_default`
- guard_policy: `required`
- constraints: draft only; do not approve final requirements; preserve change reason, change requirement, and change specification as explicit difference artifacts
- lifecycle:
  - startup: confirm confirmed assumptions and requirement inputs exist
  - planning: define requirement areas, change-difference structure, and management rows
  - execution: perform requirement draft creation and performance requirement definition through `CAP-REQ-001 -> CAP-REQ-002` while preserving change reason and specification mapping
  - monitoring_and_control: downgrade weak requirement claims or unclear delta statements to `unknown`
  - closure: finalize states and hand off unresolved requirement items with traceable difference statements
- tags: `requirements`, `planning`, `analysis`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/requirements/100_cap_req_001_requirement_draft_creation.md#xid-BC408337F2A2`
  - `../../capabilities/requirements/110_cap_req_002_performance_requirement_definition.md#xid-D67FAD650F8C`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701`
  - `../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711`
