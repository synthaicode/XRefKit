<!-- xid: BFEF855AAA8D -->
<a id="xid-BFEF855AAA8D"></a>

# Skill: draft_authoring

## Purpose

Produce a usable article draft from explicit framing and sources while keeping
unsupported claims visible instead of polishing them into hidden assumptions.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

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
