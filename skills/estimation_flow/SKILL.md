<!-- xid: FB65EC653F0F -->
<a id="xid-FB65EC653F0F"></a>

# Skill: estimation_flow

## Purpose

Execute the sequence `CAP-SUP-001 -> CAP-SUP-002 -> CAP-EST-001 -> CAP-EST-002` and prepare inputs for requirements work.

## Required Capability Definitions (XID)

- [CAP-SUP-001 External Service Condition Comparison](../../capabilities/supply/100_cap_sup_001_supplier_four_condition_check.md#xid-2DC9A90A6508)
- [CAP-SUP-002 Cost Pattern Projection](../../capabilities/supply/110_cap_sup_002_cost_estimation.md#xid-754A17D69C7C)
- [CAP-EST-001 Solution Option Structuring](../../capabilities/estimation/100_cap_est_001_solution_option_generation.md#xid-BDB6B54A3571)
- [CAP-EST-002 Assumption Ambiguity Classification](../../capabilities/estimation/110_cap_est_002_assumption_ambiguity_classification.md#xid-B362EA06B9C2)

## Inputs

- request
- change target list
- supplier definitions
- optional budget definition

## Outputs

- four-condition comparison result
- issue list
- cost estimate patterns
- solution options with effort and risk
- assumption list
- ambiguity classification result
- confirmation-required item list

## Startup

- Confirm the request and change target list exist.
- Confirm supplier definitions are available.
- Confirm budget definitions exist when cost estimation is required.
- Record `unknown` for missing evidence before proceeding.

## Planning

- Define the estimation scope and target assumptions.
- Map each business activity to its supporting capability:
  - supplier four-condition check -> `CAP-SUP-001`
  - cost estimation -> `CAP-SUP-002`
  - solution option generation -> `CAP-EST-001`
  - assumption ambiguity classification -> `CAP-EST-002`
- Define the step order: `CAP-SUP-001 -> CAP-SUP-002 -> CAP-EST-001 -> CAP-EST-002`.
- Prepare management rows for supplier checks, cost patterns, options, and assumptions.

## Execution

- Perform supplier four-condition check by executing `CAP-SUP-001`.
- Perform cost estimation by executing `CAP-SUP-002`.
- Perform solution option generation by executing `CAP-EST-001`.
- Perform assumption ambiguity classification by executing `CAP-EST-002`.

## Monitoring and Control

- Check that each required supplier and assumption item has a recorded result.
- Downgrade weakly supported assumptions to `unknown`.
- Preserve explicit assumption gaps for confirmation.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off assumptions that need confirmation.
- Escalate out-of-scope supplier or budget items when reassignment is required.

## Rules

- Do not approve supplier adoption.
- Do not approve final budget or delivery direction.
- Every unresolved assumption must remain explicit.
