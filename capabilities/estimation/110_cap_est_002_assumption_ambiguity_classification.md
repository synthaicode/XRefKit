<!-- xid: B362EA06B9C2 -->
<a id="xid-B362EA06B9C2"></a>

# Capability: CAP-EST-002 Assumption Ambiguity Classification

## Definition

- capability_id: `CAP-EST-002`
- capability_name: `assumption_ambiguity_classification`
- work_type: `execution`
- summary: classify unresolved assumptions and produce items that require confirmation

## Preconditions

- assumption list from `CAP-EST-001` exists

## Trigger

- assumption-confirmation phase starts

## Inputs

- unresolved assumption list

## Outputs

- ambiguity classification result
- confirmation-required item list
- candidate requirement statements

## Required Domain Knowledge

- business rules
- constraint definitions

## Constraints

- classify and propose only
- do not confirm assumptions by itself
- preserve evidence gaps explicitly

## Assignment

- assumption-confirmation phase
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


