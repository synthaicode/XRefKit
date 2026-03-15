<!-- xid: 60B1B69B0984 -->
<a id="xid-60B1B69B0984"></a>

# Skill Meta: manufacturing_self_check

- skill_id: `manufacturing_self_check`
- summary: perform manufacturing-group self-check against approved design before external QA review
- use_when: implementation and unit testing are complete and manufacturing needs an internal alignment check
- input: implemented code, approved design, unit test results, coding rules
- output: self-check result, design-alignment findings, unresolved list
- constraints: internal manufacturing check only; does not replace quality-group review
- lifecycle:
  - startup: confirm implemented code, design evidence, and unit-test evidence exist
  - planning: define self-check targets and management rows
  - execution: run `CAP-MFG-004`
  - monitoring_and_control: downgrade unsupported alignment claims to `unknown`
  - closure: finalize states and hand off results to quality review
- tags: `manufacturing`, `self-check`, `quality`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/manufacturing/120_cap_mfg_004_manufacturing_self_check.md#xid-6F5A9C1B4401`
  - ../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101 
  - `../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201`

