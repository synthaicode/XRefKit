---
schema_version: 1
skill_id: design_flow
xid: 6A4F8C2D1E70
summary: Prepare a human reviewed implementation ready solution design from approved planning outputs.
applies_when:
- user needs implementation-ready design after planning outputs are approved
exclusions:
- Starting manufacturing or test implementation.
- Approving business scope or silently resolving missing evidence and decisions.
inputs:
- approved requirements, work plan, source modification policy, pre-analyzed current source structure findings from canonical domain knowledge for each implementation target, Brownfield API Naming Extractor output from the selected source-structure finding when naming is design-relevant, data change policy, planning basis source list, and DB design package when database schema/persistence/migration/data-correction changes are in scope
outputs:
- human-reviewed approved design, reviewer result with resolved findings and accepted unknowns, target paths, source modification design, data change design, DB design package reference when required, brownfield naming-rule basis and candidate names for external specification and data-flow elements backed by selected source-structure finding XIDs, source analysis basis reference, current-source-structure finding XIDs used as design inputs, created or refreshed current-source-structure finding XIDs when pre-analysis was missing or stale, design basis policy reference, referenced constraint-derivation output paths when derivation was required, design-to-test input package, XDDP traceability matrix from requirement differences to design items, impacted targets, basis XIDs, implementation targets, verification/test handoff, and unknown or out-of-scope rows, and unknown design item list with reason, missing evidence or missing decision, affected area, downstream impact, and handoff or confirmation
  owner
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
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: xddp_basics
  query: XDDP basics
  required_when: Required to structure requirement differences, design traceability, and design to test handoff.
  seed_xids:
  - 7A2F4C8D1701
- id: xddp_supporting_methods
  query: XDDP supporting methods
  required_when: Required when selecting supporting design and traceability methods.
  seed_xids:
  - 7A2F4C8D1711
- id: current_source_structure_findings_catalog
  query: current source structure findings catalog
  required_when: Required to select and validate canonical source analysis findings for implementation targets.
  seed_xids:
  - A9E742B1C6D0
- id: csharp_naming_convention_extraction
  query: CSharp naming convention extraction
  required_when: Required when a new or changed external specification or data flow element needs a brownfield name.
  seed_xids:
  - B4F7E1A2C903
control_refs: []
aliases:
- 3D7A91B54210
- 1B28D96E4C11
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

## Additional bound references retained at repository cutover

These references were explicitly bound by the prior repository Skill. Apply them to the relevant method work; resolve their XIDs on demand.

- [Constraint Derivation Framework](../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

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

- summary: execute design business activity through reusable solution-design capability

- use_when: user needs implementation-ready design after planning outputs are approved

- input: approved requirements, work plan, source modification policy, pre-analyzed current source structure findings from canonical domain knowledge for each implementation target, Brownfield API Naming Extractor output from the selected source-structure finding when naming is design-relevant, data change policy, planning basis source list, and DB design package when database schema/persistence/migration/data-correction changes are in scope

- output: human-reviewed approved design, reviewer result with resolved findings and accepted unknowns, target paths, source modification design, data change design, DB design package reference when required, brownfield naming-rule basis and candidate names for external specification and data-flow elements backed by selected source-structure finding XIDs, source analysis basis reference, current-source-structure finding XIDs used as design inputs, created or refreshed current-source-structure finding XIDs when pre-analysis was missing or stale, design basis policy reference, referenced constraint-derivation output paths when derivation was required, design-to-test input package, XDDP traceability matrix from requirement differences to design items, impacted targets, basis XIDs, implementation targets, verification/test handoff, and unknown or out-of-scope rows, and unknown design item list with reason, missing evidence or missing decision, affected area, downstream impact, and handoff or confirmation owner

- constraints: preserve unresolved design assumptions explicitly; do not redefine business scope; express the change method clearly enough for pre-code review; keep design output review-ready until human review resolves findings or explicitly accepts unknowns; do not hand off design to manufacturing as approved before human review; provide a design-to-test input package so test_flow does not infer test scope from broad prose; derive candidate names for new or changed external specification and data-flow elements from the selected source-structure finding's Brownfield API Naming Extractor output instead of leaving naming to implementation or doing ad hoc source scanning in design; use pre-analyzed current source structure findings from canonical domain knowledge as the design source-analysis basis; when a source target lacks current source structure findings, the finding is stale, or naming evidence is missing for a design-relevant naming surface, perform pre-analysis with `source_structure_overview` and publish it through `source_structure_findings_registration` before freezing implementation-facing design; route database schema, persistence behavior, migration, data correction, and data ownership changes through `db_current_state_analysis` when current DB state is missing or stale, then `db_design` before implementation-facing closure; use `dotnet_change_analysis` for proposition-specific structure and impact analysis after the baseline source-structure finding exists or when the change objective needs additional coverage; when structural design artifacts still imply unresolved behavior, route through the constraint-derivation pack before freezing implementation-facing design

- lifecycle:
  - startup: confirm planning outputs, source modification policy, and pre-analyzed current source structure findings in canonical domain knowledge for each implementation target exist; if current source findings are missing, stale, or lack required Brownfield API Naming Extractor output, require `source_structure_overview` plus `source_structure_findings_registration` publication before design input is accepted; if unresolved structural design behavior remains, require constraint derivation before design closure
  - planning: define design scope, change-design boundaries, XDDP traceability matrix columns, management rows, naming-rule usage needs for external specification and data-flow elements, database current-state and design needs, whether canonical source pre-analysis or naming evidence is missing or stale, required pre-analysis/registration rows, and whether constraint derivation is required before implementation-facing decisions
  - execution: perform solution design drafting through `CAP-DSN-001`, use registered current source structure finding XIDs as design inputs, maintain XDDP traceability from requirement differences to design items and implementation/test handoff, prepare the design-to-test input package, create missing current source structure findings with `source_structure_overview`, publish or refresh the canonical finding through `source_structure_findings_registration`, preserve the intended change method explicitly, derive brownfield naming candidates from the selected source-structure finding's naming output, incorporate DB current-state analysis and DB design package output when database changes are in scope, incorporate confirmed derivation outputs where structural ambiguity existed, and record human review findings plus resolutions before approval
  - monitoring_and_control: downgrade weak design assumptions, unclear change methods, missing naming evidence, missing DB current-state analysis, missing DB design package, unsupported naming candidates, untraced design items, missing human review, or missing design-to-test input package to `unknown`; require every unknown to include reason, missing evidence or missing decision, affected area, downstream impact, and handoff or confirmation owner; stop if implementation-facing design would be frozen for a source target without canonical current source structure findings, human review approval, or required constraint derivation
  - closure: finalize states and hand off the human-reviewed approved design package, design-to-test input package, XDDP traceability matrix, naming-rule basis and candidate names, source analysis basis finding XIDs, design basis policy reference, unknown design item list, and unresolved items

- tags: `design`, `execution`, `implementation-preparation`

- knowledge_slots:
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=current_source_structure_findings_catalog; bind=A9E742B1C6D0
  - name=csharp_naming_convention_extraction; bind=B4F7E1A2C903
