---
schema_version: 1
skill_id: design_flow
xid: 6A4F8C2D1E70
aliases: [3D7A91B54210, 1B28D96E4C11]
summary: Prepare a human reviewed implementation ready solution design from approved planning outputs.
applies_when:
  - Approved requirements, a work plan, and source modification policy are available.
  - Each implementation target has a current canonical source structure finding, or a pre analysis handoff is required.
exclusions:
  - Starting manufacturing or test implementation.
  - Approving business scope or silently resolving missing evidence and decisions.
inputs:
  - Approved requirements, work plan, source modification policy, data change policy, and planning basis source list.
  - Canonical current source structure finding XIDs for each implementation target.
outputs:
  - Human reviewed approved design package and reviewer disposition.
  - Source, data, naming, XDDP traceability, design to test, and implementation handoff artifacts.
  - Source analysis basis, planning basis, and unresolved design item references.
criteria:
  - id: canonical_source_basis
    statement: Every in scope implementation target has a current canonical source structure finding XID, including naming evidence when an external or data flow name changes.
    verification: Inspect each target row and confirm its registered finding XID and Brownfield API Naming Extractor evidence, or an explicit out_of_scope or unknown handoff.
  - id: xddp_design_test_traceability
    statement: Every requirement difference and design item traces through impacted targets to implementation and test verification, with DB references or an explicit out_of_scope reason.
    verification: Review the XDDP matrix and design_to_test input package for complete forward and backward traceability.
  - id: human_design_approval
    statement: The design remains review_ready until human review findings are resolved or explicitly accepted and approval is recorded before manufacturing handoff.
    verification: Inspect reviewer findings, resolutions, accepted unknowns, approval owner, and handoff record.
  - id: unknown_stop_handoff
    statement: Missing evidence, unresolved structural behavior, database design gaps, and out_of_scope questions remain explicit with affected area and owner.
    verification: Check every unknown for reason, missing evidence or decision, downstream impact, and confirmation, derivation, analysis, or reassignment handoff.
knowledge_needs:
  - id: xddp_basics
    query: XDDP basics
    required_when: Required to structure requirement differences, design traceability, and design to test handoff.
    seed_xids: [7A2F4C8D1701]
  - id: xddp_supporting_methods
    query: XDDP supporting methods
    required_when: Required when selecting supporting design and traceability methods.
    seed_xids: [7A2F4C8D1711]
  - id: current_source_structure_findings_catalog
    query: current source structure findings catalog
    required_when: Required to select and validate canonical source analysis findings for implementation targets.
    seed_xids: [A9E742B1C6D0]
  - id: csharp_naming_convention_extraction
    query: CSharp naming convention extraction
    required_when: Required when a new or changed external specification or data flow element needs a brownfield name.
    seed_xids: [B4F7E1A2C903]
control_refs: []
---
<!-- xid: 6A4F8C2D1E70 -->
<a id="xid-6A4F8C2D1E70"></a>

# Skill: design_flow

## Purpose

Prepare an implementation ready solution design from approved planning outputs. This is change design preparation; it does not start manufacturing.

## Method

1. Confirm approved requirements, work plan, source modification policy, data change policy, planning basis source list, and canonical current source structure findings exist. Record `unknown` when an input is missing.
2. Resolve the needed XDDP and source analysis Knowledge. Use registered current source structure finding XIDs as the design basis. If a finding is missing, stale, lacks the required naming evidence, or does not cover the target's structure pivots and boundaries, stop design closure, tell the user that local source inspection is required, run `source_structure_overview`, publish through `source_structure_findings_registration`, and reload the registered XID.
3. Define design scope and handoff boundaries. Enumerate external specification and data flow elements first, then source modification points, persistence boundaries, error/retry/idempotency/ordering behavior, and other implementation details only where they affect an external contract or the change method.
4. Build the XDDP traceability matrix with requirement difference, classification, design item, external specification or data flow impact, impacted source or DB target, source analysis basis XID, design decision, implementation target, verification or test handoff, and unknown or handoff reference.
5. For every new or changed externally visible or data flow relevant name, derive local naming rules from the selected registered finding's Brownfield API Naming Extractor output and record candidate names, evidence scope, and unresolved naming assumptions. Do not invent names from a generic style guide or perform primary source scanning in this Skill.
6. Decide whether constraint derivation is required for DDL/schema, UI state, logic/state transitions, integrations, batch, or auth behavior. Route unresolved structural behavior through `constraint_derivation_index` and matching derivation Skills before freezing implementation facing behavior.
7. Decide whether database design is required. When schema, persistence, migration, data correction, ownership, transaction, consistency, idempotency, or concurrency changes are in scope, use `db_current_state_analysis` when current DB state is missing or stale, then `db_design`; record the DB design package path.
8. Draft the implementation ready design package, design basis policy reference, source analysis basis, naming output, and management rows. Include a design to test input package naming requirement differences, external and data flow changes, state or boundary changes, DB design references, verification points, and unknown or out_of_scope rows. Record the planning policy and planning basis source entry realized by each design artifact.
9. Keep every unknown explicit with its reason, missing evidence or decision, affected design area, downstream impact, and confirmation, derivation, analysis, or handoff owner. Downgrade weak assumptions and unclear change methods to `unknown`.
10. Obtain human review. Record findings, resolutions, accepted unknowns, reviewer and confirmation owner, and approval before handing the package to manufacturing or test design.

## Stop and handoff

- Stop if design closure would require implementing against a target without a current canonical source structure finding, or if required naming evidence is absent.
- Stop if manufacturing would need to guess structural behavior, required constraint derivation or DB design is absent, human review approval is absent, or the design to test package is missing.
- Do not redefine business scope, produce test artifacts, or hand off a design as approved before human review resolves or explicitly accepts findings.
- Hand off the approved design package, design basis policy reference, source analysis basis XIDs, design to test package, XDDP matrix, naming evidence and candidates, DB design package when applicable, and unresolved items to the next owner.
