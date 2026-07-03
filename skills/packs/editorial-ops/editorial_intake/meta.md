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
- model_tier: `light`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: scope an article task into topic, audience, evidence basis, quality target, and publication boundary before drafting
- responsibility: article work starts from fragments, loose notes, or vague publication intent and the execution target is not yet stable enough for drafting
- os_contract: v1
- constraints: do not start from writing style before topic and evidence basis are visible; do not treat audience label alone as enough reader definition when capability assumptions matter; keep facts and framing hypotheses separate; preserve missing source support as `unknown`; write the intake record to `work/editorial_ops/` with a date-prefixed filename unless another path is specified
- lifecycle:
  - startup: confirm the article seed, current source set, audience hints, reader capability assumption, and desired channels
  - planning: decide the smallest viable article boundary and what must be confirmed about both audience and prior knowledge before drafting
  - execution: structure the intake record and separate confirmed inputs from authoring assumptions
  - monitoring_and_control: downgrade unsupported framing claims to open questions and stop if the task tries to lock publication claims without source basis or without a usable reader capability assumption
  - closure: return the intake path, highest-priority open questions, and the drafting handoff
- tags: `editorial`, `intake`, `writing`, `planning`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`
  - `../../../../knowledge/packs/editorial-ops/120_reader_capability_model.md#xid-125B6C5E3630`
