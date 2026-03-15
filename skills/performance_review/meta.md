<!-- xid: C37C910B8E0F -->
<a id="xid-C37C910B8E0F"></a>

# Skill Meta: performance_review

- skill_id: `performance_review`
- summary: review C# code and evidence for performance risks
- use_when: user needs focused performance validation
- input: target code, performance evidence or assumptions
- output: performance review result, bottleneck findings, unresolved list
- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit
- lifecycle:
  - startup: confirm target and performance evidence exist
  - planning: define review targets and management rows
  - execution: run `CAP-QA-006`
  - monitoring_and_control: downgrade unsupported conclusions to `unknown`
  - closure: finalize review results and preserve unresolved items
- tags: `qa`, `performance`, `csharp`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/quality/140_cap_qa_006_performance_risk_review.md#xid-5A1C2F0E5506`
- knowledge_refs:
  - `../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101`
