<!-- xid: F6923D1E80C9 -->
<a id="xid-F6923D1E80C9"></a>

# Skill: integration_scenario_derivation

## Purpose

Derive integration-only failure, compensation, and replay scenarios from the
combination of persistence structure, processing order, and external
boundaries.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Integration scenario derivation catalog](../../../../knowledge/packs/constraint-derivation/210_integration_scenario_derivation_catalog.md#xid-C3F60AEB5D93)
- [Working area policy](../../../../docs/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Upward derivation output template](../references/upward_derivation_output_template.md)

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

