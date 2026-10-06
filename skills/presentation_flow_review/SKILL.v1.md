---
schema_version: 1
skill_id: presentation_flow_review
xid: D8F1A6C3B520
summary: review and restructure an explanatory presentation so claims, premises, mechanisms, and conclusions follow an explicit causal flow
applies_when:
- a slide deck or slide script exists and the explanation feels abrupt, repetitive, causally inverted, or difficult to follow; use before visual rendering or when revising an existing deck's narrative structure
exclusions:
- Human final approval or release decision remains outside this Skill
- Unsupported conclusions remain unresolved rather than being silently completed
inputs:
- target deck or slide script, intended audience, central claim, optional presentation duration, and optional known factual constraints
outputs:
- presentation-flow review under `work/presentation_flow_review/` by default, a revised slide order with per-slide purpose and bridge statements, prioritized flow findings, and a handoff to the deck-authoring or rendering Skill
criteria:
- id: semantic_sequence
  statement: The Skill's evaluation sequence and semantic criteria are applied in order without embedding routing or capability identifiers
  verification: Inspect each phase result and evidence link against the method sequence
- id: decision_boundary
  statement: Human final-decision authority remains explicit and unsupported judgments remain unknown
  verification: Check closure, rules, and handoff for approval boundaries
- id: output_closure
  statement: The declared result and unresolved items are returned with a handoff
  verification: Check the output and handoff before closure
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs: []
control_refs: []
aliases:
- B2F5D8C31E64
- A1E4C7B29D53
---
<!-- xid: D8F1A6C3B520 -->
<a id="xid-D8F1A6C3B520"></a>

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

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

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

### Original Skill-specific declarations

- summary: review and restructure an explanatory presentation so its claims, premises, mechanisms, and conclusion follow an explicit causal flow without unexplained concept jumps

- use_when: a slide deck or slide script exists and the explanation feels abrupt, repetitive, causally inverted, or difficult to follow; use before visual rendering or when revising an existing deck's narrative structure

- input: target deck or slide script, intended audience, central claim, optional presentation duration, and optional known factual constraints

- output: presentation-flow review under `work/presentation_flow_review/` by default, a revised slide order with per-slide purpose and bridge statements, prioritized flow findings, and a handoff to the deck-authoring or rendering Skill

- constraints: review the explanation flow rather than visual taste or factual truth; do not invent missing facts to make a story smoother; distinguish a missing premise from an unsupported claim; do not approve factual claims; keep existing slide facts unless the user authorizes content revision; do not render or modify slide assets unless an approved narrative revision explicitly hands off to a rendering Skill

- lifecycle:
  - startup: confirm the target deck or script, central claim, intended audience, and whether the task is review-only or authorized revision
  - planning: map the current role of every slide and the premise each transition requires
  - execution: identify flow defects and produce a revised causal slide outline with explicit bridge statements
  - monitoring_and_control: keep factual gaps, audience assumptions, and unsupported claims explicit; stop narrative smoothing from becoming invented content
  - closure: return the review path, prioritized findings, approved or proposed slide flow, and handoff target

- tags: `presentation`, `slides`, `narrative`, `story`, `review`, `causality`, `explanation`

- observation_refs:
  - `../../observations/2026-07-11_presentation_flow_review_authoring_basis.md`
