<!-- xid: 14BEA21097F6 -->
<a id="xid-14BEA21097F6"></a>

# Skill Meta: editorial_ops_index

- skill_id: `editorial_ops_index`
- summary: route editorial requests to the correct editorial-ops Skills and keep review and release stages explicit
- use_when: a user asks to turn notes, sources, or a draft into a managed article workflow instead of one-shot prompting
- input: topic notes, source links, existing draft state, desired publication channels, and optional urgency or quality concerns
- output: selected Skill sequence, routing rationale, unresolved prerequisites, and a routing note under `work/editorial_ops/` unless another path is specified
- maturity: `draft`
- execution_mode: `local_default`
- model_tier: `light`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: route editorial requests to the correct editorial-ops Skills and keep review and release stages explicit
- responsibility: a user asks to turn notes, sources, or a draft into a managed article workflow instead of one-shot prompting
- os_contract: v1
- constraints: do not skip intake when audience, sources, or channel targets are still unclear; do not treat draft generation as implicit approval; keep shared routing rules in knowledge instead of duplicating them across pack Skills; write the routing note to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm whether the request starts from idea fragments, an existing draft, or a release-ready article and identify the target channels
  - planning: map the visible state to the minimum required Skill sequence and determine which prerequisites are still missing
  - execution: route the request, preserve review before release, and keep skipped stages explicit with reason
  - monitoring_and_control: stop if the task tries to publish unresolved factual or audience-fit gaps as completed work
  - closure: return the selected Skill sequence, routing basis, unresolved gaps, and the next execution handoff
- tags: `editorial`, `routing`, `writing`, `review`
- skill_doc: `./SKILL.md`
- knowledge_refs:
- `../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`
