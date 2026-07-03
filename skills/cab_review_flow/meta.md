<!-- xid: AE3979CD83C0 -->
<a id="xid-AE3979CD83C0"></a>

# Skill Meta: cab_review_flow

- skill_id: `cab_review_flow`
- summary: execute CAB business activities through reusable quality, operational-readiness, and value-alignment evaluation capabilities
- use_when: user needs CAB-style evaluation before release confirmation
- input: release plan materials, manufacturing outputs, requirement and design evidence, value and constraint definitions
- output: quality-gate result, operational readiness result, value-gate result, unresolved list
- maturity: `draft`
- execution_mode: `subagent_preferred`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute CAB business activities through reusable quality, operational-readiness, and value-alignment evaluation capabilities
- responsibility: user needs CAB-style evaluation before release confirmation
- os_contract: v1
- constraints: evaluate only; do not make final release decision
- lifecycle:
  - startup: confirm CAB evidence exists
  - planning: define gate scope and management rows
  - execution: perform release plan suitability review, operational readiness gate work, and value-constraint fit evaluation through `CAP-QA-003 -> CAP-OPS-004 -> CAP-BIZ-001`
  - monitoring_and_control: downgrade unsupported judgments to `unknown`
  - closure: finalize states and hand off the three gate results to the decision layer
- tags: `cab`, `review`, `release`
- skill_doc: `./SKILL.md`
- knowledge_refs:
