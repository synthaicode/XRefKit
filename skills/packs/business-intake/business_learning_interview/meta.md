<!-- xid: 2B6D4F18A3C1 -->
<a id="xid-2B6D4F18A3C1"></a>

# Skill Meta: business_learning_interview

- skill_id: `business_learning_interview`
- summary: learn a business task from a human through goal-first interview and convert partial fragments into a structured business hypothesis
- use_when: a user wants to teach the AI about a business task conversationally, but can better explain the intended goal than the full process, or only knows fragments, tacit operational knowledge, bottlenecks, or partial handoffs
- input: one or more starting seeds such as goal or expected result, task name, role name, artifact, bottleneck, repeated error, approval point, or partial handoff, plus optional follow-up answers
- output: interview-cycle summary with goal hypothesis, learned facts, current hypothesis, decision hypothesis, required domain knowledge, required input information, quality viewpoints, open questions, next best question, and candidate business unit
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `heavy`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: learn a business task from a human through goal-first interview and convert partial fragments into a structured business hypothesis
- responsibility: a user wants to teach the AI about a business task conversationally, but can better explain the intended goal than the full process, or only knows fragments, tacit operational knowledge, bottlenecks, or partial handoffs
- os_contract: v1
- constraints: do not demand a complete process description before helping; do not skip the goal and jump directly to local tasks; do not mix human facts and AI inference; do not ask broad dump-everything questions when a smaller question can reduce ambiguity; keep unresolved items explicit
- lifecycle:
  - startup: confirm the visible seed, prefer goal or expected result when available, and load interview rules and template
  - planning: identify the goal first, then the smallest missing point and choose the next best question
  - execution: produce one interview cycle with goal hypothesis, learned facts, current hypothesis, decision hypothesis, domain knowledge needs, input information needs, quality viewpoints, open questions, and next best question
  - monitoring_and_control: downgrade overconfident inference, broad questioning, hidden ambiguity, or lower-level detail that appears before the goal is clarified
  - closure: return the interview-cycle output and the recommended next question or transition to scoping
- tags: `operations`, `learning`, `interview`, `business`, `intake`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../../../knowledge/packs/business-intake/120_business_learning_interview_rules.md#xid-7B3E5D1A6103`
  - `../../../../docs/packs/business-intake/061_business_learning_interview_guide.md#xid-D2A41E8C7B51`
  - `../../../../docs/packs/business-intake/060_business_intake_scoping_guide.md#xid-C91F7D2A6B40`
- observation_refs:
  - `../../../../observations/2026-05-01_session_business_learning_interview_skill_seed.md`
