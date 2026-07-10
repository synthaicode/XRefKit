<!-- xid: A7691B2D3457 -->
<a id="xid-A7691B2D3457"></a>

# Skill: auth_constraint_derivation

## Purpose

Derive requirement confirmation gates from authentication and authorization
structure before access behavior is completed implicitly.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Auth constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/170_auth_constraint_derivation_catalog.md#xid-8B14D9E70326)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md#xid-FF9A33B945ED)

## Inputs

- auth design docs, role matrices, permission models, and account rules

## Outputs

- AACD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- session or permission matrices where required
- written output path

## Startup

- Confirm the input contains authentication or authorization structure.
- Load the framework and the auth catalog.
- Identify session, role, tenant, client-auth, and account-lifecycle surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_auth_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate authentication, authorization, client-auth, and account-management elements.
2. Apply the auth catalog and assign `AACD-` ids.
3. Expand permission or session matrices where the design exposes those axes.
4. Group the results by auth surface.
5. Keep unresolved security behavior explicit instead of assuming safe defaults.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not infer permission behavior from UI visibility alone.
- Stop if session-expiry, role gaps, or tenant-boundary behavior is left implicit.
- Preserve explicit traceability from each AACD item back to the access structure.

## Closure

- Return the AACD table and grouped unresolved items.
- Highlight any session or permission gaps blocking implementation.
- Return the written output path.
