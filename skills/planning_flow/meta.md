<!-- xid: E3F2F376922F -->
<a id="xid-E3F2F376922F"></a>

# Skill Meta: planning_flow

- skill_id: `planning_flow`
- summary: execute planning business activity through reusable work-decomposition capability
- use_when: user needs planning after requirements are approved
- input: approved requirements, change target list
- output: task list, dependencies, execution order, effort estimate, group assignment draft
- constraints: draft only; do not finalize priority or resource allocation
- lifecycle:
  - startup: confirm approved requirements and change targets exist
  - planning: define decomposition scope and management rows
  - execution: perform task decomposition and plan drafting through `CAP-PLN-001`
  - monitoring_and_control: downgrade weak planning assumptions to `unknown`
  - closure: finalize states and hand off the plan draft with unresolved items
- tags: `planning`, `execution`, `decomposition`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/planning/100_cap_pln_001_task_decomposition_plan_draft.md#xid-F5193313AB79`
- knowledge_refs: none
