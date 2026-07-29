<!-- xid: E5812C0D7FB7 -->
<a id="xid-E5812C0D7FB7"></a>

# Skill: cross_constraint_derivation

## Purpose

Compare DDL and C# code as two projections of the same use case and surface
missing flows, undocumented assumptions, and duplicated rule ownership.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Cross constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/200_cross_constraint_derivation_catalog.md#xid-B2E5F9DA4C82)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Upward derivation output template](../references/upward_derivation_output_template.md#xid-3266CDEF3729)

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

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
