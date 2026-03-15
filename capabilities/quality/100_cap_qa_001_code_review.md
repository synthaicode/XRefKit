<!-- xid: 7E9CCEBEDA2D -->
<a id="xid-7E9CCEBEDA2D"></a>

# Capability: CAP-QA-001 Code Review

## Definition

- capability_id: `CAP-QA-001`
- capability_name: `code_review`
- work_type: `judgment`
- summary: review implemented code against design evidence and coding rules

## Preconditions

- implemented code exists
- design evidence exists
- coding rules are available

## Trigger

- `CAP-MFG-001` or `CAP-MFG-002` completes

## Inputs

- implemented code
- design document
- coding rules

## Outputs

- pass or fail judgment
- finding list with evidence
- uncertainty list for evidence gaps

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- review criteria
- coding rules
- local design patterns when applicable

## Constraints

- every judgment must cite evidence
- if evidence is insufficient, mark as `unknown`
- do not decide implementation policy

## Assignment

- quality review step
- [Quality Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)
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

- execution metrics log
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)



