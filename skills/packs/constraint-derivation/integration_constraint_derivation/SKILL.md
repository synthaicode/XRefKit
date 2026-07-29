<!-- xid: E547F90B1235 -->
<a id="xid-E547F90B1235"></a>

# Skill: integration_constraint_derivation

## Purpose

Derive requirement confirmation gates from external integration structure before
failure handling gets completed implicitly.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Integration constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/150_integration_constraint_derivation_catalog.md#xid-6F0D7C1A2E44)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md#xid-FF9A33B945ED)

## Inputs

- API specs, webhook definitions, file contracts, and messaging designs

## Outputs

- ICD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- retry or idempotency matrices where required
- written output path

## Startup

- Confirm the input contains external integration structure.
- Load the framework and the integration catalog.
- Identify retry, timeout, ordering, and idempotency surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_integration_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate API, webhook, file, message, and external-service interaction points.
2. Apply the integration catalog and assign `ICD-` ids.
3. Expand retry or idempotency matrices where repeated execution is possible.
4. Group the results by integration surface.
5. Keep unresolved timeout, retry, ordering, and confirmation behavior explicit.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not assume provider defaults satisfy the business requirement.
- Stop if retry or duplicate-delivery behavior is left implicit.
- Preserve explicit links from each ICD item back to the integration structure.

## Closure

- Return the ICD table and grouped unresolved items.
- Highlight any retry, timeout, or idempotency gaps blocking implementation.
- Return the written output path.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
