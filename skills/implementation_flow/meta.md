<!-- xid: 1832ADA8D6D4 -->
<a id="xid-1832ADA8D6D4"></a>

# Skill Meta: implementation_flow

- skill_id: `implementation_flow`
- summary: execute manufacturing business activities through reusable scoped realization and unit-level verification capabilities
- use_when: user asks to implement changes based on an approved design or explicitly bounded instructions
- input: approved design or equivalent scope instruction, target files, applicable coding rules, optional test viewpoints
- output: code changes, unit test results, uncertainty list, out-of-scope list
- constraints: do not change design policy; keep unresolved items explicit
- lifecycle:
  - startup: confirm approved scope, target files, and coding rules exist
  - planning: define implementation and test targets and management rows
  - execution: perform implementation and unit test execution through `CAP-MFG-001 -> CAP-MFG-002`
  - monitoring_and_control: downgrade weak completion claims to `unknown`; preserve out-of-scope reasons
  - closure: finalize states and hand off results to QA review
- tags: `implementation`, `manufacturing`, `engineering`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/manufacturing/100_cap_mfg_001_implementation.md#xid-1A12C5C61269`
  - `../../capabilities/manufacturing/110_cap_mfg_002_unit_test_execution.md#xid-55CC9027ACAD`
- knowledge_refs: none
