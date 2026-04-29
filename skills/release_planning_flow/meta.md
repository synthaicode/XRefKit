<!-- xid: 22DE60C2BBCB -->
<a id="xid-22DE60C2BBCB"></a>

# Skill Meta: release_planning_flow

- skill_id: `release_planning_flow`
- summary: execute release-planning business activities through reusable release-material, release-procedure, release-confirmation, signal-specification, response-structuring, and readiness-evaluation capabilities
- use_when: user needs release-planning work after manufacturing and testing
- input: manufacturing outputs, requirements, design materials, optional performance data
- output: release plan draft, release procedure draft, release confirmation procedure draft, rollback procedure draft, monitoring specification, event-response procedure draft, operational readiness result
- execution_mode: `local_default`
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
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/operations/100_cap_ops_001_release_plan_draft_creation.md#xid-9715BACE7EB8`
  - `../../capabilities/operations/110_cap_ops_002_monitoring_design.md#xid-316B0FB4493C`
  - `../../capabilities/operations/120_cap_ops_003_event_response_procedure_draft.md#xid-6DA033B45D93`
  - `../../capabilities/operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
