# Skill: devto_check

## Purpose

Check a Dev.to article draft before publishing.
Return a clear pass/fail result with concrete fixes.
Use the canonical check spec in `knowledge/devto/100_devto_check_spec.md#xid-D6AFA8483950`.

## Inputs

- draft text (or path to draft)
- mode: `check-only` or `check-and-rewrite`
- optional topic/audience
- optional target style constraints

## Outputs

- checklist result by category
- blocking issues (must-fix)
- non-blocking improvements (should-fix)
- ready-to-publish verdict: `PASS` or `REVISE`
- if mode is `check-and-rewrite`: full revised draft

## Checklist

1. Structure
   - clear title
   - problem -> approach -> result flow
   - section order is understandable
2. Clarity
   - no ambiguous pronouns
   - key terms are defined once
   - paragraphs are concise
3. Technical correctness
   - commands/code match the stated environment
   - no contradictory claims
   - uncertainty is explicitly marked ("I don't know" protocol)
4. Safety/Trust
   - no invented facts
   - assumptions are declared
   - risky claims include limits/conditions
5. Actionability
   - includes reproducible steps
   - expected outcomes are explicit

## Procedure

1. Load check spec: `knowledge/devto/100_devto_check_spec.md#xid-D6AFA8483950`.
2. Read the draft end-to-end once.
3. Run the checklist and collect issues by category.
4. Mark each issue:
   - `blocking`: publish should stop
   - `non_blocking`: quality improvement
5. Provide concrete rewrite suggestions with minimal text replacements.
6. Provide 3-5 revised title candidates with rationale.
7. Output final verdict:
   - `PASS` if no blocking issue
   - `REVISE` if at least one blocking issue exists
8. If mode is `check-and-rewrite`, output a rewritten full draft that resolves blocking issues first.

## Rules

- Do not fabricate references or facts.
- If fact validity is uncertain, state uncertainty and request source confirmation.
- Keep feedback specific; avoid generic comments.
- In rewrite mode, preserve original intent and core message.
- In rewrite mode, do not over-optimize into clickbait.

## Failure Handling

- If draft is incomplete, return `REVISE` and list missing sections first.
- If intent/audience is unknown, ask for them before final pass/fail.
