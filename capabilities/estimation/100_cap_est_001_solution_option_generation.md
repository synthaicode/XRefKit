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
