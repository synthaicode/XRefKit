<!-- xid: 8F312706C5F0 -->
<a id="xid-8F312706C5F0"></a>

# Skill Meta: review_report_composition

- skill_id: `review_report_composition`
- summary: compose review Skill outputs into decision-readable reports without changing the detector's technical judgment
- use_when: a review Skill has produced findings, category results, evidence, or a draft report and the result must be expressed for human review, especially when category rows, not-applicable basis, required-input results, severity wording, or handoff wording are unclear
- input: detector Skill output, category results, findings, evidence references, usage premise, optional draft report
- output: composed review report, category matrix expression check, finding expression check, required-input result table when applicable, composition issues, and handoff items back to the detector when evidence is insufficient
- maturity: `draft`
- execution_mode: `direct`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: `documentation`
- tuning: `review_report`
- responsibility: report composition
- os_contract: v1
- constraints: do not invent findings; do not suppress detector categories by headline purpose; do not change severity or technical judgment unless the detector output itself provides evidence; do not put implementation-specific examples in this Skill; use expression slots and evidence references rather than whitelist-like wording
- lifecycle:
  - startup: confirm detector output, report purpose, scope, and evidence references
  - planning: identify report sections, category rows, finding rows, and handoff rows that need composition
  - execution: compose the report while preserving detector judgments and making the decision basis visible
  - monitoring_and_control: flag missing evidence slots, purpose-biased category suppression, summary-only rows, and unsupported severity wording
  - closure: return composed report plus unresolved composition issues or detector handoffs
- tags: `review`, `report`, `composition`, `quality`
- skill_doc: `./SKILL.md`
