---
schema_version: 1
skill_id: cross_constraint_derivation
xid: F4A8D2C6B190
aliases:
  - E5812C0D7FB7
  - E5812C0D7FB6
summary: compare DDL structure and C# processing structure to surface missing flows and implicit assumptions
applies_when:
  - source structure for this Skill may leave requirements implicit
exclusions:
  - Generic runtime possibilities without explicit structural evidence are outside this Skill
  - Implementation policy is not decided unless explicitly requested
inputs:
  - source material required by this Skill
outputs:
  - derivation basis table
  - confirmation items and remaining gaps
  - written output path
criteria:
  - id: evidence_boundary
    statement: Every derivation is grounded in explicit structural evidence and unsupported business meaning remains unresolved
    verification: Review each item against its source structure and record unresolved gaps
  - id: output_closure
    statement: The derivation output exists at the declared path and reports confirmation items and remaining gaps
    verification: Check the output path and closure report before handoff
knowledge_needs:
  - id: constraint_derivation_framework
    query: constraint derivation framework
    required_when: Required for this Skill's derivation and classification
    seed_xids:
      - 81A6C4E2B190
  - id: cross_constraint_derivation_catalog
    query: cross constraint derivation catalog
    required_when: Required for this Skill's derivation and classification
    seed_xids:
      - B2E5F9DA4C82
control_refs:
  - 111D282CA0EA
---
<!-- xid: F4A8D2C6B190 -->
<a id="xid-F4A8D2C6B190"></a>

# Skill: cross_constraint_derivation

## Purpose

Compare DDL and C# code as two projections of the same use case and surface
missing flows, undocumented assumptions, and duplicated rule ownership.

## Inputs

- DDL or schema definitions
- corresponding C# code
- optional mapping hints

## Outputs

- XCD-prefixed derivation basis table written to a Markdown file
- missing-flow confirmations
- implicit-assumption confirmations
- written output path

## Startup

- Confirm both DDL and code inputs exist.
- Load the framework and the cross-constraint catalog.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_cross_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Extract valid data-side variations from DDL.
2. Extract handled processing variations from code.
3. Compare the two sides for nullability, multiplicity, state coverage, FK behavior, validation ownership, and default handling.
4. Write the result by using `references/upward_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not silently choose DDL or code as the winner when they disagree.
- Stop if the comparison no longer points to a concrete structural mismatch.

## Closure

- Return the written output path.
- Return the highest-priority mismatches and remaining gaps.
