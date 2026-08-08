# Brownfield Pattern Learning

Learn existing implementation and operational patterns before choosing a
design approach. The purpose is to avoid unnecessary complexity and preserve
the service's demonstrated operational level.

When external modernization knowledge is needed, use the packaged
`references/external-modernization-basis.md` as thematic background. Do not
copy an external pattern without comparing it with local evidence, data
ownership, operation, rollback, and decision ownership.

Inspect coherent peer scopes, record representative paths, rule signatures,
counts, exceptions, freshness, and confidence. Do not treat one example as a
repository rule. Compare the candidate with existing structure, contracts,
data flow, state, errors, tests, deployment, monitoring, recovery, support,
and operator actions.

Return a pattern inventory, data-lifecycle pattern inventory,
lifecycle/propagation map, operational baseline, complexity/operational delta,
`follows`/`adapts`/`introduces`/`unknown` decision basis, deviation options,
risks, owner, and handoff. For in-scope data, cover creation, ownership,
state/status transitions, logical deletion, retention, archive/purge, audit,
replay/correction, downstream propagation, backup/restore, and recovery. An
`adapts` or `introduces` result must explain why
the existing pattern is insufficient and who can operate the added complexity.
Unclear, stale, weak, or conflicting evidence is an impact-bearing `unknown`.

For every enhancement, load `references/pattern-decision-report.md` and produce
a concise overview plus detailed evidence. Compare selected and rejected
options, explain complexity and operational impact, describe data-lifecycle
impact and protected invariants, and link the decision to XDDP, work items,
tests, and evidence.

Start output with `Status`, `Result`, `Evidence`, `Open Items`, and `Handoff`.
Do not approve business requirements, design, release, or residual risk.
