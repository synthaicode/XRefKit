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
- `references/requirements-validation.md`
- `references/specification-reconciliation.md`
- `references/delta-detail-planning.md`
- `references/ipa-reconstruction-guide-mapping.md`
- `references/service-data-impact.md`
- `references/file-edit-integrity.md`
- `references/change-test-suite.md`
- `references/testability-and-case-generation.md`
- `references/reporting-and-closure.md`

The test procedure must declare investigation scope, existing-data investigation
method, white-box structure-to-test mapping, pre-change test suite,
change-impact selection, testability input completeness, AI-generated case
candidates, definition gaps, post-change comparison, and overview/detail
evidence. Tool preparation and the testability gate belong in planning/design;
test execution belongs in testing. Do not generate a case by guessing a missing
input, expected result, business rule, or evidence source.

## Phase-based use

Route the request to one phase and carry forward the same upstream reference,
evidence, unknowns, owners, and decisions:

- `requirements`: current/desired behavior, acceptance, scope, and decisions;
- `planning`: impact scope, dependencies, tools, data, fixtures, gates, and
  handoff;
- `design`: traced structural delta, contracts, and testability/case-definition
  check;
- `manufacturing`: approved implementation with file and concurrency integrity;
- `testing`: approved suite execution, evidence, pre/post comparison, and
  residual risk;
- `closure`: upstream trace, unknown classification, decisions, and handoff.

If the phase is not stated, infer it only from the requested deliverable and
make the selected phase explicit in the summary. Stop when the phase requires
an unresolved business, design, data, expected-result, or ownership decision.

When an existing Requirement is supplied, validate its source, version,
authority, owner, freshness, consistency with current evidence, and
testability before using it as a design or test basis. Do not silently rewrite
or approve it.

In `design`, reconcile the current specification, evidenced current behavior,
and validated new requirement. Record the delta class, protected invariants,
compatibility/downstream impact, test impact, owner, and human decision before
approving the design delta.

After reconciliation, refine the initial work policy from the approved delta
before manufacturing or test-case approval. Recalculate work units, data,
compatibility, rollback, evidence, test, gates, owners, and handoffs; do not
treat the Requirement-only plan as final.

Every phase starts with a summary containing conclusion, downstream-ordered
unknowns, blockers, completed items, next handoff, and evidence links. Before
closure, trace every upstream item, attach evidence and Knowledge/pattern
basis, give each unknown a resolver and owner, and stop when proceeding would
require guessing.
