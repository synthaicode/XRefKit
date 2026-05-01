<!-- xid: 2B6D4F18A3C1 -->
<a id="xid-2B6D4F18A3C1"></a>

# Skill Meta: business_learning_interview

- skill_id: `business_learning_interview`
- summary: learn a business task from a human through iterative interview and convert partial fragments into a structured business hypothesis
- use_when: a user wants to teach the AI about a business task conversationally, only knows fragments, has tacit operational knowledge, or wants the AI to ask the next best question instead of demanding a complete process map
- input: one or more starting seeds such as task name, role name, artifact, bottleneck, repeated error, approval point, or partial handoff, plus optional follow-up answers
- output: interview-cycle summary with learned facts, current hypothesis, open questions, next best question, and candidate business unit
- maturity: `trial`
- execution_mode: `local_default`
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
- constraints: do not demand a complete process description before helping; do not mix human facts and AI inference; do not ask broad dump-everything questions when a smaller question can reduce ambiguity; keep unresolved items explicit
- lifecycle:
  - startup: confirm the visible seed and load interview rules and template
  - planning: identify the smallest missing point and choose the next best question
  - execution: produce one interview cycle with learned facts, current hypothesis, open questions, and next best question
  - monitoring_and_control: downgrade overconfident inference, broad questioning, or hidden ambiguity
  - closure: return the interview-cycle output and the recommended next question or transition to scoping
- tags: `operations`, `learning`, `interview`, `business`, `intake`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/operations/120_business_learning_interview_rules.md#xid-7B3E5D1A6103`
  - `../../docs/061_business_learning_interview_guide.md#xid-D2A41E8C7B51`
  - `../../docs/060_business_intake_scoping_guide.md#xid-C91F7D2A6B40`
- observation_refs:
  - `../../work/sessions/2026-05-01_session_business_learning_interview_skill_seed.md`
