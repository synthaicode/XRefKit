# Brownfield Execution Planning

Create the concrete work plan before executing a bounded brownfield change.
Preserve the upstream reference and use service catalog and
service-interaction/data-flow Knowledge before deciding ownership or impact.

The plan must define objective and boundaries, an XDDP change-requirement
specification, an XDDP traceability matrix, a change-design handoff,
investigation scope, service and data dependencies, ordered work items,
existing-data extraction and reproducibility, pre-change test-suite
preparation, white-box structure-to-test mapping, evidence, gates, owners,
stop conditions, and handoffs.

Use the XDDP chain `Why/What -> Where -> How`: map each change requirement or
specification to impacted assets, work items, tests, evidence, and handoffs.
Keep change intent separate from reconstructed current behavior, and update the
matrix before continuing when a parameter, return value, state, or shared
module change expands the impact.

Prepare tools, environments, fixtures, and test data in planning; execute them
in the assigned phase. Record unsupported mappings, missing data, dynamic
paths, or unclear acceptance rules as impact-bearing `unknown` items.

Every work item carries `id`, `upstream_ref`, `target`, `phase`, `basis`,
`dependencies`, `state`, `impact`, `xddp_row_id`, `evidence_target`, `owner`,
`next_action`, and `completion_criterion`. Start output with `Status`, `Result`, `Evidence`,
`Open Items`, and `Handoff`. Do not approve human-owned requirements,
design, release, or residual risk.
