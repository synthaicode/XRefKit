<!-- xid: 83140C9538B4 -->
<a id="xid-83140C9538B4"></a>

# Capability: CAP-OPS-005 Release Verification

## Definition

- capability_id: `CAP-OPS-005`
- capability_name: `release_verification`
- work_type: `execution`
- summary: verify release readiness evidence against release criteria before CAB

## Preconditions

- release plan materials exist
- operational readiness inputs exist

## Trigger

- release verification starts before CAB

## Inputs

- test-environment release plan
- production-environment release plan
- release basis reference
- environment release basis reference
- release confirmation procedure draft
- operational readiness result
- integration regression verification result

## Outputs

- release verification result
- unresolved list
- release verification basis reference

## Required Domain Knowledge

- acceptance criteria
- rollback criteria
- release criteria

## Constraints

- verify only
- each verification result must identify which release plan item, release confirmation procedure item, and release basis reference it verified
- release verification must cover both placement confirmation evidence and behavior confirmation evidence
- do not decide final release approval
- every judgment needs evidence

## Assignment

- release planning phase
- [Operations Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

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
