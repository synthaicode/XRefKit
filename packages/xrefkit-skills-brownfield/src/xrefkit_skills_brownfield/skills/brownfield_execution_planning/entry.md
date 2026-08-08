# Brownfield Execution Planning

Create the concrete work plan before executing a bounded brownfield change.
Preserve the upstream reference and use service catalog and
service-interaction/data-flow Knowledge before deciding ownership or impact.

The plan must define objective and boundaries, investigation scope, service and
data dependencies, ordered work items, existing-data extraction and
reproducibility, pre-change test-suite preparation, white-box structure-to-test
mapping, evidence, gates, owners, stop conditions, and handoffs.

Prepare tools, environments, fixtures, and test data in planning; execute them
in the assigned phase. Record unsupported mappings, missing data, dynamic
paths, or unclear acceptance rules as impact-bearing `unknown` items.

Every work item carries `id`, `upstream_ref`, `target`, `phase`, `basis`,
`dependencies`, `state`, `impact`, `evidence_target`, `owner`, `next_action`,
and `completion_criterion`. Start output with `Status`, `Result`, `Evidence`,
`Open Items`, and `Handoff`. Do not approve human-owned requirements,
design, release, or residual risk.
