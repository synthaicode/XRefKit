<!-- xid: 754A17D69C7C -->
<a id="xid-754A17D69C7C"></a>

# Capability: CAP-SUP-002 Cost Estimation

## Definition

- capability_id: `CAP-SUP-002`
- capability_name: `cost_estimation`
- work_type: `execution`
- summary: estimate service cost patterns and identify budget-overrun risk

## Preconditions

- output from `CAP-SUP-001` exists
- budget definition exists

## Trigger

- supplier condition check completes

## Inputs

- request size assumptions
- supplier cost conditions
- budget definition

## Outputs

- cost estimate patterns
- budget-overrun risk list
- uncertainty list

## Required Domain Knowledge

- budget definitions
- supplier cost conditions

## Constraints

- estimate and compare patterns only
- do not decide final budget ceiling
- preserve assumption gaps explicitly

## Assignment

- estimation phase
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


