<!-- xid: D436E8FA0124 -->
<a id="xid-D436E8FA0124"></a>

# Skill: logic_constraint_derivation

## Purpose

Derive requirement confirmation gates from business-logic structure before
exception paths are filled in implicitly.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Logic constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/140_logic_constraint_derivation_catalog.md#xid-4E5B8923C912)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md)

## Inputs

- logic specs, flowcharts, calculations, and state-transition definitions

## Outputs

- LCD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- state-transition matrix when required
- written output path

## Startup

- Confirm the input contains branch, calculation, or transition structure.
- Load the framework and the logic catalog.
- Identify where transition matrices or boundary cases are structurally required.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_logic_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate branches, calculations, transitions, approvals, and control rules.
2. Apply the logic catalog and assign `LCD-` ids.
3. Expand transition matrices where the design exposes current-state and action axes.
4. Group the results by logic unit.
5. Keep unresolved branches, invalid values, and boundary behavior explicit.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not accept a single happy-path example as full logic coverage.
- Stop if invalid transitions or boundary calculations are being skipped.
- Preserve the difference between confirmed rules and unconfirmed cases.

## Closure

- Return the LCD table and grouped unresolved items.
- Highlight any transition or calculation matrices that block implementation.
- Return the written output path.
