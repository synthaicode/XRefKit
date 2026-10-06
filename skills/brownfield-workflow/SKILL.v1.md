---
schema_version: 1
skill_id: brownfield_workflow
xid: E1A7C4D9B260
aliases: [A17C4E8B2D91, 9B3D7A1C4E20]
summary: carry a brownfield change through traced phase outputs while preserving evidence, unknowns, and human decisions
applies_when:
  - an existing codebase or system must be changed and current implementation is evidence rather than complete specification
exclusions:
  - do not create untraced work or approve human-owned requirements, design, release, or residual-risk decisions
inputs:
  - upstream work item, current-system evidence, target scope, constraints, risks, decisions, and optional source or Knowledge artifacts
outputs:
  - summary-first phase result, traced items, evidence and Knowledge references, pattern decisions, unknowns, gates, and handoff
criteria:
  - id: traceability
    statement: Every phase item remains tied to its upstream item and records target, result, state, basis, impact, next action, and owner.
    verification: Inspect the phase output for complete item fields and one upstream reference per item.
  - id: brownfield_integrity
    statement: Existing behavior is treated as evidence; edits preserve encoding, BOM, newlines, revision checks, and uncommitted work.
    verification: Check the integrity record, compare-and-swap revision result, and round-trip bytes before accepting an edit.
  - id: unknown_and_authority
    statement: Missing evidence stays unknown with impact and resolver, and human-owned decisions remain handoffs.
    verification: Inspect unresolved items, owners, decision basis, and handoff artifacts for every material gap.
  - id: coverage_and_tests
    statement: Scope, deterministic inventories, testability, and coverage limits are explicit before claiming completion.
    verification: Confirm each in-scope bucket is done, not_applicable, or unknown with evidence and next action.
knowledge_needs:
  - id: service_catalog
    query: service catalog ownership and responsibility boundary
    required_when: Required before requirements become design when service ownership is in scope.
    seed_xids: [7A2F4C8D2201]
  - id: service_interaction_data_flow
    query: service interaction and data-flow viewpoints
    required_when: Required before implementation-facing design when cross-service or persistence flow is in scope.
    seed_xids: [7A2F4C8D2301]
  - id: knowledge_ontology_management
    query: domain knowledge ontology and reuse rules
    required_when: Required when importing, refreshing, registering, or publishing existing Knowledge artifacts.
    seed_xids: [5803607419B9]
control_refs: []
---
<!-- xid: E1A7C4D9B260 -->
<a id="xid-E1A7C4D9B260"></a>

# Brownfield Workflow

Carry one brownfield change through requirements, planning, design,
manufacturing, testing, and closure. Preserve the upstream item as the
traceability anchor; do not create an independent task catalogue. Search the
applicable Knowledge fragments before each phase judgment and classify the
relationship to existing patterns as `follows`, `adapts`, `introduces`, or
`unknown`.

## Phase method

1. Confirm the upstream item, target scope, current behavior, desired behavior,
   acceptance, decision owners, evidence, and phase. If any material input is
   absent, record an impact-bearing `unknown`.
2. In requirements, separate purpose, evidenced current behavior, desired
   behavior, acceptance, normal/error/boundary conditions, scope, and decisions.
3. In planning, define impacted targets, work units, dependencies, execution
   order, compatibility/data/release/rollback policy, tools, fixtures, gates,
   and handoffs. Prepare test tools and testability inputs here.
4. In design, reconcile current specification, evidenced current behavior, and
   new requirement. Define only the traced structural delta, protected
   invariants, contracts, state, transaction/idempotency/concurrency,
   compatibility, observability, and design-to-test handoff.
5. In manufacturing, implement only approved design items. Before editing an
   existing file, record encoding, BOM, newline convention, strict decode,
   original bytes or hash, approved spans, and a compare-and-swap revision
   token. Abort on concurrent changes, unclear specification alignment, or
   protected overlapping work. Use atomic replacement only after alignment is
   confirmed, then verify byte round-trip and semantic alignment.
6. In testing, execute the approved change-focused suite, compare pre/post
   behavior, and record expected result, observation source, evidence, and
   residual risk. Generate only traceable test candidates; do not invent
   inputs, expectations, business rules, or evidence sources.
7. In closure, trace every in-scope upstream item to a result, attach evidence
   and Knowledge/pattern basis, classify unknowns, record the next-phase input,
   and prepare the handoff.

## Required item shape

Each phase item records `id`, `upstream_ref`, `target`, `phase_result`, `state`
(`done`, `unknown`, or `out_of_scope`), `basis`, `knowledge_refs`,
`pattern_decision`, `pattern_basis`, `impact`, `next_action`, and `owner`.
Keep current behavior, desired behavior, inference, and human decisions
separate. Import existing service, flow, DB, or test artifacts before new
discovery; classify imports as `create`, `extend`, `refresh`, `split`,
`reject_duplicate`, or `proposal_only` and preserve freshness and conflicts.

## Coverage and stop conditions

Adjust DFD detail to the declared scope and distinguish primary, supporting,
and derived Entities. When in scope, map named change points, state
transitions, approvals, audit evidence, logical deletion, and downstream
propagation. Use deterministic inventories for coverage-critical questions; if
one cannot run, record an `unknown` and do not claim complete coverage.

Stop and hand off when requirement authority, meaning, scope, acceptance,
impact, data, owner, compatibility, or delta-specific execution policy is
missing or conflicting. Do not select history as authority merely because it
is newer. Suspected defects and security findings go to their respective
review Skills. Human owners decide requirements, design, release, and residual
risk; this Skill prepares evidence and questions for those decisions.
