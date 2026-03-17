<!-- xid: AE3979CD83C0 -->
<a id="xid-AE3979CD83C0"></a>

# Skill Meta: cab_review_flow

- skill_id: `cab_review_flow`
- summary: execute CAB business activities through reusable quality, operational-readiness, and value-alignment evaluation capabilities
- use_when: user needs CAB-style evaluation before release confirmation
- input: release plan materials, manufacturing outputs, requirement and design evidence, value and constraint definitions
- output: quality-gate result, operational readiness result, value-gate result, unresolved list
- constraints: evaluate only; do not make final release decision
- lifecycle:
  - startup: confirm CAB evidence exists
  - planning: define gate scope and management rows
  - execution: perform release plan suitability review, operational readiness gate work, and value-constraint fit evaluation through `CAP-QA-003 -> CAP-OPS-004 -> CAP-BIZ-001`
  - monitoring_and_control: downgrade unsupported judgments to `unknown`
  - closure: finalize states and hand off the three gate results to the decision layer
- tags: `cab`, `review`, `release`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/quality/120_cap_qa_003_release_plan_suitability_review.md#xid-93E53EF38700`
  - `../../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3`
  - `../../capabilities/business/100_cap_biz_001_value_constraint_fit_evaluation.md#xid-837CDB1183C9`
- knowledge_refs: none
