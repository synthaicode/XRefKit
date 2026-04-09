<!-- xid: 1832ADA8D6D4 -->
<a id="xid-1832ADA8D6D4"></a>

# Skill Meta: implementation_flow

- skill_id: `implementation_flow`
- summary: execute manufacturing business activities through reusable scoped realization and unit-level verification capabilities
- use_when: user asks to implement changes based on an approved design or explicitly bounded instructions
- input: approved design or equivalent scope instruction, design basis policy reference, test plan, test design, test design basis policy reference, test-item requirement traceability reference, manufacturing test review result, target files, applicable coding rules, optional test viewpoints
- output: code changes, unit test results, unit test execution basis reference, implementation basis design reference, uncertainty list, out-of-scope list
- execution_mode: `local_default`
- guard_policy: `required`
- constraints: do not change design policy; keep unresolved items explicit
- lifecycle:
  - startup: confirm approved scope, reviewed test package, target files, and coding rules exist
  - planning: define implementation and test targets and management rows from design and reviewed test design
  - execution: perform implementation and unit test execution through `CAP-MFG-001 -> CAP-MFG-002`
  - monitoring_and_control: downgrade weak completion claims to `unknown`; preserve out-of-scope reasons
  - closure: finalize states and hand off results and implementation basis design reference to QA review
- tags: `implementation`, `manufacturing`, `engineering`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/manufacturing/100_cap_mfg_001_implementation.md#xid-1A12C5C61269`
  - `../../capabilities/manufacturing/110_cap_mfg_002_unit_test_execution.md#xid-55CC9027ACAD`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
