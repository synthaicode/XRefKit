<!-- xid: 60B1B69B0984 -->
<a id="xid-60B1B69B0984"></a>

# Skill Meta: manufacturing_self_check

- skill_id: `manufacturing_self_check`
- summary: execute manufacturing self-check business activity through reusable design-alignment self-evaluation capability
- use_when: code, DB, or persistence implementation and unit testing are complete and manufacturing needs an internal alignment check
- input: implemented code, DB manufacturing artifacts when in scope, approved design, unit test results, coding rules
- output: self-check result, design-alignment findings for code and DB manufacturing results, unresolved list
- maturity: `draft`
- execution_mode: `subagent_preferred`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute manufacturing self-check business activity through reusable design-alignment self-evaluation capability
- responsibility: code, DB, or persistence implementation and unit testing are complete and manufacturing needs an internal alignment check
- os_contract: v1
- constraints: internal manufacturing check only; does not replace quality-group review; when code, DB artifacts, tests, and design evidence together risk context overflow, split self-check execution into subagents by artifact family or target boundary and merge results explicitly
- lifecycle:
  - startup: confirm implemented code, DB manufacturing artifacts when in scope, design evidence, and unit-test evidence exist
  - planning: define self-check targets including DB manufacturing outputs, management rows, and subagent split when evidence breadth risks context overflow
  - execution: perform manufacturing self-check through `CAP-MFG-004`, comparing code and DB manufacturing artifacts against approved design evidence
  - monitoring_and_control: downgrade unsupported alignment claims to `unknown`
  - closure: finalize states and hand off results to quality review
- tags: `manufacturing`, `self-check`, `quality`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=csharp_quality_review_criteria; bind=8C4D2A7E5101
  - name=metrics_definition; bind=7A2F4C8D1201

