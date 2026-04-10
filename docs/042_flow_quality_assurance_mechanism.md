<!-- xid: 8B31F02A4011 -->
<a id="xid-8B31F02A4011"></a>

# Flow Quality Assurance Mechanism

This page defines how output quality is assured inside a single workflow before cross-group handoff.

## Purpose

Prevent a workflow from producing outputs that cannot be explained, traced, or safely handed off.

This page covers quality assurance inside one workflow only.
It does not define role ownership or cross-workflow structural correction.
For those boundaries, see [Group definitions](040_group_definitions.md#xid-8B31F02A4009), [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012), and [Group, quality, and feedback boundaries](021_group_quality_and_feedback_boundaries.md#xid-8E5D31A4C672).

## Quality Assurance Layers

Within one workflow, quality assurance is built from the following layers:

1. task lifecycle control
2. group-internal self-check
3. management-table control
4. execution metrics
5. closure check
6. optional external review after handoff

## Layer 1: Task Lifecycle Control

Each workflow step follows:

1. Startup
2. Planning
3. Execution
4. Monitoring and Control
5. Closure

This ensures that output quality is checked while work is still inside the same flow, not only after handoff.

## Layer 2: Group-Internal Self-Check

The owner group must perform self-check inside its own responsibility boundary.

The self-check verifies:

- the output stayed inside scope
- required evidence was recorded
- assumptions and gaps were recorded
- unresolved or out-of-scope items were preserved explicitly

Reference:

- [Group definitions](040_group_definitions.md#xid-8B31F02A4009)

## Layer 3: Management-Table Control

Every `(work, target)` pair must be visible in the management table and end as:

- `done`
- `unknown`
- `out_of_scope`

`missing` is treated as a leak and blocks closure.

Reference:

- [Management table schema](../knowledge/organization/110_management_table_schema.md#xid-7A2F4C8D1101)

## Layer 4: Execution Metrics

Each output or management row must preserve enough metrics to interpret quality:

- `judgment_evidence`
- `confidence`
- `context_usage`

Low-confidence or estimation-only results must not be handed off as normal completion.

Reference:

- [Metrics definition](../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Layer 5: Closure Check

Before handoff, the workflow must confirm:

- no `missing` rows remain
- all unresolved items are explicit
- all `out_of_scope` reasons are preserved
- return or escalation paths are defined

Reference:

- [Closure workflow](034_closure_workflow.md#xid-8B31F02A4003)

## Traceability Requirement

A workflow output is not considered quality-assured unless it is traceable.

## Minimum Traceability Elements

Each output should be traceable to:

1. source input
2. executed work item or capability
3. responsible group
4. evidence used for the result
5. self-check result
6. remaining unresolved or out-of-scope items

## Traceability Mapping

| Traceability element | Typical repository location |
|------|------|
| source input | workflow inputs, referenced artifacts, source paths |
| executed work item or capability | `docs/` workflow step and `capabilities/` reference |
| responsible group | workflow `Group Interaction` and [Group definitions](040_group_definitions.md#xid-8B31F02A4009) |
| evidence used | management table `evidence`, metrics `judgment_evidence`, work log |
| self-check result | group-specific self-check output or review finding |
| unresolved / out_of_scope | uncertainty list, out-of-scope list, closure record |

## Output Rule

Before cross-group handoff, each workflow output should be explainable in the following form:

- what was produced
- from which inputs
- by which group
- under which capability or workflow step
- with which evidence
- with which self-check result
- with which remaining gaps

## Example

For manufacturing output:

- output:
  - implemented code and unit test result
- trace back to:
  - approved design
  - manufacturing workflow
  - `CAP-MFG-001` and `CAP-MFG-002`
  - Manufacturing Group
  - manufacturing self-check result
  - implementation assumption-gap record when present

## Related

- [Group, quality, and feedback boundaries](021_group_quality_and_feedback_boundaries.md#xid-8E5D31A4C672)
- [Flow-to-group matrix](041_flow_to_group_matrix.md#xid-8B31F02A4010)
- [Group definitions](040_group_definitions.md#xid-8B31F02A4009)
- [Closure workflow](034_closure_workflow.md#xid-8B31F02A4003)
- [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012)
