<!-- xid: 67179146EEB3 -->
<a id="xid-67179146EEB3"></a>

# Skill: editorial_ops_index

## Purpose

Route editorial work to the correct pack Skills so intake, drafting, review,
and release do not collapse into one prompt.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- topic fragments, notes, or article seeds
- source links or evidence set
- optional existing draft
- publication channels and timeline

## Outputs

- selected Skill sequence
- routing rationale
- explicit missing prerequisites
- routing note path

## Startup

- Confirm whether the request starts from idea, draft, review, or release state.
- Identify which channels the article is intended for.
- Load the routing table and shared principles from the framework knowledge page.

## Execution

1. Classify the request into one or more stages:
   - `editorial_intake`
   - `draft_authoring`
   - `fact_review`
   - `reader_experience_review`
   - `crosspost_release`
2. Require `editorial_intake` when topic framing, source basis, audience, or publication boundary is still unclear.
3. Require both review Skills before `crosspost_release` unless the user explicitly asks for a draft-only output.
4. Keep skipped stages explicit with reason.
5. Write the routing result to the output path and return that path.

## Monitoring and Control

- Stop if review is being skipped while the request still claims release readiness.
- Do not treat one strong source as automatic permission to skip factual separation.
- Do not let channel adaptation silently overwrite the source article meaning.

## Closure

- Return the selected Skill set and order.
- Return the unresolved prerequisites.
- Return the routing note path.
