# Brownfield Workflow

Carry one brownfield change through requirements, planning, design,
manufacturing, and testing. Preserve the upstream item as the traceability
anchor; do not create an independent task catalogue.

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
- downstream impact;
- next action and owner.

Do not use `unknown` as a bare label. State what is unknown, why it is unknown,
what it affects, and who or what can resolve it. Do not infer missing behavior
from the existing implementation; existing code is evidence of current
behavior, not automatically the business requirement.

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

## Manufacturing

Re-organize approved design items into implementation units for code, DB,
migrations, configuration, integrations, tests, and build/static checks. If
implementation exposes an unresolved requirement or design decision, stop that
item and return it as `unknown` or `blocked`; do not decide silently in code.

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
