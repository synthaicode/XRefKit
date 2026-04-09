<!-- xid: BB7FC6766830 -->
<a id="xid-BB7FC6766830"></a>

# Skill Meta: management_table_control

- skill_id: `management_table_control`
- summary: inspect management-table state and produce closure or return actions
- use_when: user needs leak detection, closure confirmation, or out-of-scope escalation handling
- input: management table, optional metrics log, optional out-of-scope list
- output: leak detection result, closure confirmation, escalation record when needed
- execution_mode: `local_default`
- guard_policy: `required`
- constraints: control state only; do not alter judgment content or accept risk implicitly
- lifecycle:
  - startup: confirm management table and control evidence exist
  - planning: define control scope and management rows
  - execution: run `CAP-QA-004 -> CAP-MGT-003`
  - monitoring_and_control: re-check low-confidence rows and preserve escalation reasons
  - closure: confirm closure readiness or return instructions with escalation records
- tags: `management`, `qa`, `control`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/quality/110_cap_qa_004_management_table_check.md#xid-AFEB172B97D8`
  - `../../capabilities/management/120_cap_mgt_003_out_of_scope_escalation.md#xid-1E3B2AA5B328`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/organization/110_management_table_schema.md#xid-7A2F4C8D1101`
  - `../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201`
