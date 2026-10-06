---
schema_version: 1
skill_id: integration_scenario_derivation
xid: 5F8B2D6A1C90
aliases: [F6923D1E80C8, F6923D1E80C9]
summary: derive integration-only failure and compensation scenarios from persistence, processing order, and external boundaries
applies_when:
  - DDL, code, and external-boundary specs may hide partial-failure, retry, or compensation scenarios
exclusions:
  - unit-level correctness alone is outside this integration-scenario scope
  - implementation policy is not decided unless explicitly requested
inputs: [DDL or schema definitions, processing-order-aware code, external boundary specs, optional retry or transaction notes]
outputs: [ISD derivation table, compensation-design items, partial-failure matrix, test candidates, written output path]
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
knowledge_needs:
  - id: constraint_derivation_framework
    query: constraint derivation framework
    required_when: Required for deriving integration scenarios
    seed_xids: [81A6C4E2B190]
  - id: integration_scenario_derivation_catalog
    query: integration scenario derivation catalog
    required_when: Required for selecting scenario categories
    seed_xids: [C3F60AEB5D93]
control_refs: [111D282CA0EA]
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
