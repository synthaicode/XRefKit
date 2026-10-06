---
schema_version: 1
skill_id: integration_scenario_derivation
xid: 5F8B2D6A1C90
summary: derive integration-only failure and compensation scenarios from persistence, processing order, and external boundaries
applies_when:
- DDL, code, and external-boundary specs together may hide partial-failure, retry, or compensation scenarios that unit-level reasoning misses
exclusions:
- unit-level correctness alone is outside this integration-scenario scope
- implementation policy is not decided unless explicitly requested
inputs:
- DDL or schema definitions, processing-order-aware code, external API or boundary specs, and optional retry or transaction notes
outputs:
- ISD-prefixed derivation file under `work/constraint_derivation/` by default, plus compensation-design items, partial-failure matrices, and post-confirmation test candidates
criteria:
- id: boundary_evidence
  statement: Every scenario is grounded in an ordered boundary crossing or persistence point.
  verification: Check each scenario against the supplied DDL, code, and external-boundary evidence.
- id: compensation_coverage
  statement: Partial failure, replay, retry, and compensation questions remain explicit.
  verification: Review the matrix and unresolved items for each boundary sequence.
- id: output_closure
  statement: The ISD result exists at the declared output path with remaining gaps.
  verification: Check the output path before handoff.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: constraint_derivation_framework
  query: constraint derivation framework
  required_when: Required for deriving integration scenarios
  seed_xids:
  - 81A6C4E2B190
- id: integration_scenario_derivation_catalog
  query: integration scenario derivation catalog
  required_when: Required for selecting scenario categories
  seed_xids:
  - C3F60AEB5D93
control_refs:
- 111D282CA0EA
aliases:
- F6923D1E80C8
- F6923D1E80C9
---
<!-- xid: 5F8B2D6A1C90 -->
<a id="xid-5F8B2D6A1C90"></a>

# Skill: integration_scenario_derivation

## Purpose
Derive integration-only failure, compensation, and replay scenarios from persistence structure, processing order, and external boundaries.

## Inputs
- DDL or schema definitions
- processing-order-aware code
- external API or boundary specs
- optional retry or transaction notes

## Outputs
- ISD-prefixed derivation basis table
- compensation-design items
- partial-failure matrix
- post-confirmation test candidates
- written output path

## Startup
- Confirm DDL, code, and boundary inputs exist.
- Load framework and integration-scenario catalog Knowledge.
- Use `work/constraint_derivation/YYYY-MM-DD_integration_scenario_derivation_<topic>.md` unless an output path is supplied.

## Execution
1. Identify ordered boundary crossings such as DB save, external call, follow-up update, and retry surfaces.
2. Derive partial-failure and replay scenarios from those interactions.
3. Separate compensation-design items, implementation notes, and test candidates.
4. Write the result using the upward derivation output template or an equivalent structure.

## Monitoring and Control
- Do not treat unit-level correctness as proof of integration correctness.
- Stop if the scenario no longer depends on actual boundary crossing or state progression.

## Closure and Handoff
- Return the written path, compensation-design items, and remaining gaps.
- Hand unresolved compensation decisions to the design owner.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: integration_scenario_derivation

## Purpose

Derive integration-only failure, compensation, and replay scenarios from the
combination of persistence structure, processing order, and external
boundaries.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Integration scenario derivation catalog](../../../../knowledge/packs/constraint-derivation/210_integration_scenario_derivation_catalog.md#xid-C3F60AEB5D93)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Upward derivation output template](../references/upward_derivation_output_template.md#xid-3266CDEF3729)

## Inputs

- DDL or schema definitions
- processing-order-aware code
- external API or boundary specs
- optional retry or transaction notes

## Outputs

- ISD-prefixed derivation basis table written to a Markdown file
- compensation-design items
- partial-failure matrix
- post-confirmation test candidates
- written output path

## Startup

- Confirm DDL, code, and boundary inputs exist.
- Load the framework and the integration-scenario catalog.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_integration_scenario_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Identify ordered boundary crossings such as DB save, external call, follow-up update, and retry surfaces.
2. Derive partial-failure and replay scenarios from the interaction among those steps.
3. Separate compensation-design items from implementation-design items and from later test-case candidates.
4. Write the result by using `references/upward_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not treat unit-level correctness as proof of integration correctness.
- Stop if the scenario no longer depends on actual boundary crossing or state progression.

## Closure

- Return the written output path.
- Return the compensation-design items and remaining gaps.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: derive integration-only failure and compensation scenarios from DDL, processing order, and external system boundaries

- use_when: DDL, code, and external-boundary specs together may hide partial-failure, retry, or compensation scenarios that unit-level reasoning misses

- input: DDL or schema definitions, processing-order-aware code, external API or boundary specs, and optional retry or transaction notes

- output: ISD-prefixed derivation file under `work/constraint_derivation/` by default, plus compensation-design items, partial-failure matrices, and post-confirmation test candidates

- constraints: focus on boundary-crossing state progression rather than isolated method correctness; keep compensation and retry questions explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm DDL, code, and boundary inputs exist and load the framework plus the integration-scenario catalog
  - planning: identify ordered boundary crossings, persistence points, and retry surfaces
  - execution: derive partial-failure scenarios, compensation questions, and write the ISD result file
  - monitoring_and_control: stop if unit-level success is being mistaken for boundary-level correctness
  - closure: return the written derivation path, compensation-design items, and remaining gaps

- tags: `review`, `integration`, `requirements-derivation`

- knowledge_slots:
  - name=working_area_policy; bind=111D282CA0EA
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=integration_scenario_derivation_catalog; bind=C3F60AEB5D93

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
