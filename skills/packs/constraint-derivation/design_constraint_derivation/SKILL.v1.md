---
schema_version: 1
skill_id: design_constraint_derivation
xid: A6D9F3B1C720
aliases:
  - B214C6D8E012
  - B214C6D8E011
summary: derive requirement confirmation gates from data-structure, database, relationship, and operation design
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
  - id: design_constraint_derivation_catalog
    query: design constraint derivation catalog
    required_when: Required for this Skill's derivation and classification
    seed_xids:
      - 2D14F88A6C01
control_refs:
  - 111D282CA0EA
---
<!-- xid: A6D9F3B1C720 -->
<a id="xid-A6D9F3B1C720"></a>

# Skill: design_constraint_derivation

## Purpose

Derive requirement confirmation gates from data-structure design before
implementation starts.

## Inputs

- DDL, schema definitions, ER diagrams, and CRUD design notes

## Outputs

- DCD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- design-time decision list
- combination-expansion matrix when structurally required
- written output path

## Startup

- Confirm the input contains schema or operation structure.
- Load the framework and the design catalog.
- Identify any nullable, relational, state, or operation axes that may require matrix expansion.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_design_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate design elements by type, constraint, relation, operation, and business pattern.
2. Apply the design catalog mechanically and assign `DCD-` ids.
3. Separate requirement confirmations from design-time decisions.
4. Expand combination cases only when the design structure actually creates them.
5. Emit unresolved items as `未確定`; do not fill them in from implied defaults.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not collapse `null`, `0`, `not found`, and `multiple` into one vague case.
- Stop if the task tries to move into implementation before DCD items are confirmed.
- Keep the derivation basis traceable back to the design structure.

## Closure

- Return the derivation table and grouped unresolved items.
- Highlight any matrix expansions that must be confirmed before implementation.
- Return the written output path.
