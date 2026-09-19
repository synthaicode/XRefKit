---
schema_version: 1
skill_id: reader_experience_review
xid: E1C7A5D9B430
aliases:
  - D84028E6F515
  - 79372C67DBA0
summary: review a draft from the target reader perspective to surface confusion, drop-off points, context gaps, and pacing issues
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
  - id: reader_capability_model
    query: reader capability model
    required_when: Required when applying this Skill's editorial or reader evaluation criteria
    seed_xids:
      - 125B6C5E3630
control_refs: []
---
<!-- xid: E1C7A5D9B430 -->
<a id="xid-E1C7A5D9B430"></a>

# Skill: reader_experience_review

## Purpose

Review a draft from the declared reader perspective so confusion, missing
context, and likely drop-off points are visible before release.

## Inputs

- article draft
- intake record
- target reader definition
- reader capability assumption
- optional channel assumptions

## Outputs

- reader-experience review path
- friction points
- capability-mismatch findings
- revision priorities

## Startup

- Confirm the draft and intake record exist.
- Confirm the intended reader, reading context, and assumed prior knowledge.
- Confirm whether the review is for restructuring, tone adjustment, or release gating.

## Execution

1. Walk the article in reader order.
2. Compare each major jump in the article to the assumed reader capability.
3. Note where a reader would likely pause, doubt, or leave.
4. Separate comprehension issues from factual issues.
5. Flag capability mismatches such as:
   - unexplained low-level concept jumps
   - missing component-role clarification
   - abstraction leaps beyond the assumed tolerance
6. Rank the friction points by likely reader impact.
7. Write the review result to the output path and return it.

## Monitoring and Control

- Do not present empathy-based feedback as factual validation.
- Do not default to generic style preference when reader context is unclear.
- Do not infer clarity without stating what the reader already knows.
- Keep missing audience evidence explicit.

## Closure

- Return the review path.
- Return the top friction points.
- Return the author revision handoff.

