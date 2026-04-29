<!-- xid: 2D7B0A661990 -->
<a id="xid-2D7B0A661990"></a>

# Skill Meta: test_flow

- skill_id: `test_flow`
- summary: execute test-planning, test-item structuring, integration/regression test design, and manufacturing-side test-method review
- use_when: user needs a reviewed test package from planning outputs, requirements, and design evidence
- input: approved requirements, work plan, test policy, approved design, planning basis source list
- output: test plan, test design, requirement traceability reference, integration regression test design, manufacturing test review result
- execution_mode: `subagent_preferred`
- guard_policy: `required`
- os_contract:
  - version: `1`
  - worklist_policy: `required`
  - execution_role: `required`
  - check_role: `required`
  - logging_policy: `session_required`
  - judgment_log_policy: `required_when_non_trivial`
  - unknown_risk_policy: `explicit`
  - closure_gate: `required`
  - handoff_policy: `explicit`
- constraints: do not redefine requirement intent, business scope, or final release judgment
- lifecycle:
  - startup: confirm requirements, planning outputs, and design evidence exist
  - planning: define test scope and management rows
  - execution: perform `CAP-DSN-004 -> CAP-DSN-002 -> CAP-DSN-003 -> CAP-MFG-003`
  - monitoring_and_control: downgrade unsupported test assumptions to `unknown`
  - closure: finalize states and hand off the reviewed test package
- tags: `test`, `design`, `manufacturing`, `traceability`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/design/130_cap_dsn_004_test_plan_structuring.md#xid-6C1A2D9F4504`
  - `../../capabilities/design/110_cap_dsn_002_test_design_structuring.md#xid-6C1A2D9F4502`
  - `../../capabilities/design/120_cap_dsn_003_integration_regression_test_design_structuring.md#xid-6C1A2D9F4503`
  - `../../capabilities/manufacturing/130_cap_mfg_003_test_method_review.md#xid-55CC9027ACAE`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102`
