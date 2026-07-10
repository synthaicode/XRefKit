<!-- xid: A1E4C7B29D53 -->
<a id="xid-A1E4C7B29D53"></a>

# Skill Meta: presentation_flow_review

- skill_id: `presentation_flow_review`
- summary: review and restructure an explanatory presentation so its claims, premises, mechanisms, and conclusion follow an explicit causal flow without unexplained concept jumps
- use_when: a slide deck or slide script exists and the explanation feels abrupt, repetitive, causally inverted, or difficult to follow; use before visual rendering or when revising an existing deck's narrative structure
- input: target deck or slide script, intended audience, central claim, optional presentation duration, and optional known factual constraints
- output: presentation-flow review under `work/presentation_flow_review/` by default, a revised slide order with per-slide purpose and bridge statements, prioritized flow findings, and a handoff to the deck-authoring or rendering Skill
- maturity: `trial`
- execution_mode: `subagent_preferred`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: review and restructure explanatory narrative flow
- tuning: presentation-level causal ordering, premise introduction, and slide-to-slide transitions
- responsibility: make an explanatory deck understandable as a connected argument before slide visuals or narration are finalized
- os_contract: v1
- constraints: review the explanation flow rather than visual taste or factual truth; do not invent missing facts to make a story smoother; distinguish a missing premise from an unsupported claim; do not approve factual claims; keep existing slide facts unless the user authorizes content revision; do not render or modify slide assets unless an approved narrative revision explicitly hands off to a rendering Skill
- lifecycle:
  - startup: confirm the target deck or script, central claim, intended audience, and whether the task is review-only or authorized revision
  - planning: map the current role of every slide and the premise each transition requires
  - execution: identify flow defects and produce a revised causal slide outline with explicit bridge statements
  - monitoring_and_control: keep factual gaps, audience assumptions, and unsupported claims explicit; stop narrative smoothing from becoming invented content
  - closure: return the review path, prioritized findings, approved or proposed slide flow, and handoff target
- tags: `presentation`, `slides`, `narrative`, `story`, `review`, `causality`, `explanation`
- skill_doc: `./SKILL.md`
- observation_refs:
  - `../../observations/2026-07-11_presentation_flow_review_authoring_basis.md`
