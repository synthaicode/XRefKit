<!-- xid: B2F5D8C31E64 -->
<a id="xid-B2F5D8C31E64"></a>

# Skill: presentation_flow_review

## Purpose

Review or revise the explanatory flow of a presentation before visual rendering.
Treat the deck as a connected argument, not as an independent collection of
well-written slides.

## Inputs

- target deck or slide script
- intended audience and assumed prior knowledge
- central claim the audience should understand
- whether the task is review-only or an authorized narrative revision
- optional duration and factual constraints

## Outputs

- flow review path under `work/presentation_flow_review/` unless another path is supplied
- current slide-role map
- prioritized flow findings
- revised slide order with title, purpose, and bridge to the next slide
- handoff to the deck-authoring or rendering Skill

## Procedure

1. State the central claim in one sentence. State the audience conclusion the
   deck must support.
2. Map each slide to one role: problem, premise, definition, mechanism,
   consequence, evidence, decision, or conclusion. Mark slides with no unique
   role.
3. For every transition, write the premise required to understand the next
   slide. Flag a transition when that premise is absent or first appears after
   the mechanism that depends on it.
4. Identify and rank flow defects:
   - premise gap: an introduced concept has no prior reason or definition
   - causal inversion: a mechanism appears before the problem it solves
   - duplicate role: adjacent slides make the same argument without advancing it
   - missing bridge: the next claim does not follow from the current claim
   - conclusion gap: the ending asserts a result not established by the deck
   - overloaded slide: one slide contains multiple independent explanatory moves
5. Build the minimum revised causal flow. Preserve validated facts and remove
   or merge only slides that do not advance the argument.
6. For every proposed slide, provide:
   - title
   - one-sentence purpose
   - required premise from the preceding slide
   - bridge sentence explaining why the next slide follows
7. Keep factual gaps explicit. If the revised flow needs an unverified fact,
   record it as an unknown or request source material; do not invent a bridge.
8. When the revised flow is approved, hand it to the appropriate authoring or
   rendering Skill. For CSS/HTML PNG deck assets, hand off to
   `marketing_slide_png`.

## Review Boundaries

- Do not treat fluent wording as evidence that the argument is sound.
- Do not replace factual review, domain review, quality acceptance, or human
  approval.
- Do not use generic style preferences as a flow finding.
- Do not change images, layout, or speaker timing unless the user explicitly
  includes them in the revision scope.

## Closure

Return the flow review path, the top flow defects, the revised causal outline,
and the next Skill or human decision required.

## Reporting Contract (共通報告)



- reporting_profile: phase_summary

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
