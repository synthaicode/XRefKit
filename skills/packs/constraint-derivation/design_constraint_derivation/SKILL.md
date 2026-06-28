<!-- xid: B214C6D8E012 -->
<a id="xid-B214C6D8E012"></a>

# Skill: design_constraint_derivation

## Purpose

Derive requirement confirmation gates from data-structure design before
implementation starts.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Design constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/120_design_constraint_derivation_catalog.md#xid-2D14F88A6C01)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md)

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
