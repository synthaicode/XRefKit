<!-- xid: BC408337F2A2 -->
<a id="xid-BC408337F2A2"></a>

# Capability: CAP-REQ-001 Requirement Draft Creation

## Definition

- capability_id: `CAP-REQ-001`
- capability_name: `requirement_draft_creation`
- work_type: `execution`
- summary: draft a requirement document from confirmed assumptions and investigation outputs

## Preconditions

- confirmed assumptions exist
- change-test viewpoint table exists

## Trigger

- requirements phase starts after assumption confirmation

## Inputs

- confirmed assumptions
- change target list
- change-test viewpoint table
- performance needs when available

## Outputs

- requirement draft

## Required Domain Knowledge

- business rules
- SLA definitions
- supplier definitions

## Constraints

- draft only
- do not approve requirements
- preserve unresolved points explicitly

## Assignment

- requirements phase
- [Planning Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)
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


