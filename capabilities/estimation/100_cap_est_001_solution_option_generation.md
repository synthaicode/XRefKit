<!-- xid: BDB6B54A3571 -->
<a id="xid-BDB6B54A3571"></a>

# Capability: CAP-EST-001 Solution Option Generation

## Definition

- capability_id: `CAP-EST-001`
- capability_name: `solution_option_generation`
- work_type: `execution`
- summary: generate solution options with effort, risk, and assumption lists

## Preconditions

- change target list from investigation exists

## Trigger

- estimation phase starts for solution planning

## Inputs

- request
- change target list
- relevant domain knowledge

## Outputs

- solution options
- effort estimate per option
- risk list per option
- assumption list

## Required Domain Knowledge

- coding rules
- architecture knowledge
- business rules

## Constraints

- propose options only
- do not decide the final direction
- preserve uncertain assumptions explicitly

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


