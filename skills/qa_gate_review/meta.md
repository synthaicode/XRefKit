<!-- xid: 6655C6BD6238 -->
<a id="xid-6655C6BD6238"></a>

# Skill Meta: qa_gate_review

- skill_id: `qa_gate_review`
- summary: execute evidence-based QA across specification, performance, security, and license domains
- use_when: user asks for QA review against design, performance, security, or license expectations
- input: target code paths, design evidence, coding rules, optional performance evidence, optional dependency provenance
- output: per-domain review results, findings with evidence, uncertainty list
- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit
- lifecycle:
  - startup: confirm domain evidence exists for specification, performance, security, and license review
  - planning: define review domains, targets, and management rows
  - execution: run `CAP-QA-001`, `CAP-QA-006`, `CAP-QA-007`, and `CAP-QA-008`, with `CAP-QA-005` when attribute analysis is required
  - monitoring_and_control: downgrade unsupported conclusions to `unknown`
  - closure: finalize states and return per-domain findings with evidence
- tags: `qa`, `review`, `quality`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/quality/100_cap_qa_001_code_review.md#xid-7E9CCEBEDA2D`
  - `../../capabilities/quality/140_cap_qa_006_performance_risk_review.md#xid-5A1C2F0E5506`
  - `../../capabilities/quality/150_cap_qa_007_security_review.md#xid-5A1C2F0E5507`
  - `../../capabilities/quality/160_cap_qa_008_license_compliance_check.md#xid-5A1C2F0E5508`
- knowledge_refs: none

