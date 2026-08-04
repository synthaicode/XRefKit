# Brownfield Workflow

Carry one brownfield change through requirements, planning, design,
manufacturing, and testing. Preserve the upstream item as the traceability
anchor; do not create an independent task catalogue.

Use a Knowledge- and pattern-first loop: search applicable repository Knowledge
before each phase judgment, compare the change with the target's existing
patterns, and record `follows`, `adapts`, `introduces`, or `unknown`. Knowledge
and existing implementation are evidence, not automatic business truth.

Before requirements become design, resolve the service catalog record for the
responsible existing service and the service-interaction/data-flow records for
communication and database propagation. Missing or stale ownership, contract,
or flow evidence is `unknown`; do not infer it from a namespace, folder, or one
call site.

For every phase, return a summary first containing the conclusion, unresolved
items ordered by downstream impact, blockers, completed items, next handoff,
and references to detailed evidence.

Maintain each item with:

- stable `id`;
- `upstream_ref`;
- target;
- current phase result;
- state: `done`, `unknown`, or `out_of_scope`;
- evidence or decision basis;
- `knowledge_refs` (XID references used for the item);
- `pattern_decision` and `pattern_basis`;
- `knowledge_import_results` when an existing catalog or flow artifact was supplied;
- downstream impact;
- next action and owner.

Do not use `unknown` as a bare label. State what is unknown, why it is unknown,
what it affects, and who or what can resolve it. Do not infer missing behavior
from the existing implementation; existing code is evidence of current
behavior, not automatically the business requirement.

Planning must produce a phase-by-phase Knowledge reuse plan covering design,
manufacturing, and testing. Verify each Knowledge fragment's applicability and
freshness/recheck condition. If an applicable existing pattern cannot be
followed, record the deviation, rationale, evidence, and decision owner before
handing the item onward.

The plan must identify service ownership, affected flows, communication
contracts, database read/write ownership, and downstream propagation for each
in-scope item.

When these records already exist in documents, exports, diagrams, OpenAPI/
AsyncAPI, DDL/ERD, CMDB extracts, or analysis reports, import them before new
discovery. Preserve the original source, search canonical XIDs, classify each
concept as `create`, `extend`, `refresh`, `split`, `reject_duplicate`, or
`proposal_only`, normalize into the two Knowledge schemas, attach evidence and
freshness, and record conflicts. Apply canonical changes only when authorized;
otherwise hand a `work/` proposal to `knowledge_ontology_management`.

If the supplied input is already an XID-bearing file under `knowledge/`, use
the canonical path fast path: verify the path boundary, resolve the XID with
`xref show`, confirm applicability and freshness, record
`mode: canonical_path_reuse`, and use that XID directly. Do not duplicate or
re-register the fragment. Semantic changes go to
`knowledge_ontology_management`; an invalid or XID-less path remains unknown.

## Requirements

Re-organize the request and current-state evidence into purpose, current
behavior, desired behavior, acceptance conditions, scope, normal/error/boundary
conditions, non-functional requirements, assumptions, and unresolved decisions.
Do not approve human-owned business requirements.

## Planning

Re-organize approved requirements into impacted targets, work units,
dependencies, execution order, compatibility/data/release/rollback policies,
risks, stop conditions, phase gates, and verification evidence. Produce the
work policy here. Include test tools, versions, fixtures, environment,
dependencies, test data, cleanup, result storage, and local/CI execution. Test
tool preparation belongs to planning; test execution belongs to testing.

## Design

Re-organize each requirements and planning item into only the required design
areas: current-to-target delta, component responsibility, API/message/DB/data
contracts, processing order and state, transaction/idempotency/concurrency,
error/retry/timeout/rollback behavior, compatibility/migration, observability,
and design-to-test handoff. Output decisions and explicit unknowns. Create
detailed artifacts only for traced items; do not make testing infer scope from
broad prose.

Use the selected design Knowledge and pattern-conformity result to make the
delta explicit. An `adapts` or `introduces` decision requires an explicit basis
and owner; it is not implementation freedom.

## Manufacturing

Re-organize approved design items into implementation units for code, DB,
migrations, configuration, integrations, tests, and build/static checks. If
implementation exposes an unresolved requirement or design decision, stop that
item and return it as `unknown` or `blocked`; do not decide silently in code.

Implement only against the approved Knowledge and pattern basis. If hard
evidence refutes that basis, record the assumption gap and correction handoff.

## Testing

Re-organize the design-to-test handoff and planned test policy into executable
tests. Cover applicable baseline, unit, integration, regression, boundary,
negative, migration, compatibility, retry, idempotency, concurrency, and
rollback cases. Record tool versions, context, test data, logs, raw results,
failure classification, retest, and residual risk.

## Closure

Trace every in-scope upstream item to a result. Classify every item, attach
evidence to completed items, give every unknown a reason/impact/action/owner,
and record the next phase's input package and handoff conditions. Stop when
proceeding would require guessing business behavior, structure,
compatibility, data handling, or test acceptance.
