<!-- xid: 22DE60C2BBCB -->
<a id="xid-22DE60C2BBCB"></a>

# Skill Meta: release_planning_flow

- skill_id: `release_planning_flow`
- summary: execute release-planning business activities through reusable release-material, release-procedure, release-confirmation, signal-specification, response-structuring, and readiness-evaluation capabilities
- use_when: user needs release-planning work after manufacturing and testing
- input: manufacturing outputs, requirements, design materials, optional performance data
- output: release plan draft, release procedure draft, release confirmation procedure draft, rollback procedure draft, monitoring specification, event-response procedure draft, operational readiness result
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute release-planning business activities through reusable release-material, release-procedure, release-confirmation, signal-specification, response-structuring, and readiness-evaluation capabilities
- responsibility: user needs release-planning work after manufacturing and testing
- os_contract: v1
- constraints: do not approve release timing or final go or no-go
- lifecycle:
  - startup: confirm manufacturing outputs and release-planning evidence exist
  - planning: define release-planning scope and management rows
  - execution: perform release plan drafting, monitoring design, event-response drafting, and operational readiness gate work through `CAP-OPS-001 -> CAP-OPS-002 -> CAP-OPS-003 -> CAP-OPS-004`
  - monitoring_and_control: downgrade unsupported readiness conclusions to `unknown`
  - closure: finalize states and hand off release materials to CAB
- tags: `operations`, `release`, `planning`
- skill_doc: `./SKILL.md`
- knowledge_refs:
