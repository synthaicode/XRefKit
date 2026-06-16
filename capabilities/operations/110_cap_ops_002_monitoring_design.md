<!-- xid: 316B0FB4493C -->
<a id="xid-316B0FB4493C"></a>

# Capability: CAP-OPS-002 Operational Signal Specification

## Definition

- capability_id: `CAP-OPS-002`
- capability_name: `operational_signal_specification`
- work_type: `execution`
- summary: define monitoring items, thresholds, and alert conditions from performance evidence

## Preconditions

- performance data or performance requirements exist

## Trigger

- release-planning phase runs monitoring preparation

## Inputs

- performance data
- performance requirements
- supplier capacity conditions when applicable

## Outputs

- monitoring items
- normal ranges
- threshold definitions
- alert conditions

## Required Domain Knowledge

- monitoring definitions
- threshold criteria

## Constraints

- define settings only
- do not apply vendor-tool configuration directly
- preserve evidence gaps explicitly

## Assignment

- release-planning phase
- [Operations Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `monitoring design` is a business activity in release-planning work.
- This capability is the reusable operational-signal specification ability used by that activity.
