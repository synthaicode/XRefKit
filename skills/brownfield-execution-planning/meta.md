<!-- xid: 9E4B7C2A6101 -->
<a id="xid-9E4B7C2A6101"></a>

# Skill Meta: brownfield_execution_planning

- skill_id: `brownfield_execution_planning`
- summary: create an evidence-backed execution work plan for a brownfield change before investigation, implementation, and change-based testing
- use_when: a brownfield change needs an explicit execution plan covering scope, dependencies, existing data, test suite, evidence, gates, and handoff
- input: approved or bounded change request, upstream items, current-system evidence, service/data-flow Knowledge, constraints, decision owners, and known test or data artifacts
- output: execution work plan, investigation scope, target and dependency map, existing-data investigation plan, pre-change test-suite plan, evidence plan, stop conditions, gates, owners, unknowns, and handoff package
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: brownfield_execution_planning
- responsibility: prepare a traceable and human-reviewable execution plan before brownfield change work begins
- os_contract: v1
- constraints: do not approve requirements or release decisions; do not infer missing behavior, service ownership, data rules, or test acceptance; do not hide unverified scope; do not execute production changes; keep tool preparation in planning and execution in the assigned phase
- lifecycle:
  - startup: confirm upstream change, target service, evidence, decision owners, and Knowledge candidates
  - planning: define scope, work items, dependencies, data/test/evidence policies, gates, and handoffs
  - monitoring_and_control: downgrade unsupported mappings or missing inputs to `unknown` and stop material planning gaps
  - closure: verify every in-scope item has an owner, evidence target, next action, and phase handoff
- tags: `brownfield`, `planning`, `execution-plan`, `impact-analysis`, `regression-testing`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=service_catalog; bind=7A2F4C8D2201
  - name=service_interaction_data_flow; bind=7A2F4C8D2301
  - name=xddp_basics; bind=7A2F4C8D1701
