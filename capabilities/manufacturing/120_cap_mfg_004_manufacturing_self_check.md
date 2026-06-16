<!-- xid: 6F5A9C1B4401 -->
<a id="xid-6F5A9C1B4401"></a>

# Capability: CAP-MFG-004 Design Alignment Self Evaluation

## Definition

- capability_id: `CAP-MFG-004`
- capability_name: `design_alignment_self_evaluation`
- work_type: `judgment`
- summary: verify that manufacturing outputs remain aligned with approved design before external QA review

## Preconditions

- implemented code exists
- approved design evidence exists
- unit test results or equivalent implementation evidence exist

## Trigger

- implementation and local testing complete
- before quality-group review starts

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

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- design evidence
- coding rules
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Constraints

- perform manufacturing-side alignment checking only
- do not replace independent quality-group review
- preserve evidence gaps explicitly as `unknown`

## Assignment

- manufacturing phase
- [Manufacturing Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `manufacturing self check` is a business activity in manufacturing work.
- This capability is the reusable self-evaluation ability used by that activity.
