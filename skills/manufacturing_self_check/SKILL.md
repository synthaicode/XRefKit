<!-- xid: 5D4E91B0D110 -->
<a id="xid-5D4E91B0D110"></a>

# Skill: manufacturing_self_check

## Purpose

Execute `CAP-MFG-004` and verify that manufacturing outputs remain aligned with approved design before external QA review.

## Required Capability Definitions (XID)

- [CAP-MFG-004 Manufacturing Self Check](../../capabilities/manufacturing/120_cap_mfg_004_manufacturing_self_check.md#xid-6F5A9C1B4401)

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Inputs

- implemented code
- approved design
- unit test results
- coding rules

## Outputs

- self-check result
- design-alignment findings
- unresolved list
- execution metrics log

## Startup

- Confirm implemented code exists.
- Confirm approved design evidence exists.
- Confirm unit-test evidence exists.
- Record `unknown` if required evidence is missing.

## Planning

- Define self-check targets by file, module, or change area.
- Prepare management rows for alignment findings and unresolved items.

## Execution

- Compare implemented code against approved design evidence.
- Check whether local changes stay inside approved boundaries.
- Produce self-check findings and explicit unresolved items.

## Monitoring and Control

- Downgrade unsupported alignment claims to `unknown`.
- Preserve explicit design gaps and out-of-scope reasons.
- Attach execution metrics to the result.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off self-check results to quality-group review.
- Escalate out-of-scope items when reassignment is required.

## Rules

- This is manufacturing-side self-control, not an independent QA substitute.
- Every finding must map back to design evidence or an explicit evidence gap.
- Do not silently change design policy.

