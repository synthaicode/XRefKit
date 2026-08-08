---
name: brownfield-execution-planning
description: Create a traceable execution work plan for a brownfield change, including investigation scope, service and data dependencies, existing-data handling, pre-change test-suite preparation, evidence, gates, owners, and handoffs. Use before executing a bounded change in an existing system.
---
<!-- xid: 9E4B7C2A6102 -->
<a id="xid-9E4B7C2A6102"></a>

# Brownfield Execution Planning

Prepare the work policy before a brownfield change is investigated, modified,
or tested. This Skill complements `brownfield_workflow`: the workflow governs
the full lifecycle; this Skill produces the concrete execution plan for the
current change.

## Inputs

- approved or bounded change request and upstream reference;
- target service, current-system evidence, and known implementation/test data;
- service catalog and service-interaction/data-flow Knowledge;
- constraints, risks, decision owners, and required handoffs.

If a material input is missing, record an impact-bearing `unknown`; do not infer
it from a folder, namespace, one call site, or existing behavior.

## Planning outputs

Produce a work plan containing:

- objective, acceptance boundary, and out-of-scope boundary;
- XDDP change-requirement specification separating change reason, before/after
  behavior, and concrete change specifications;
- XDDP traceability matrix mapping each change requirement/specification to
  impacted services, modules, files, data, tests, evidence, and handoffs;
- change-design handoff describing the intended change method before editing;
- investigation scope with included, excluded, detail level, and unknowns;
- service, component, DB, integration, downstream, and data dependency map;
- work items ordered by dependency and downstream impact;
- existing-data extraction, snapshot/fixture, masking, freshness, and
  reproducibility policy;
- pre-change test-suite creation and baseline-result capture plan;
- white-box structure-to-test mapping and change-impact analysis plan;
- evidence paths, stable IDs, raw-result retention, and comparison method;
- preparation, execution, check, closure, and handoff gates;
- owner, next action, stop condition, and resolver for every unknown.

## XDDP traceability

Use the XDDP three-artifact chain before implementation:

```text
Why / What: change-requirement specification
        ↓
Where: traceability matrix
        ↓
How: change-design handoff
        ↓
execution plan → tests → evidence → decision
```

The matrix must use change differences as rows and impacted assets as columns.
At minimum, map each row to `service_id`, `flow_id`, `entity_id` or target,
`work_item_id`, `test_id`, `evidence_id`, and `handoff_id` where applicable.
When a parameter, return value, state, or shared module change expands the
impact, update the matrix before continuing. Do not begin implementation while
an in-scope change row has no target, method, test/evidence path, or owner.

Keep the XDDP artifacts focused on the difference; do not reproduce the entire
base specification. When source or documents are weak, record a bounded
spec-out investigation as evidence and keep reconstructed behavior separate
from approved change intent.

## Planning rules

1. Preserve the upstream item as the traceability anchor.
2. Search and cite applicable Knowledge before deciding scope or ownership.
3. Separate specification, current behavior, inference, and human decision.
4. Record `follows`, `adapts`, `introduces`, or `unknown` for relevant patterns.
5. Prepare tools, environments, fixtures, and data in planning; execute them in
   their assigned phase.
6. Create or refresh the test suite before the implementation change.
7. Use white-box structure to identify changed and protected paths, not to
   replace business approval.
8. Do not call unverified data, dynamic paths, or missing constraints harmless.
9. Stop planning closure when a material target, owner, data condition, or
   acceptance rule cannot be evidenced.

## Work item shape

Each work item must contain `id`, `upstream_ref`, `target`, `phase`, `basis`,
`dependencies`, `state`, `impact`, `xddp_row_id`, `evidence_target`, `owner`,
`next_action`, and `completion_criterion`. Use `done`, `unknown`, or
`out_of_scope`; unknowns must state reason, impact, resolver, and owner.

## Required summary

Start the output with `Status`, `Result`, `Evidence`, `Open Items`, and
`Handoff`. The result must state whether the work plan is ready, partial,
blocked, or escalated. Do not approve business requirements, design, release,
or residual risk on behalf of the responsible human.
