<!-- xid: 9F14372D994A -->
<a id="xid-9F14372D994A"></a>

# Capability: CAP-MGT-002 Uncertainty and Risk Logging

## Definition

- capability_id: `CAP-MGT-002`
- capability_name: `uncertainty_and_risk_logging`
- work_type: `management`
- summary: record uncertainty, unresolved items, and execution metrics during work

## Preconditions

- active work execution exists

## Trigger

- `unknown`, `out_of_scope`, or unresolved findings occur
- a work step completes

## Inputs

- work result
- uncertainty or unresolved details
- metrics definition

## Outputs

- uncertainty list
- out-of-scope list
- implementation assumption gap log
- metrics log

## Required Domain Knowledge

- `../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201`

## Constraints

- record only
- do not resolve or accept risk by itself
- preserve evidence gaps explicitly
- preserve implementation assumption gap classification explicitly

## Assignment

- [All Groups](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- execution management role
