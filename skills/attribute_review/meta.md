<!-- xid: 66BCDDE04992 -->
<a id="xid-66BCDDE04992"></a>

# Skill Meta: attribute_review

- skill_id: `attribute_review`
- summary: review C# attributes for necessity, value correctness, and usage correctness
- use_when: user needs focused validation of C# attributes
- input: target C# code, design evidence, coding rules
- output: attribute review result, invalid usage findings, unresolved list
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
  - startup: confirm code and evidence exist
  - planning: define review targets and management rows
  - execution: run `CAP-QA-005`
  - monitoring_and_control: downgrade unsupported conclusions to `unknown`
  - closure: finalize review results and preserve unresolved items
- tags: `qa`, `attribute`, `csharp`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/quality/130_cap_qa_005_attribute_usage_review.md#xid-5A1C2F0E5505`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101`
