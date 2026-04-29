<!-- xid: C8D4A92F61E0 -->
<a id="xid-C8D4A92F61E0"></a>

# Capability: CAP-MKT-002 Repository Infographic Snapshot

## Definition

- capability_id: `CAP-MKT-002`
- capability_name: `repository_infographic_snapshot`
- work_type: `execution`
- summary: create a one-page marketing infographic that represents the current repository structure, operating model, and control message

## Preconditions

- the target repository or repository area is known
- the intended audience is known or can be recorded as `unknown`
- the infographic is meant to explain the repository's current state, not an imagined future design

## Trigger

- a one-page image is needed to explain what the repository currently represents
- a deck, README, article, or social post needs a standalone visual summary
- the existing repository explanation has drifted and needs a refreshed visual snapshot

## Inputs

- repository entry points such as `README.md`, `docs/000_index.md`, and `agent/000_agent_entry.md`
- relevant operating-model, workflow, capability, skill, and knowledge pages
- current repository status or release context when the image is time-sensitive
- target audience and intended viewer action
- required output size, language, and publication context
- visual reference images, if provided

## Outputs

- infographic goal and central claim
- repository fact map
- visual section map
- text-to-visual mapping
- unsupported or unstable claim list
- reusable HTML/CSS/render source files
- final PNG or other requested image export

## Required Domain Knowledge

- current repository structure and entry policy
- repository-specific control model when explaining XRefKit
- flow, capability, skill, knowledge, source, and XID relationships
- context-direction guard and uncertainty-handling rules when they are part of the message

## Constraints

- represent the repository as it currently is; do not invent functions that are not documented or implemented
- separate evidence-backed repository facts from marketing framing
- show `unknown`, unsupported assumptions, and human decision boundaries when they are part of the repository's control model
- keep the infographic rerenderable; do not keep only the final PNG
- keep claims traceable to repository files or mark them as marketing explanation
- do not present the infographic as an official product promise, roadmap, or policy commitment unless the responsible owner grants that authority

## Assignment

- marketing and orientation visual explanation
- [AI Organization Explainer Video Team](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- This capability is for single-image repository explanation, not general decorative illustration.
- For XRefKit, the stable visual center should be controlled AI work: responsibility separation, required context loading, AI execution/check separation, no unsupported guessing, context-direction guard, human trade-off decisions, and auditability.
- Stable XID references are supporting infrastructure and should not displace the operating-control message unless the request specifically targets reference durability.
- Visual production may use `marketing_slide_png` in `single_image_infographic` mode after the fact map and visual section map are explicit.

## Task Lifecycle Mapping

- Startup:
  - confirm the repository scope, audience, output language, image size, publication context, and desired viewer action
  - identify the repository entry points and source pages that must be read
- Planning:
  - define the central claim, fact map, visual section map, and evidence/unknown list
  - decide which repository concepts must appear and which details should be omitted for readability
- Execution:
  - produce a one-page visual specification
  - render the infographic from reusable HTML/CSS/source files into PNG
- Monitoring and Control:
  - verify that each non-obvious claim is traceable or explicitly framed as marketing explanation
  - verify that the image represents the current repository rather than an unsupported future state
  - verify that text is readable at the requested output size
- Closure:
  - confirm the final PNG exists
  - confirm the render sources are preserved
  - record remaining unknowns, unstable claims, or refresh triggers
