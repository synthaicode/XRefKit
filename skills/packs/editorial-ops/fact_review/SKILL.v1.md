---
schema_version: 1
skill_id: fact_review
xid: D4E8B2A6F190
aliases:
  - 0AA2CEC66CB2
  - 7687FD352C4C
summary: review article claims for factual separation, source support, names, numbers, links, and channel-sensitive wording risks
applies_when:
  - the editorial workflow has the source, intake, or reader context required by this Skill
exclusions:
  - Publication approval remains with the human requester
  - Unsupported claims or audience assumptions remain unresolved rather than being silently completed
inputs:
  - source material and workflow artifacts required by this Skill
outputs:
  - editorial result path
  - evidence or reader-experience findings
  - unresolved questions and handoff
criteria:
  - id: evidence_and_audience_boundary
    statement: Claims, evidence, reader assumptions, and unresolved support remain explicitly separated
    verification: Inspect the result for traceable evidence and explicit unknowns
  - id: human_publication_authority
    statement: The Skill does not approve publication or convert review feedback into factual approval
    verification: Check the handoff and publication boundary before closure
  - id: output_closure
    statement: The declared editorial result exists and the next handoff is stated
    verification: Check the output path, open items, and handoff
knowledge_needs:
  - id: editorial_operations_framework
    query: editorial operations framework
    required_when: Required when applying this Skill's editorial or reader evaluation criteria
    seed_xids:
      - F9E58E2BAD21
control_refs: []
---
<!-- xid: D4E8B2A6F190 -->
<a id="xid-D4E8B2A6F190"></a>

# Skill: fact_review

## Purpose

Review article claims against the visible evidence set so factual gaps,
unsupported wording, and release blockers stay explicit.

## Inputs

- article draft
- source links or evidence set
- optional claim list
- target channels

## Outputs

- fact-review result path
- release blockers
- unresolved unknowns

## Startup

- Confirm the draft and source set exist.
- Identify the highest-risk claim classes such as numbers, names, dates, URLs, and quoted assertions.
- Confirm whether the goal is draft feedback or release gating.

## Execution

1. Extract the concrete claims that need checking.
2. Compare each claim to the visible source basis.
3. Classify each result as supported, unsupported, ambiguous, or channel-risky.
4. Mark missing support as `unknown`.
5. Write the review result to the output path and return it.

## Monitoring and Control

- Do not rewrite the article and call it review.
- Do not treat likely truth as verified support.
- Keep opinion and fact findings separate.

## Closure

- Return the fact-review result path.
- Return the release blockers.
- Return the author revision handoff.

