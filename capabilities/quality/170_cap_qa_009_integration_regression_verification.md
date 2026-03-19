<!-- xid: 5A1C2F0E5509 -->
<a id="xid-5A1C2F0E5509"></a>

# Capability: CAP-QA-009 Integration and Regression Verification

## Definition

- capability_id: `CAP-QA-009`
- capability_name: `integration_regression_verification`
- work_type: `execution`
- summary: execute or evaluate integration and regression verification against approved test design

## Preconditions

- integration regression test design exists
- implementation outputs exist

## Trigger

- post-manufacturing verification starts

## Inputs

- implemented code or deployed verification target
- integration regression test design
- integration regression test basis policy reference

## Outputs

- integration regression verification result
- unresolved list
- uncertainty list

## Required Domain Knowledge

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)

## Constraints

- execute or evaluate only against the approved test design
- do not redefine release approval
- record unresolved failures explicitly

## Assignment

- quality verification phase
- [Quality Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

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
