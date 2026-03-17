<!-- xid: 6AB17163C9BF -->
<a id="xid-6AB17163C9BF"></a>

# Capability: CAP-INV-003 Structured Investigation Summary

## Definition

- capability_id: `CAP-INV-003`
- capability_name: `structured_investigation_summary`
- work_type: `execution`
- summary: structure investigation outputs into reusable change-target, test-viewpoint, and unresolved-item summaries

## Preconditions

- outputs from `CAP-INV-002` exist

## Trigger

- investigation workflow step 3 starts

## Inputs

- change viewpoints
- test viewpoints
- uncertainty list from prior investigation steps

## Outputs

- change target list
- change-test viewpoint table
- uncertainty list consolidated for handoff

## Required Domain Knowledge

- change impact analysis criteria
- test design criteria

## Constraints

- structure and summarize only
- do not prioritize or decide policy
- preserve unresolved items explicitly

## Assignment

- investigation phase step 3
- [Planning Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- [Design Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- [Quality Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `change target summary` is a business activity in the investigation workflow.
- This capability is the reusable structuring ability used by that activity.

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


