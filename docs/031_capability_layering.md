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

## Example

- workflow: implementation and review flow in `docs/`
- capability: `CAP-MFG-001` in `capabilities/manufacturing/`
- domain knowledge: coding rules in `knowledge/`
- execution: `skills/implementation_flow/`
