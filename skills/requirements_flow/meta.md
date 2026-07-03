<!-- xid: 6720268498FD -->
<a id="xid-6720268498FD"></a>

# Skill Meta: requirements_flow

- skill_id: `requirements_flow`
- summary: execute requirements business activities through reusable requirement and performance-constraint structuring capabilities
- use_when: user needs requirement drafting after investigation and estimation
- input: confirmed assumptions, change target list, test viewpoints, request, optional performance constraints
- output: requirement draft, performance requirement definition, load-test draft plan, unresolved list
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute requirements business activities through reusable requirement and performance-constraint structuring capabilities
- responsibility: user needs requirement drafting after investigation and estimation
- os_contract: v1
- constraints: draft only; do not approve final requirements; preserve change reason, change requirement, and change specification as explicit difference artifacts
- lifecycle:
  - startup: confirm confirmed assumptions and requirement inputs exist
  - planning: define requirement areas, change-difference structure, and management rows
  - execution: perform requirement draft creation and performance requirement definition through `CAP-REQ-001 -> CAP-REQ-002` while preserving change reason and specification mapping
  - monitoring_and_control: downgrade weak requirement claims or unclear delta statements to `unknown`
  - closure: finalize states and hand off unresolved requirement items with traceable difference statements
- tags: `requirements`, `planning`, `analysis`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701`
  - `../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711`
