---
schema_version: 1
skill_id: draft_authoring
xid: B6A9D3F1C720
aliases:
  - BFEF855AAA8D
  - 51FDA8671D61
summary: produce an article draft from explicit intake framing and source basis without hiding unsupported claims
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
<!-- xid: B6A9D3F1C720 -->
<a id="xid-B6A9D3F1C720"></a>

# Skill: draft_authoring

## Purpose

Produce a usable article draft from explicit framing and sources while keeping
unsupported claims visible instead of polishing them into hidden assumptions.

## Inputs

- intake record
- source set
- optional existing draft
- channel intent

## Outputs

- draft path
- claim-to-source notes
- unresolved authoring questions

## Startup

- Confirm the intake record exists.
- Confirm the source set is enough to support at least a first draft.
- Confirm whether the target is a new draft or revision.

## Execution

1. Build the article spine from the intake goal and audience.
2. Write the draft in that order.
3. Keep unsupported claims marked for later review.
4. Add claim-to-source notes for concrete assertions, numbers, names, and URLs.
5. Write the draft to the output path and return it.

## Monitoring and Control

- Do not convert missing evidence into confident prose.
- Do not treat smooth structure as factual validity.
- Keep channel-specific wording changes reversible.

## Closure

- Return the draft path.
- Return the unresolved authoring questions.
- State that the next steps are `fact_review` and `reader_experience_review`.

