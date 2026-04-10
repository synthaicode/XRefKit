<!-- xid: 6D2E4A9C0B71 -->
<a id="xid-6D2E4A9C0B71"></a>

# Workflow Page Schema

This page defines the common documentation shape used by workflow pages in `docs/`.

It exists to reduce interpretation drift across workflow pages.
Individual workflows should focus on their domain-specific differences and may rely on this page for the shared section pattern.

## Common Sections

Most workflow pages use the following sections:

- `Purpose`
- `Group Interaction`
- `Flow Diagram`
- `Business Activities and Supporting Capabilities`
- `Sequence`
- optional `Inputs`
- optional `Outputs`
- optional `Control Rules`
- optional `Required Knowledge`
- `Related Skills`

Not every workflow must use every optional section, but omissions should be intentional.

## Section Meanings

- `Purpose`:
  - what outcome this workflow is responsible for
- `Group Interaction`:
  - owner group, upstream inputs, downstream handoff, and escalation path
- `Flow Diagram`:
  - high-level progression and handoff structure
- `Business Activities and Supporting Capabilities`:
  - the business activities and the capability definitions that support them
- `Sequence`:
  - the readable operational order for humans and agents
- `Inputs` / `Outputs`:
  - explicit handoff artifacts where traceability matters
- `Control Rules`:
  - workflow-specific boundary or quality rules that should not be buried only in capabilities
- `Required Knowledge`:
  - knowledge pages that are especially important for executing the workflow
- `Related Skills`:
  - likely skill entry points for execution

## Authoring Rule

Do not repeat repository-wide base control or XRefKit routing rules in every workflow page unless the workflow needs a narrower local rule.

Prefer:

- shared repository rules in:
  - [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
  - [Base control and xref routing layers](017_base_and_xref_layering.md#xid-5A1C8E4D2F90)
  - [Workflow](010_workflow.md#xid-7D1E1C0279F1)
- workflow-specific rules in each workflow page

## Related

- [Workflow](010_workflow.md#xid-7D1E1C0279F1)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
