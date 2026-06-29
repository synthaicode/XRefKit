<!-- xid: 79372C67DBA0 -->
<a id="xid-79372C67DBA0"></a>

# Skill Meta: reader_experience_review

- skill_id: `reader_experience_review`
- summary: review a draft from the target reader perspective to surface confusion, drop-off points, context gaps, and pacing issues
- use_when: a draft exists and the team needs reader-side feedback before release or before final restructuring
- input: article draft, intake record, target audience definition, reader capability assumption, and optional channel-specific reading assumptions
- output: reader-experience review under `work/editorial_ops/` by default, plus friction points, capability-mismatch findings, likely reader questions, and revision priorities
- maturity: `draft`
- execution_mode: `subagent_preferred`
- model_tier: `standard`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: review a draft from the target reader perspective to surface confusion, drop-off points, context gaps, and pacing issues
- role_responsibilities:
  - executor: a draft exists and the team needs reader-side feedback before release or before final restructuring
  - quality_reviewer: independently review output acceptance when this Skill run requires a quality gate
  - handoff_owner: record outputs, unresolved items, next owner, and handoff boundary for this Skill run
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
- constraints: review from the declared reader perspective rather than generic style taste; evaluate omission and pacing against the declared reader capability assumption; keep missing audience evidence explicit; do not convert reader feedback into factual approval; write the review result to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the draft, intake record, target reader definition, and reader capability assumption exist
  - planning: define the likely reader path through the article and where friction is most likely to occur given the assumed prior knowledge
  - execution: review the draft from that perspective and write the experience review result
  - monitoring_and_control: downgrade unsupported audience or capability assumptions to open questions and stop if the task tries to approve factual claims from empathy alone
  - closure: return the review path, top friction points, and the author revision handoff
- tags: `editorial`, `review`, `reader`, `ux`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`
  - `../../../../knowledge/packs/editorial-ops/120_reader_capability_model.md#xid-125B6C5E3630`
