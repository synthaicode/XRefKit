<!-- xid: 6720268498FD -->
<a id="xid-6720268498FD"></a>

# Skill Meta: requirements_flow

- skill_id: `requirements_flow`
- summary: produce requirement drafts and performance requirements from confirmed assumptions
- use_when: user needs requirement drafting after investigation and estimation
- input: confirmed assumptions, change target list, test viewpoints, request, optional performance constraints
- output: requirement draft, performance requirement definition, load-test draft plan, unresolved list
- constraints: draft only; do not approve final requirements
- lifecycle:
  - startup: confirm confirmed assumptions and requirement inputs exist
  - planning: define requirement areas and management rows
  - execution: run `CAP-REQ-001 -> CAP-REQ-002`
  - monitoring_and_control: downgrade weak requirement claims to `unknown`
  - closure: finalize states and hand off unresolved requirement items
- tags: `requirements`, `planning`, `analysis`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/requirements/100_cap_req_001_requirement_draft_creation.md#xid-BC408337F2A2`
  - `../../capabilities/requirements/110_cap_req_002_performance_requirement_definition.md#xid-D67FAD650F8C`
- knowledge_refs: none
