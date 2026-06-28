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
- [Planning Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)
- [Design Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)
- [Quality Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `change target summary` is a business activity in the investigation workflow.
- This capability is the reusable structuring ability used by that activity.
