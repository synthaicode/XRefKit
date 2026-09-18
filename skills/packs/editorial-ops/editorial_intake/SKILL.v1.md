---
{
  "schema_version": 1,
  "skill_id": "editorial_intake",
  "xid": "7C4E9A2D6F81",
  "aliases": ["77F7D4CB9F99", "54437A84B3D0"],
  "summary": "scope an article task into topic, audience, evidence basis, quality target, and publication boundary before drafting",
  "applies_when": ["article work starts from fragments, loose notes, or vague publication intent and the execution target is not yet stable enough for drafting"],
  "exclusions": ["drafting or publication approval", "unsupported claims presented as established evidence"],
  "inputs": ["article idea or raw notes", "optional source links or citations", "audience and reader capability hints", "target channels"],
  "outputs": ["intake record path", "topic focus", "audience and reader capability assumption", "evidence basis", "quality checkpoints", "publication boundary", "open questions"],
  "criteria": [
    {"id": "intake_scope", "statement": "The intake record states the topic focus, audience, reader capability assumption, and channel boundary.", "verification": "Inspect the declared intake record and apply Workflow verification and closure gates."},
    {"id": "evidence_basis", "statement": "Confirmed evidence, framing assumptions, and missing support are separated.", "verification": "Check the intake record for explicit evidence and unknown entries."},
    {"id": "draft_handoff", "statement": "Quality checkpoints and open questions are recorded for the drafting handoff.", "verification": "Inspect the handoff fields and apply Workflow verification and closure gates."}
  ],
  "knowledge_needs": [
    {"id": "editorial_operations_framework", "query": "editorial operations framework for intake scope and publication boundary", "required_when": "Required for every editorial intake unless the parent explicitly records why it is not applicable.", "seed_xids": ["F9E58E2BAD21"]},
    {"id": "reader_capability_model", "query": "reader capability model for audience and prior knowledge assumptions", "required_when": "Required when audience capability or assumed prior knowledge affects the intake.", "seed_xids": ["125B6C5E3630"]}
  ],
  "control_refs": []
}
---
<!-- xid: 7C4E9A2D6F81 -->
<a id="xid-7C4E9A2D6F81"></a>

# Skill: editorial_intake

## Purpose

Turn a loose article idea into a drafting-ready intake record with an explicit
topic, audience, reader capability assumption, evidence basis, quality target,
and publication boundary.

## Context boundaries

Keep confirmed facts, source-supported claims, framing hypotheses, and missing
support separate. Treat audience labels as hypotheses until the reader's prior
knowledge and capability assumption are stated. The intake may define a
drafting boundary, but it does not approve publication or settle unsupported
claims.

## Method

1. Confirm what the article is trying to say, the intended channels, and the
   smallest useful topic boundary.
2. Resolve the applicable Knowledge needs at the point they are required;
   record the selected XIDs and any unresolved applicability as `unknown`.
3. Separate confirmed facts and supplied evidence from framing assumptions and
   missing source support.
4. State the intended audience, likely reader question, and reader capability
   assumption. For a Zenn technical article, use
   `zenn_practitioner_web_ai` only as the default when stronger evidence is
   absent; override it for learners or specialists.
5. Define quality checkpoints, explanations that can be omitted, and details
   that must remain explicit for the assumed reader.
6. Write the intake record to `work/editorial_ops/` using a date-prefixed name
   unless another output path is specified.
7. Return the intake path, highest-priority open questions, and the
   `draft_authoring` handoff when the boundary is draft-ready.

## Stop, unknowns, and handoff

Preserve missing source support as `unknown`. Stop and hand off when the task
tries to lock publication claims without a source basis or without a usable
reader capability assumption. Keep release approval with the human requester;
the next owner is `draft_authoring` after the intake boundary is accepted.
