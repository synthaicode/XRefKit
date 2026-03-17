<!-- xid: 837CDB1183C9 -->
<a id="xid-837CDB1183C9"></a>

# Capability: CAP-BIZ-001 Value-Constraint Alignment Evaluation

## Definition

- capability_id: `CAP-BIZ-001`
- capability_name: `value_constraint_alignment_evaluation`
- work_type: `judgment`
- summary: evaluate whether the release still fits the intended value, constraints, and priorities

## Preconditions

- release-plan materials exist
- original value and constraint definitions exist

## Trigger

- CAB preparation starts

## Inputs

- value definition
- constraint definition
- priority definition
- release summary

## Outputs

- value-gate result
- findings with evidence
- unresolved list

## Required Domain Knowledge

- business rules
- SLA definitions
- contract constraints
- budget definitions

## Constraints

- evaluate only
- do not decide final release approval
- every judgment needs evidence

## Assignment

- CAB preparation
- [Planning Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `value and constraint fit evaluation` is a business activity in CAB preparation.
- This capability is the reusable alignment-evaluation ability used by that activity.
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


