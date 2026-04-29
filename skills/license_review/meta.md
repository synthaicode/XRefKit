<!-- xid: 8C5AA4CAFF4D -->
<a id="xid-8C5AA4CAFF4D"></a>

# Skill Meta: license_review

- skill_id: `license_review`
- summary: review dependency and provenance evidence for license compliance risks
- use_when: user needs focused license validation
- input: package list, dependency information, provenance information
- output: license review result, incompatible or unknown license findings, unresolved list
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
- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit
- lifecycle:
  - startup: confirm dependency or provenance evidence exists
  - planning: define review targets and management rows
  - execution: run `CAP-QA-008`
  - monitoring_and_control: downgrade unsupported conclusions to `unknown`
  - closure: finalize review results and preserve unresolved items
- tags: `qa`, `license`, `csharp`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/quality/160_cap_qa_008_license_compliance_check.md#xid-5A1C2F0E5508`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101`
