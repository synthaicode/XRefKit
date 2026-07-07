<!-- xid: C5D6E7F8A9B0 -->
<a id="xid-C5D6E7F8A9B0"></a>

# Skill Meta: python_implementation_flow

- skill_id: `python_implementation_flow`
- summary: execute Python manufacturing activities through scoped realization and unit-level verification
- use_when: user asks to implement Python changes based on an approved design, explicitly bounded instructions, or concrete quality-feedback items
- input: approved design or equivalent scope instruction, design basis policy reference, test plan or test intent, test design basis reference when available, target files, applicable Python coding rules, configured test and static baseline commands, optional quality-feedback items
- output: Python code changes, unit test or unit-level verification results, static baseline evidence when configured, implementation basis design reference, quality-feedback response when applicable, uncertainty list, out-of-scope list, and handoff items for Python review or QA review
- maturity: `trial`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: `software_development`
- tuning: `Python`
- responsibility: `implementation`
- os_contract: v1
- constraints: do not change design policy; keep unresolved behavior explicit; implement only traced and approved differences by default; when coding would require guessing unresolved structural behavior from design artifacts, route through the constraint-derivation pack before implementation; handle concrete in-scope quality feedback when no tradeoff exists among active findings; keep Python-specific implementation evidence tied to configured tests and static baseline commands where available
- lifecycle:
  - startup: confirm approved scope, reviewed test basis or test intent, target files, Python coding rules, and configured validation commands exist; stop if the task still depends on unresolved structural behavior that should be derived before coding
  - planning: define implementation, test, and static-baseline targets from design and reviewed test evidence; if structural behavior remains implicit, route back through constraint derivation before coding
  - execution: perform Python implementation and unit-level verification against traced and approved differences only after required derivation or design confirmation exists
  - monitoring_and_control: downgrade weak completion claims or untraced diffs to `unknown`; preserve out-of-scope reasons; stop if coding starts to choose missing design behavior locally
  - closure: finalize states and hand off code changes, validation evidence, and implementation basis to Python review or QA review
- tags: `python`, `implementation`, `manufacturing`, `engineering`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=implementation_assumption_gap_handling; bind=7A2F4C8D1501
  - name=temporary_traceability_comment_rule; bind=22E4C7AC7063
  - name=quality_feedback_return_rules; bind=7A2F4C8D1901
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=python_review_spec; bind=A9B7C6D5E4F1
- observation_refs:
  - `../../observations/2026-07-07_session_python_skill_authoring.md`
