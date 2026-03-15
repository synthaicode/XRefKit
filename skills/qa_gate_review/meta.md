<!-- xid: 6655C6BD6238 -->
<a id="xid-6655C6BD6238"></a>

# Skill Meta: qa_gate_review

- skill_id: `qa_gate_review`
- summary: execute evidence-based code review after implementation or unit testing
- use_when: user asks for code review against design and local rules
- input: target code paths, design evidence, coding rules
- output: pass or fail judgment, findings with evidence, uncertainty list
- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit
- lifecycle:
  - startup: confirm code, design evidence, and coding rules exist
  - planning: define review targets and management rows
  - execution: run `CAP-QA-001`
  - monitoring_and_control: downgrade unsupported conclusions to `unknown`
  - closure: finalize states and return findings with evidence
- tags: `qa`, `review`, `quality`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/quality/100_cap_qa_001_code_review.md#xid-7E9CCEBEDA2D`
- knowledge_refs: none

