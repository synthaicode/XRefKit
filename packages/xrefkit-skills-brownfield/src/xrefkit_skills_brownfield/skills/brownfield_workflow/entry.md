# Brownfield Workflow

Carry one brownfield change through requirements, planning, design,
manufacturing, and testing. Preserve the upstream item as the traceability
anchor and do not create untraced work.

Use Knowledge- and pattern-first execution. Search applicable Knowledge before
each phase judgment, compare the change with the existing pattern, and record
`follows`, `adapts`, `introduces`, or `unknown`. Existing implementation and
Knowledge are evidence, not automatic business truth.

Before requirements become design, resolve service ownership and the
service-interaction/data-flow records for communication and database
propagation. Missing or stale evidence is an impact-bearing `unknown`.

Maintain each item with stable `id`, `upstream_ref`, `target`, phase result,
state, evidence/decision basis, `knowledge_refs`, `pattern_decision`,
`pattern_basis`, impact, next action, and owner. Do not use `unknown` as a bare
label.

Load the detailed procedure only when needed:

- `references/phase-workflow.md`
- `references/service-data-impact.md`
- `references/file-edit-integrity.md`
- `references/change-test-suite.md`
- `references/reporting-and-closure.md`

The test procedure must declare investigation scope, existing-data investigation
method, white-box structure-to-test mapping, pre-change test suite,
change-impact selection, post-change comparison, and overview/detail evidence.
Tool preparation belongs in planning; test execution belongs in testing.

Every phase starts with a summary containing conclusion, downstream-ordered
unknowns, blockers, completed items, next handoff, and evidence links. Before
closure, trace every upstream item, attach evidence and Knowledge/pattern
basis, give each unknown a resolver and owner, and stop when proceeding would
require guessing.
