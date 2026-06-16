<!-- xid: 0AA2CEC66CB2 -->
<a id="xid-0AA2CEC66CB2"></a>

# Skill: fact_review

## Purpose

Review article claims against the visible evidence set so factual gaps,
unsupported wording, and release blockers stay explicit.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

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
