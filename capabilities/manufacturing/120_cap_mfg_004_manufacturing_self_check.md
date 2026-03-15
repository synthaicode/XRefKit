<!-- xid: 6F5A9C1B4401 -->
<a id="xid-6F5A9C1B4401"></a>

# Capability: CAP-MFG-004 Manufacturing Self Check

## Definition

- capability_id: `CAP-MFG-004`
- capability_name: `manufacturing_self_check`
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

## Task Lifecycle Mapping

- Startup:
  - use `Preconditions`, `Trigger`, and `Inputs` to confirm the capability can start
  - if required evidence is missing, record `unknown` before continuing
- Planning:
  - define targets, work rows, and handoff boundaries for this capability
- Execution:
  - produce the outputs defined in this capability within its stated constraints
- Monitoring and Control:
  - check progress and evidence quality through management-table and metrics rules
  - downgrade weakly supported conclusions to `unknown`
- Closure:
  - confirm the capability result is finalized as `done`, `unknown`, or `out_of_scope`
  - preserve unresolved and out-of-scope items for handoff or escalation

