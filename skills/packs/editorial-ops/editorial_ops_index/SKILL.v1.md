---
schema_version: 1
skill_id: editorial_ops_index
xid: C8E1A6D3B270
aliases: [67179146EEB3, 14BEA21097F6]
summary: route editorial requests to the correct editorial-ops Skills and keep review and release stages explicit
applies_when:
  - notes, sources, or a draft need a managed editorial workflow instead of one-shot prompting
exclusions:
  - do not skip intake when audience, sources, or channel targets are unclear
  - draft generation is not implicit publication approval
inputs: [topic notes, source links, existing draft state, target channels, urgency or quality concerns]
outputs: [selected Skill sequence, routing rationale, unresolved prerequisites, routing note path]
criteria:
  - id: stage_routing
    statement: The visible editorial state is mapped to the minimum required Skill sequence.
    verification: Compare the routing note with the supplied idea, draft, review, and release state.
  - id: review_gate
    statement: Both review Skills precede crosspost release unless draft-only output is explicit.
    verification: Inspect stage order and any recorded skip reason.
  - id: unresolved_prerequisites
    statement: Missing audience, source, channel, and approval prerequisites remain explicit.
    verification: Review the routing note open items and next handoff.
knowledge_needs:
  - id: editorial_framework
    query: editorial operations framework for routing and publication boundaries
    required_when: Required for every editorial routing decision unless applicability is explicitly recorded.
    seed_xids: [F9E58E2BAD21]
control_refs: []
---
<!-- xid: C8E1A6D3B270 -->
<a id="xid-C8E1A6D3B270"></a>

# Skill: editorial_ops_index

## Purpose
Route editorial work to the correct pack Skills so intake, drafting, review, and release do not collapse into one prompt.

## Method
1. Confirm whether the request starts from an idea, draft, review, or release state and identify target channels.
2. Resolve the editorial framework Knowledge and preserve its selected XID.
3. Classify the request into `editorial_intake`, `draft_authoring`, `fact_review`, `reader_experience_review`, and/or `crosspost_release`.
4. Require intake when topic framing, source basis, audience, or publication boundary is unclear.
5. Require both reviews before `crosspost_release` unless draft-only output is explicit.
6. Keep skipped stages and reasons explicit, then write the routing note to `work/editorial_ops/` with a date-prefixed filename unless another path is supplied.

## Monitoring, stop, and handoff
- Stop if review is skipped while release readiness is claimed, or if channel adaptation would overwrite source meaning.
- Do not treat one strong source as permission to skip factual separation.
- Return the selected sequence, unresolved prerequisites, and next execution handoff; publication approval remains with the human requester.
