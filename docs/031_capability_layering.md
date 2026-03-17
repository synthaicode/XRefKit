<!-- xid: 8D50A972BA9F -->
<a id="xid-8D50A972BA9F"></a>

# Capability Layering

This repository separates workflow, capability, domain knowledge, and executable procedure.

## Intent

Keep `knowledge/` focused on domain knowledge.
Store reusable capability definitions in `capabilities/`.

## Layers

- `docs/`: human-facing workflow, governance, boundaries, escalation, CAB
- `capabilities/`: reusable work-unit definitions
- `knowledge/`: shared domain knowledge and local rules
- `skills/`: executable procedures that use capability definitions and domain knowledge

## Mapping

- business workflow -> `docs/`
- capability definition -> `capabilities/`
- evidence and local rules -> `knowledge/`
- execution procedure -> `skills/`

## Three Layers

- capability:
  - reusable base professional ability
  - examples: software development, accounting, review, planning
- tuning:
  - specialization of a capability by technology, framework, domain, or quality focus
  - examples: C#, .NET, construction-industry accounting, security-focused review
- responsibility:
  - how a tuned capability is exercised for a business purpose
  - examples: implementation, code review, finance, bookkeeping, management accounting

## Interpretation

- A capability is the reusable base.
- Tuning changes how that capability is specialized.
- Responsibility changes how the tuned capability is exercised in a workflow.

## Naming Rule

- Capability names should describe reusable professional ability.
- Responsibility and workflow names should describe the business activity that uses that ability.
- Names such as `service catalog analysis` belong in workflow or responsibility definitions.
- The supporting capability beneath that activity should use an abstract name such as `scope classification`.

Example:

- base capability: software development
- technical tuning: C#
- domain tuning: construction industry
- responsibility: implementation for a construction-industry C# system

## Example

- workflow: implementation and review flow in `docs/`
- capability: `CAP-MFG-001` in `capabilities/manufacturing/`
- domain knowledge: coding rules in `knowledge/`
- execution: `skills/implementation_flow/`

## Review Judgment Rule

- For review-oriented `judgment` capabilities, LLM internal knowledge is supplementary only.
- Primary evidence must come from local artifacts and referenced canonical knowledge.
- See [LLM review knowledge usage rules](../knowledge/organization/140_llm_review_knowledge_usage_rules.md#xid-7A2F4C8D1401).

## Group Work Rule

- Within a group boundary, workflow is `execution -> recording -> self-check -> handoff`.
- The self-check remains inside the same responsibility boundary as the executed work.
- Cross-group review or approval is a separate step after that handoff.
