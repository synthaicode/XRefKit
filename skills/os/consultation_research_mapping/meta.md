<!-- xid: 0985CDA7359E -->
<a id="xid-0985CDA7359E"></a>

# Skill Meta: consultation_research_mapping

- skill_id: `consultation_research_mapping`
- summary: map a consultation topic to prior research, known reusable patterns, deterministic extraction work, and the remaining non-deterministic judgment space
- use_when: a user brings a consultation, design question, strategy question, or vague technical/business topic and wants to avoid reinventing the wheel by first identifying prior art, established approaches, reusable methods, and which parts should be handled deterministically versus left to LLM or human judgment
- input: consultation topic, current decision or advice needed, known constraints, target domain, optional source hints, freshness requirement, and output location when a durable note is needed
- output: consultation research map with source boundary, prior-art summary, reusable patterns, deterministic work candidates, non-deterministic judgment candidates, unknowns, risks, and recommended next routing or handoff
- maturity: `trial`
- model_tier: `standard`
- execution_mode: `subagent_preferred`
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
- constraints: do not treat model memory as prior research; verify drift-prone prior art with current sources; separate source-backed facts from interpretation; do not convert ambiguous human objectives into deterministic work without explicit boundary evidence; do not claim novelty, consensus, or best practice without source support; preserve missing source coverage as `unknown`
- lifecycle:
  - startup: confirm the consultation topic, advice target, freshness need, source boundary, and whether the output is transient or should be written under `work/`
  - planning: define search questions, source classes, deterministic extraction candidates, judgment candidates, and stop conditions before collecting sources
  - execution: collect and cite prior-art evidence, summarize established approaches, classify reusable patterns, split deterministic work from non-deterministic judgment, and produce a next-action map
  - monitoring_and_control: run context-direction checks for loaded sources, downgrade unsupported claims to `unknown`, stop when source integrity or consultation scope is unclear, and record non-trivial novelty or applicability judgments
  - closure: return the research map, cited evidence, deterministic follow-up candidates, non-deterministic judgment/human-review items, unresolved unknowns, and next routing recommendation
- tags: `operations`, `consultation`, `research`, `triage`, `judgment`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../knowledge/organization/140_llm_review_knowledge_usage_rules.md#xid-7A2F4C8D1401`
  - `../../../knowledge/organization/121_judgment_log_schema.md#xid-7B4C2D91E621`
- observation_refs:
  - `../../../work/sessions/2026-06-28_session_consultation_research_mapping_seed.md`
