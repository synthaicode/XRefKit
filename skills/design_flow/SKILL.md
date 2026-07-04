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
- pre-analyzed current source structure findings for each implementation target,
  registered as canonical domain knowledge
- data change policy
- planning basis source list

## Outputs

- approved design
- human-reviewed design result with resolved issues, remaining approved
  unknowns, and reviewer/confirmation owner
- target paths
- source modification design
- data change design
- brownfield naming-rule basis and candidate names for new or changed external
  specification and data-flow elements
- Brownfield API Naming Extractor section or equivalent naming-rule output from
  the selected current-source-structure finding
- source analysis basis reference
- current-source-structure finding XIDs used as design inputs
- created or refreshed current-source-structure finding XIDs when pre-analysis
  was missing or stale
- design basis policy reference
- change-design package for implementation
- design-to-test input package for `test_flow`, including XDDP traceability rows,
  external specification and data-flow impacts, acceptance/verification points,
  DB design references, unknown items, and out-of-scope reasons
- XDDP traceability matrix from requirement differences to design items,
  impacted targets, source-analysis basis, implementation targets, DB design
  package references, derivation outputs, and unknown items
- unknown design item list with reason, missing evidence or missing decision,
  affected design area, downstream impact, and handoff or confirmation owner

## Required Knowledge (XID)

- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)
- [Current source structure findings catalog](../../knowledge/source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0)
- [CSharp naming-convention extraction](../../knowledge/source_analysis/140_csharp_naming_convention_extraction.md#xid-B4F7E1A2C903)

## Design Elements

In this Skill, design elements mainly mean the parts that affect external
specification or data flow.

Primary design elements:

- external API, message, file, screen, batch, auth, permission, or integration
  contracts
- input, output, transformation, routing, persistence, publication, and
  consumption paths in the data flow
- schema, DDL, entity, topic, queue, event, cache, state, and storage boundaries
- configuration or environment-controlled behavior that changes external
  behavior or data-flow behavior
- error, retry, compensation, idempotency, ordering, consistency, and
  concurrency behavior visible at an external boundary or data-flow boundary
- source modification points required to realize the above without changing
  unrelated implementation structure

Secondary implementation-only details are design elements only when they change
an external specification, data-flow behavior, or the source modification method
that implementation must follow.

Brownfield naming is part of the design element when a new or changed element
will be visible in an external specification, data-flow path, runtime binding,
or source modification point. Derive candidate names from existing local names
and de-facto rules before proposing new names. Do not invent names from generic
style guides when the existing codebase provides a local rule.

## Startup

- Confirm planning outputs exist.
- Confirm source modification policy and work plan are approved.
- Confirm each implementation target has pre-analyzed current source structure
  findings registered as canonical domain knowledge.
- Use the registered finding XIDs as the source-analysis basis for design.
- For any target where the design changes externally visible or
  data-flow-relevant names, confirm the selected source-structure finding
  contains Brownfield API Naming Extractor output or equivalent naming-rule
  evidence.
- If a target lacks registered current source structure findings, or the
  finding is stale, perform the pre-analysis first. Tell the user that this run
  must inspect local source files to create or refresh the baseline structure
  information, then run `source_structure_overview` for that local source scope.
  Publish or refresh the canonical finding through
  `source_structure_findings_registration`, then reload the registered XID as
  the design input before freezing the design for that target.
- Record `unknown` if required design inputs are missing.
- If the input still contains structural behavior that would otherwise be guessed during coding, route through `constraint_derivation_index` and the matching derivation Skills before closing design.
- If the design includes database schema, persistence behavior, migration,
  data correction, or data ownership changes, route the DB portion through
  `db_current_state_analysis` when current DB state is missing or stale, then
  `db_design` before freezing implementation-facing design.

## Planning

- Define design scope and handoff boundaries.
- Treat this design work as change-design preparation, not as immediate implementation.
- Treat the design output as review-ready until a human review resolves or
  accepts design issues. Only a reviewed and approved design package becomes
  input to manufacturing.
- Preserve which requirement difference and impacted target each design area addresses.
- Define the XDDP traceability matrix columns before drafting design content:
  requirement difference, change/addition classification, design item,
  external specification or data-flow impact, impacted source/DB target,
  source-analysis basis XID, design decision, implementation target,
  verification or test handoff, and unknown or handoff reference.
- Define the design-to-test input package before closure. It must identify the
  requirement differences, external specification changes, data-flow changes,
  state or boundary changes, DB design references, verification points, and
  unknown/out-of-scope rows that `test_flow` must use.
- Enumerate design elements by focusing first on external specification impact
  and data-flow impact.
- For new or changed external specification and data-flow elements, derive
  local naming rules from the selected source-structure finding's Brownfield
  API Naming Extractor output before proposing names.
- Prepare candidate names with their rule basis, evidence scope, and unresolved
  naming assumptions.
- Decide whether the incoming design material still needs constraint derivation:
  - DDL or schema behavior gaps
  - UI state or transition gaps
  - logic or state-transition gaps
  - integration, batch, or auth behavior gaps
- Decide whether current-source structure analysis is missing for any target:
  - no current source structure finding exists for the target in the canonical
    knowledge catalog
  - the finding predates the relevant source shape
  - the finding does not cover the target's structure pivots, runtime flows,
    state/persistence boundaries, extension/convention mechanisms, variation
    points, or unresolved verification needed for implementation-facing design
  - the design requires externally visible or data-flow-relevant names, but the
    finding does not contain Brownfield API Naming Extractor output or
    equivalent naming-rule evidence
  - the source modification policy relies on an unverified structure assumption
- When missing current structure is detected, create design work rows for:
  - pre-analysis with latest source-structure overview creation
  - canonical source-structure finding registration as domain knowledge
  - reloading the registered finding XID as the design source-analysis basis
- Decide whether database design is required:
  - schema, DDL, table, column, index, constraint, migration, ORM mapping, raw
    SQL, seed data, report, data correction, or persistence ownership changes
    are in scope
  - data change policy requires migration, backfill, reconciliation, rollback,
    or a dedicated correction tool
  - the design changes transaction, consistency, idempotency, concurrency, or
    read/write ownership
- When database design is required, create a design work row for `db_design`
  and, when the current DB state is missing or stale, a preceding work row for
  `db_current_state_analysis`. Use the DB design package as part of this
  Skill's design output.
- Map the business activity to its supporting capability:
  - solution design drafting -> `CAP-DSN-001`
- Prepare management rows for design outputs and unresolved assumptions.

## Execution

- Perform solution design drafting by executing `CAP-DSN-001`.
- Before freezing implementation-facing design for each target, verify that the
  target's pre-analysis exists as canonical domain knowledge and that its XID is
  recorded as the source-analysis basis. When missing or stale, run
  `source_structure_overview` for that target only after telling the user that
  local source inspection is required for the current run, then route its output
  through `source_structure_findings_registration` so the canonical finding XID
  becomes the design input.
- Use `dotnet_change_analysis` only for proposition-specific structure and
  impact analysis after the baseline source-structure finding exists or when a
  change objective requires additional change-specific coverage.
- When constraint derivation is required, treat its confirmed outputs as the gate before freezing implementation-facing behavior.
- When database design is required, run `db_design` or incorporate its existing
  DB design package before finalizing the implementation-facing design.
- When database current state is missing or stale, run
  `db_current_state_analysis` before `db_design`.
- Record the written derivation output path in the design artifacts or design basis reference when derivation was required.
- Record the DB design package path in the design artifacts or design basis
  reference when database design was required.
- Record the canonical current-source-structure finding XID in the source
  analysis basis reference when source analysis was required.
- Record which planning policy and planning basis source entry each design artifact realizes.
- Maintain the XDDP traceability matrix while drafting. Every design item must
  trace back to a requirement difference and forward to an implementation
  target, DB design package reference, verification/test handoff, explicit
  `unknown`, or `out_of_scope` reason.
- Record the brownfield naming rule used for each new or changed externally
  visible or data-flow-relevant element, then list the candidate name or names
  and the selected source-structure finding section that made them plausible.
- Describe the intended change method in design language before any implementation begins.
- Consolidate overlapping changes that hit the same location so implementation can modify the code in one coordinated pass.
- Produce implementation-ready design artifacts and preserve unresolved design assumptions explicitly.
- Produce design artifacts for human review first. Record review findings,
  resolutions, accepted unknowns, and remaining handoff owners before marking
  the design as approved for manufacturing or test design.
- For every design item marked `unknown`, record why it is unknown, which
  evidence or decision is missing, which design area and downstream work it
  affects, and whether the next action is user confirmation, source/database
  pre-analysis, constraint derivation, or out-of-scope handoff.

## Monitoring and Control

- Check that all required design areas have a recorded result.
- Check that every new or changed external specification or data-flow element
  has a naming-rule basis and candidate name, or an explicit `unknown`.
- Check that naming-rule basis comes from a registered source-structure finding
  XID, not from ad hoc local inspection in `design_flow`.
- Check that every implementation target either has current source structure
  findings in canonical knowledge or is explicitly out of scope for source
  modification.
- Check that the XDDP traceability matrix contains no untraced design item,
  untraced requirement difference, or implementation target that lacks a
  design-basis row.
- Downgrade weakly supported design assumptions to `unknown`.
- Downgrade design areas to `unknown` when the intended change method is not concrete enough to review before implementation.
- Do not leave an `unknown` as a bare label. Each `unknown` must be visible in
  the design package with its reason, missing evidence or missing decision,
  affected external specification, data-flow, source, or DB area, implementation
  impact, and required owner or handoff.
- Stop if design closure would require implementing against a source target
  whose current structure has not been analyzed.
- Stop if design closure would force manufacturing to guess unresolved structural behavior that should have been derived first.
- Stop if database design is required but no DB design package is present.
- Stop if the design has not been reviewed and approved for manufacturing input.
- Stop if the design-to-test input package is missing for a change that requires
  test planning or test-item design.
- Preserve unresolved design constraints for manufacturing handoff.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Confirm human review has been performed, review findings are resolved or
  explicitly accepted, and the design is approved before it is handed to
  manufacturing.
- Confirm every `unknown` row has a reason, missing-evidence or
  missing-decision note, affected area, downstream impact, and handoff or
  confirmation owner.
- Confirm every source-modification target has a source analysis basis reference
  to a canonical finding XID or an explicit `out_of_scope` reason.
- Confirm the XDDP traceability matrix is included in the design package and
  links each requirement difference to design items, impacted source/DB targets,
  basis XIDs, implementation targets, verification/test handoff, and unresolved
  `unknown` or `out_of_scope` rows.
- Confirm naming candidates for external specification and data-flow elements
  are included in the design package with their selected source-structure
  finding XID and Brownfield API Naming Extractor evidence.
- Confirm database design package path is included when database schema,
  persistence, migration, data correction, or data ownership changes are in
  scope.
- Confirm the design-to-test input package is included so `test_flow` can derive
  the test plan, test design, integration/regression design, and traceability
  from the same approved design basis.
- Hand off the approved design package, design basis policy reference,
  design-to-test input package, and unresolved design items.
- Escalate out-of-scope design questions when reassignment is required.

## Rules

- Do not redefine business scope.
- Do not start manufacturing changes in this skill.
- Do not produce test artifacts in this skill.
- Do not hand off a design package to manufacturing as approved before human
  review has resolved or explicitly accepted design findings.
- Do not make `test_flow` infer its scope from broad design prose; provide the
  design-to-test input package and XDDP traceability basis.
- Do not leave implementation to infer the change method from broad intent alone.
- Do not leave names for new or changed external specification or data-flow
  elements for implementation to invent; provide brownfield naming candidates
  from the registered source-structure finding's naming rules.
- Do not perform primary source scanning for naming in this Skill. If the
  selected source-structure finding lacks required naming evidence, route back
  to `source_structure_overview` and `source_structure_findings_registration`.
- Do not freeze implementation-facing design for a source target without current
  source structure findings already available as canonical domain knowledge;
  when missing or stale, tell the user that local source inspection is required,
  perform pre-analysis with `source_structure_overview`, and publish it through
  `source_structure_findings_registration` first.
- Do not use a local analysis artifact as the design source-analysis basis until
  it has been registered as canonical domain knowledge.
