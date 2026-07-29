<!-- xid: D4701BFC6EA5 -->
<a id="xid-D4701BFC6EA5"></a>

# Skill: code_constraint_derivation

## Purpose

Derive hidden assumptions and selected business constraints from explicit C#
code choices without treating generic runtime possibilities as business
signals.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Code constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/190_code_constraint_derivation_catalog.md#xid-A1D4E8C93B71)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Upward derivation output template](../references/upward_derivation_output_template.md#xid-3266CDEF3729)

## Inputs

- C# code files
- optional target classes or methods
- optional related design context

## Outputs

- CCD-prefixed derivation basis table written to a Markdown file
- high-priority confirmation items
- implementation-layer notes when justified
- written output path

## Startup

- Confirm the code input exists.
- Load the framework and the code-constraint catalog.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_code_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Detect explicit code-choice signals such as guard-plus-throw, silent failure, multiplicity assumptions, magic values, transaction spans, and visibility choices.
2. Ignore generic runtime possibilities that do not represent an explicit code choice.
3. Classify each signal by whether it requires business-layer confirmation or implementation-layer recording.
4. Write the result by using `references/upward_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not turn generic exceptions such as overflow or out-of-memory into business confirmation items.
- Stop if the interpretation depends on business meaning that is not supported by the code shape.

## Closure

- Return the written output path.
- Return the high-priority confirmation items and remaining gaps.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
