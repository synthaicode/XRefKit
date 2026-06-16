<!-- xid: 83140C9538B3 -->
<a id="xid-83140C9538B3"></a>

# Capability: CAP-OPS-004 Operational Readiness Evaluation

## Definition

- capability_id: `CAP-OPS-004`
- capability_name: `operational_readiness_evaluation`
- work_type: `judgment`
- summary: evaluate whether release planning, monitoring, and response procedures are ready for CAB

## Preconditions

- outputs from `CAP-OPS-001`, `CAP-OPS-002`, and `CAP-OPS-003` exist

## Trigger

- CAB preparation starts

## Inputs

- release plan draft
- monitoring specification
- event-response procedure draft

## Outputs

- operational readiness result
- findings with evidence
- unresolved list

## Required Domain Knowledge

- acceptance criteria
- rollback criteria
- monitoring criteria

## Constraints

- evaluate only
- do not decide final release approval
- every judgment needs evidence

## Assignment

- CAB preparation
- [Operations Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `operational readiness gate` is a business activity in release-planning and CAB work.
- This capability is the reusable operational-readiness evaluation ability used by that activity.
