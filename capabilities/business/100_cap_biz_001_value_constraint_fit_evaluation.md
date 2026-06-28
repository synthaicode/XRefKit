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
- [Planning Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `value and constraint fit evaluation` is a business activity in CAB preparation.
- This capability is the reusable alignment-evaluation ability used by that activity.
