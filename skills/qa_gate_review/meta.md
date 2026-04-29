<!-- xid: 6655C6BD6238 -->
<a id="xid-6655C6BD6238"></a>

# Skill Meta: qa_gate_review

- skill_id: `qa_gate_review`
- summary: execute evidence-based QA across specification, performance, security, and license domains
- use_when: user asks for QA review against design, performance, security, or license expectations
- input: target code paths, design evidence, coding rules, optional performance evidence, optional dependency provenance
- output: per-domain review results, findings with evidence, uncertainty list
- execution_mode: `subagent_required`
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
- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit; review the intended difference, not the whole implementation by default
- lifecycle:
  - startup: confirm domain evidence exists for specification, performance, security, and license review
  - planning: define review domains, delta-bounded targets, management rows, and subagent split when scope-separated parallel review is safe
  - execution: run `CAP-QA-001`, `CAP-QA-006`, `CAP-QA-007`, and `CAP-QA-008`, with `CAP-QA-005` when attribute analysis is required, while checking delta appropriateness against traced intent
  - monitoring_and_control: downgrade unsupported conclusions or unclear delta coverage to `unknown`
  - closure: finalize states, return per-domain findings with evidence, and hand off target-scope cleanup when code review completion is declared
- tags: `qa`, `review`, `quality`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/quality/100_cap_qa_001_code_review.md#xid-7E9CCEBEDA2D`
  - `../../capabilities/quality/140_cap_qa_006_performance_risk_review.md#xid-5A1C2F0E5506`
  - `../../capabilities/quality/150_cap_qa_007_security_review.md#xid-5A1C2F0E5507`
  - `../../capabilities/quality/160_cap_qa_008_license_compliance_check.md#xid-5A1C2F0E5508`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/organization/151_temporary_traceability_comment_rule.md#xid-22E4C7AC7063`
  - `../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701`
  - `../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711`

