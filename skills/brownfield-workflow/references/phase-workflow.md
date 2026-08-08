<!-- xid: B4F1C8D2A601 -->
<a id="xid-B4F1C8D2A601"></a>

# Brownfield phase workflow

Use the phase sequence `requirements -> planning -> design -> manufacturing ->
testing`. Preserve upstream references and carry forward decisions, unknowns,
evidence, owners, and handoff conditions.

## Requirements

Record purpose, evidenced current behavior, desired behavior, acceptance
conditions, scope, normal/error/boundary conditions, assumptions, and
unresolved decisions. Current implementation is not automatically the business
requirement.

## Planning

Produce the work policy: impacted targets, dependencies, order, tools,
versions, fixtures, environment, test data, cleanup, result storage,
compatibility, migration, release, rollback, risks, stop conditions, gates,
and handoffs. Tool preparation belongs here; execution belongs to testing.

## Design

Describe only the traced delta and required responsibilities, contracts,
processing/state, transaction/idempotency/concurrency, error/retry/timeout,
compatibility/migration, observability, and design-to-test handoff.

## Manufacturing

Implement only approved design items. Return newly exposed requirement/design/
data decisions as `unknown` or `blocked`; do not decide silently in code.

## Testing

Use the pre-change suite and approved design-to-test handoff. Apply the detailed
rules in `change-test-suite.md` and record raw results, classifications,
retests, and residual risk.

## Gates and handoff

Do not advance a phase while a material unknown lacks an impact, resolver,
owner, or decision. A handoff must state completed items, unresolved items,
evidence, next owner, next action, and conditions for acceptance.
