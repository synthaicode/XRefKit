<!-- xid: 54437A84B3D0 -->
<a id="xid-54437A84B3D0"></a>

# Skill Meta: editorial_intake

- skill_id: `editorial_intake`
- summary: scope an article task into topic, audience, evidence basis, quality target, and publication boundary before drafting
- use_when: article work starts from fragments, loose notes, or vague publication intent and the execution target is not yet stable enough for drafting
- input: article idea, raw notes, optional links, target audience hints, optional reader capability assumption, and target channels
- output: intake record with topic focus, audience hypothesis, reader capability assumption, evidence basis, channel target, quality checkpoints, and explicit open questions
- maturity: `draft`
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
- constraints: do not start from writing style before topic and evidence basis are visible; do not treat audience label alone as enough reader definition when capability assumptions matter; keep facts and framing hypotheses separate; preserve missing source support as `unknown`; write the intake record to `work/editorial_ops/` with a date-prefixed filename unless another path is specified
- lifecycle:
  - startup: confirm the article seed, current source set, audience hints, reader capability assumption, and desired channels
  - planning: decide the smallest viable article boundary and what must be confirmed about both audience and prior knowledge before drafting
  - execution: structure the intake record and separate confirmed inputs from authoring assumptions
  - monitoring_and_control: downgrade unsupported framing claims to open questions and stop if the task tries to lock publication claims without source basis or without a usable reader capability assumption
  - closure: return the intake path, highest-priority open questions, and the drafting handoff
- tags: `editorial`, `intake`, `writing`, `planning`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`
  - `../../../../knowledge/packs/editorial-ops/120_reader_capability_model.md#xid-125B6C5E3630`
