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
- integration regression verification basis reference

## Required Domain Knowledge

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)

## Constraints

- execute or evaluate only against the approved test design
- each verification result must identify which integration/regression test-design item and basis reference it verified
- do not redefine release approval
- record unresolved failures explicitly

## Assignment

- quality verification phase
- [Quality Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)
