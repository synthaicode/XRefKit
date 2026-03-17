<!-- xid: 22DE60C2BBCB -->
<a id="xid-22DE60C2BBCB"></a>

# Skill Meta: release_planning_flow

- skill_id: `release_planning_flow`
- summary: execute release-planning business activities through reusable release-material, signal-specification, response-structuring, and readiness-evaluation capabilities
- use_when: user needs release-planning work after manufacturing and testing
- input: manufacturing outputs, requirements, design materials, optional performance data
- output: release plan draft, monitoring specification, event-response procedure draft, operational readiness result
- constraints: do not approve release timing or final go or no-go
- lifecycle:
  - startup: confirm manufacturing outputs and release-planning evidence exist
  - planning: define release-planning scope and management rows
  - execution: perform release plan drafting, monitoring design, event-response drafting, and operational readiness gate work through `CAP-OPS-001 -> CAP-OPS-002 -> CAP-OPS-003 -> CAP-OPS-004`
  - monitoring_and_control: downgrade unsupported readiness conclusions to `unknown`
  - closure: finalize states and hand off release materials to CAB
- tags: `operations`, `release`, `planning`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/operations/100_cap_ops_001_release_plan_draft_creation.md#xid-9715BACE7EB8`
  - `../../capabilities/operations/110_cap_ops_002_monitoring_design.md#xid-316B0FB4493C`
  - `../../capabilities/operations/120_cap_ops_003_event_response_procedure_draft.md#xid-6DA033B45D93`
  - `../../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3`
- knowledge_refs: none
