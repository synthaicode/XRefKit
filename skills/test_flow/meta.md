<!-- xid: 2D7B0A661990 -->
<a id="xid-2D7B0A661990"></a>

# Skill Meta: test_flow

- skill_id: `test_flow`
- summary: execute test-planning, test-item structuring, integration/regression test design, and manufacturing-side test-method review
- use_when: user needs a reviewed test package from planning outputs, requirements, and design evidence
- input: approved requirements, work plan, test policy, test tool policy, approved design, design-to-test input package, XDDP traceability matrix or rows from the approved design package, planning basis source list, selected domain/environment test tool knowledge XIDs when available
- output: test plan with selected test tool basis, test design, requirement and design traceability reference, integration regression test design, manufacturing test review result, unresolved tool gaps
- maturity: `draft`
- execution_mode: `subagent_preferred`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute test-planning, test-item structuring, integration/regression test design, and manufacturing-side test-method review
- responsibility: user needs a reviewed test package from planning outputs, requirements, and design evidence
- os_contract: v1
- constraints: do not redefine requirement intent, business scope, design intent, final release judgment, or domain/environment test tool facts; derive test scope from the approved design's design-to-test input package and XDDP traceability rows rather than broad design prose; select test tools from planning test tool policy and available domain/environment test tool knowledge, and record unsupported tool assumptions as unknown
- lifecycle:
  - startup: confirm requirements, planning outputs, test policy, test tool policy, approved design, design-to-test input package, XDDP traceability rows, and available domain/environment test tool catalog metadata exist when tool selection is needed
  - planning: define test scope, tool-selection scope, and management rows from the design-to-test input package and selected domain/environment test tool knowledge
  - execution: perform `CAP-DSN-004 -> CAP-DSN-002 -> CAP-DSN-003 -> CAP-MFG-003` and record requirement/design/tool traceability for each test item
  - monitoring_and_control: downgrade unsupported test assumptions, tool assumptions, or uncovered design-to-test rows to `unknown`
  - closure: finalize states and hand off the reviewed test package with requirement/design/tool traceability
- tags: `test`, `design`, `manufacturing`, `traceability`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=test_design_criteria; bind=8C4D2A7E5102
- knowledge_inputs:
  - name=domain_environment_test_tool_catalog; required=false; accepts=test-tool-catalog,environment-test-tool-policy,domain-test-automation-map,local-test-runner-guide; purpose=select-test-tools-for-plan-and-test-design
