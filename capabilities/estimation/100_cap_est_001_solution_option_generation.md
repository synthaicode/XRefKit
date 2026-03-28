<!-- xid: BDB6B54A3571 -->
<a id="xid-BDB6B54A3571"></a>

# Capability: CAP-EST-001 Solution Option Structuring

## Definition

- capability_id: `CAP-EST-001`
- capability_name: `solution_option_structuring`
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

## Solution Option Generation Rule

A solution option must be differentiated by at least one explicit branching axis while keeping the same request and the same change target list.

### Allowed Branching Axes

- realization approach: existing-function extension / new implementation / external service usage
- automation boundary: manual absorption / semi-automation / full automation
- change-impact strategy: preserve existing structure / partial modification / redesign
- assumption dependency: works without added assumptions / requires stakeholder confirmation / requires external condition fulfillment

### Rules

- each option must explicitly state which branching axis or axes make it distinct
- branching axes must describe differences in realization, not differences in request scope or change target scope
- options without a material axis difference must be merged into a single option
- every option must include an effort estimate, a risk list, and an assumption list
- option generation proposes alternatives only and does not decide the final direction

## Assignment

- estimation phase
- [Planning Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `solution option generation` is a business activity in estimation work.
- This capability is the reusable option-structuring ability used by that activity.
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


