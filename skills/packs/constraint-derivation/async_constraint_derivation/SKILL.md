<!-- xid: F6580A1C2346 -->
<a id="xid-F6580A1C2346"></a>

# Skill: async_constraint_derivation

## Purpose

Derive requirement confirmation gates from asynchronous and batch execution
structure before restart and recovery behavior becomes implicit.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Async constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/160_async_constraint_derivation_catalog.md#xid-72ECA94D1B35)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md#xid-FF9A33B945ED)

## Inputs

- queue designs, job definitions, batch specs, and schedule rules

## Outputs

- ACD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- rerun or restart matrices where required
- written output path

## Startup

- Confirm the input contains queue, job, batch, or schedule structure.
- Load the framework and the async catalog.
- Identify rerun, duplicate-start, partial-failure, and schedule-boundary surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_async_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate queue, job, batch, schedule, and state-management elements.
2. Apply the async catalog and assign `ACD-` ids.
3. Expand rerun or restart matrices where repeated or partial execution is possible.
4. Group the results by processing unit.
5. Keep unresolved restart, recovery, and schedule behavior explicit.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not assume successful rerun semantics from the platform alone.
- Stop if partial-failure handling or duplicate-start behavior is left unstated.
- Preserve traceability from each ACD item back to the execution structure.

## Closure

- Return the ACD table and grouped unresolved items.
- Highlight any restart, duplicate-run, or schedule gaps blocking implementation.
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
