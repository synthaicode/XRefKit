<!-- xid: A4E9B13D7C20 -->
<a id="xid-A4E9B13D7C20"></a>

# Capability: CAP-MKT-001 Presentation Material Structuring

## Definition

- capability_id: `CAP-MKT-001`
- capability_name: `presentation_material_structuring`
- work_type: `execution`
- summary: structure a presentation from goal definition through issue organization, information collection, analysis, and deck structure

## Preconditions

- a presentation topic, request, or communication need exists
- intended audience or stakeholder context is known or can be clarified

## Trigger

- marketing or orientation presentation material must be prepared
- a slide deck, explanatory deck, or slide-based video needs an argument structure before visual production

## Inputs

- requested topic
- target audience
- intended decision, understanding, or viewer action
- available source materials
- constraints on scope, timing, tone, or publication context

## Outputs

- presentation goal
- issue map
- information collection list
- analysis memo
- deck structure outline
- unresolved evidence list

## Required Domain Knowledge

- source materials for the requested topic
- audience and stakeholder context
- applicable repository facts when the deck explains XRefKit
- marketing tone and presentation conventions

## Constraints

- do not start slide visual production before the goal, issue map, and deck structure are explicit
- distinguish evidence-backed claims from explanatory or marketing framing
- preserve missing source material as `unknown`
- do not approve official announcements, policy positions, or business commitments unless the responsible owner assigns that authority
- keep the deck structure aligned to the requested audience and desired action

## Assignment

- marketing and orientation presentation preparation
- [AI Organization Explainer Video Team](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `presentation material creation` is the business activity assigned to the Marketing Group production function.
- This capability covers the upstream thinking work: goal definition, issue structuring, information collection, analysis, and structure design.
- Visual slide production may use `marketing_slide_png` after this capability has produced a stable deck structure.

## Task Lifecycle Mapping

- Startup:
  - confirm the topic, audience, desired action, source availability, and constraints
  - if the audience or desired action is missing, record `unknown` before continuing
- Planning:
  - define the work rows for goal definition, issue organization, information collection, analysis, and deck structure
- Execution:
  - produce the outputs defined in this capability within its stated constraints
- Monitoring and Control:
  - check whether claims are supported, unsupported, or intentionally framed as marketing explanation
  - downgrade weakly supported conclusions to `unknown`
- Closure:
  - confirm the presentation structure is finalized as `done`, `unknown`, or `out_of_scope`
  - preserve unresolved and out-of-scope items for handoff or escalation
