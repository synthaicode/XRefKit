---
schema_version: 1
skill_id: estimation_flow
xid: E2B7D9F4A130
aliases:
  - FB65EC653F0F
  - EA208AA244DF
summary: prepare estimation options, supplier checks, and assumption clarification before requirements
applies_when:
  - user needs estimate options, supplier checks, or assumption clarification before requirements
exclusions:
  - Human final approval or release decision remains outside this Skill
  - Unsupported conclusions remain unresolved rather than being silently completed
inputs:
  - request, change target list, supplier definitions, optional budget definition
outputs:
  - supplier check results, cost patterns, solution options, assumption list, ambiguity classification
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
<!-- xid: E2B7D9F4A130 -->
<a id="xid-E2B7D9F4A130"></a>

# Skill: estimation_flow

## Purpose

Execute supplier checking, cost estimation, solution option generation, and assumption ambiguity classification in that order.

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
  - supplier four-condition check
  - cost estimation
  - solution option generation
  - assumption ambiguity classification
- Define the step order explicitly.
- Prepare management rows for supplier checks, cost patterns, options, and assumptions.

## Execution

- Perform the supplier four-condition check.
- Perform cost estimation.
- Perform solution option generation.
- Consult on option differences, direction tradeoffs, and assumption impacts when comparison cannot be closed inside the current boundary.
- Perform assumption ambiguity classification.

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
