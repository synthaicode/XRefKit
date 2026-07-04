<!-- xid: 3D7A91B54210 -->
<a id="xid-3D7A91B54210"></a>

# Skill: design_flow

## Purpose

Execute `CAP-DSN-001` and prepare implementation-ready solution-design artifacts from planning outputs.

## Required Capability Definitions (XID)


## Inputs

- approved requirements
- work plan
- source modification policy
- current source structure findings for each implementation target
- data change policy
- planning basis source list

## Outputs

- approved design
- target paths
- source modification design
- data change design
- source analysis basis reference
- design basis policy reference
- change-design package for implementation

## Required Knowledge (XID)

- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)
- [Current source structure findings catalog](../../knowledge/source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0)

## Startup

- Confirm planning outputs exist.
- Confirm source modification policy and work plan are approved.
- Confirm each implementation target has current source structure findings in
  the canonical knowledge catalog.
- If a target lacks current source structure findings, route that target through
  `dotnet_change_analysis`, then publish or refresh the finding through
  `knowledge_ontology_management` before freezing the design for that target.
- Record `unknown` if required design inputs are missing.
- If the input still contains structural behavior that would otherwise be guessed during coding, route through `constraint_derivation_index` and the matching derivation Skills before closing design.

## Planning

- Define design scope and handoff boundaries.
- Treat this design work as change-design preparation, not as immediate implementation.
- Preserve which requirement difference and impacted target each design area addresses.
- Decide whether the incoming design material still needs constraint derivation:
  - DDL or schema behavior gaps
  - UI state or transition gaps
  - logic or state-transition gaps
  - integration, batch, or auth behavior gaps
- Decide whether current-source structure analysis is missing for any target:
  - no current source structure finding exists for the target in the canonical
    knowledge catalog
  - the finding predates the relevant source shape
  - the finding does not cover the target's structure pivots, route/usecase
    traces, implicit runtime bindings, or prohibited changes
  - the source modification policy relies on an unverified structure assumption
- Map the business activity to its supporting capability:
  - solution design drafting -> `CAP-DSN-001`
- Prepare management rows for design outputs and unresolved assumptions.

## Execution

- Perform solution design drafting by executing `CAP-DSN-001`.
- Before freezing implementation-facing design for each target, verify that the
  target has current source structure findings in the canonical knowledge
  catalog. When missing, run `dotnet_change_analysis` for that target and route
  its domain-knowledge candidate through `knowledge_ontology_management` so the
  canonical finding XID becomes the source analysis basis.
- When constraint derivation is required, treat its confirmed outputs as the gate before freezing implementation-facing behavior.
- Record the written derivation output path in the design artifacts or design basis reference when derivation was required.
- Record the canonical current-source-structure finding XID in the source
  analysis basis reference when source analysis was required.
- Record which planning policy and planning basis source entry each design artifact realizes.
- Describe the intended change method in design language before any implementation begins.
- Consolidate overlapping changes that hit the same location so implementation can modify the code in one coordinated pass.
- Produce implementation-ready design artifacts and preserve unresolved design assumptions explicitly.

## Monitoring and Control

- Check that all required design areas have a recorded result.
- Check that every implementation target either has current source structure
  findings in canonical knowledge or is explicitly out of scope for source
  modification.
- Downgrade weakly supported design assumptions to `unknown`.
- Downgrade design areas to `unknown` when the intended change method is not concrete enough to review before implementation.
- Stop if design closure would require implementing against a source target
  whose current structure has not been analyzed.
- Stop if design closure would force manufacturing to guess unresolved structural behavior that should have been derived first.
- Preserve unresolved design constraints for manufacturing handoff.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Confirm every source-modification target has a source analysis basis reference
  to a canonical finding XID or an explicit `out_of_scope` reason.
- Hand off the approved design package, design basis policy reference, and unresolved design items.
- Escalate out-of-scope design questions when reassignment is required.

## Rules

- Do not redefine business scope.
- Do not start manufacturing changes in this skill.
- Do not produce test artifacts in this skill.
- Do not leave implementation to infer the change method from broad intent alone.
- Do not freeze implementation-facing design for a source target without current
  source structure findings in canonical knowledge; create them with
  `dotnet_change_analysis` and publish them through `knowledge_ontology_management`
  first.
