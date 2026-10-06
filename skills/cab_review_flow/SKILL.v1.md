---
schema_version: 1
skill_id: cab_review_flow
xid: C7A4E9B2D610
aliases:
  - 33D0A3A01B47
  - AE3979CD83C0
summary: execute CAB evaluation gates for quality, operational readiness, and value alignment before human release confirmation
applies_when:
  - user needs CAB-style evaluation before release confirmation
exclusions:
  - Human final approval or release decision remains outside this Skill
  - Unsupported conclusions remain unresolved rather than being silently completed
inputs:
  - release plan materials, manufacturing outputs, requirement and design evidence, value and constraint definitions
outputs:
  - quality-gate result, operational readiness result, value-gate result, unresolved list
criteria:
  - id: semantic_sequence
    statement: The Skill's evaluation sequence and semantic criteria are applied in order without embedding routing or capability identifiers
    verification: Inspect each phase result and evidence link against the method sequence
  - id: decision_boundary
    statement: Human final-decision authority remains explicit and unsupported judgments remain unknown
    verification: Check closure, rules, and handoff for approval boundaries
  - id: output_closure
    statement: The declared result and unresolved items are returned with a handoff
    verification: Check the output and handoff before closure
knowledge_needs: []
control_refs: []
---
<!-- xid: C7A4E9B2D610 -->
<a id="xid-C7A4E9B2D610"></a>

# Skill: cab_review_flow

## Purpose

Execute CAB-facing evaluation in the order quality suitability, operational readiness, and value and constraint fit.

## Inputs

- release plan materials
- manufacturing outputs
- design and requirement evidence
- value, constraint, and priority definitions

## Outputs

- quality-gate result
- operational readiness result
- value-gate result
- unresolved list

## Startup

- Confirm CAB input materials exist.
- Confirm design, requirement, and value evidence exists.
- Record `unknown` if required evidence is missing.

## Planning

- Define the CAB evaluation scope.
- Map each business activity to its supporting capability:
  - release plan suitability review
  - operational readiness gate
  - value and constraint fit evaluation
- Prepare management rows for quality, operations, business, and unresolved risk items.

## Execution

- Evaluate release-plan suitability from the quality perspective.
- Evaluate operational readiness.
- Evaluate value and constraint fit.
- Return the three results with explicit evidence and unresolved items.

## Monitoring and Control

- Check that each CAB gate has a recorded result.
- Preserve explicit unresolved risks.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the three gate results to the human decision layer.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Evaluate only; do not decide final release approval.
- Every judgment must cite evidence.
- Preserve unresolved risks explicitly.
