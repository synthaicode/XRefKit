---
schema_version: 1
skill_id: judgment_log
xid: C6A2E9B4D170
aliases: [2A9E4C71D5F2, E3C8A16D4B02]
summary: write an inspectable judgment log with decision, evidence, inference boundary, confidence, and next verification
applies_when: [a task produces a non-trivial judgment with mixed confidence or material alternatives]
exclusions: [do not present inferred-only judgments as facts or hide material alternatives and open questions]
inputs: [work type, target, decision, evidence, confidence, optional alternatives, open questions, output path]
outputs: [judgment log path, normalized evidence and inference boundary, decision status]
criteria:
  - id: evidence_boundary
    statement: Facts, inferences, evidence types, confidence, and decision status are separated.
    verification: Inspect the normalized log fields and evidence paths.
  - id: uncertainty
    statement: Inferred-only or weakly supported decisions are downgraded to unknown when appropriate.
    verification: Compare confidence and evidence with the recorded status.
  - id: next_check
    statement: Alternatives, open questions, and the next verification step are preserved.
    verification: Inspect the log before handoff.
knowledge_needs:
  - id: judgment_log_schema
    query: judgment log schema
    required_when: Required for every judgment log
    seed_xids: [7B4C2D91E621]
control_refs: [111D282CA0EA]
---
<!-- xid: C6A2E9B4D170 -->
<a id="xid-C6A2E9B4D170"></a>

# Skill: judgment_log

## Purpose
Write an AI-authored judgment log recording a non-trivial decision, evidence, inference boundary, and next verification step.

## Method
1. Confirm the target and evidence; record missing evidence as `unknown`.
2. Resolve the judgment schema Knowledge and classify evidence as `deterministic`, `context_extracted`, or `inferred`.
3. Classify status as `proposed`, `accepted`, `rejected`, `unknown`, or `deferred`.
4. Normalize path-specific evidence, decision, confidence, alternatives, open questions, and next check.
5. Write to `work/judgments/` or the requested path using the judgment template or equivalent.

## Stop and handoff
- Preserve uncertainty and never mix session facts with judgment reasoning.
- If the target is unwritable, return normalized content and intended path; hand unresolved decisions to the human owner.
