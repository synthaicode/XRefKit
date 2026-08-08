---
name: brownfield-pattern-learning
description: Learn existing implementation and operational patterns before a brownfield change, then prepare a complexity- and operability-aware basis for following, adapting, or introducing a pattern. Use when a proposed design may depart from local conventions or increase operational burden.
---
<!-- xid: 9E4B7C2A6202 -->
<a id="xid-9E4B7C2A6202"></a>

# Brownfield Pattern Learning

Learn the target system's existing patterns before selecting a design approach.
The purpose is to prevent unnecessary complexity and preserve the operational
level that the service can actually support.

## Inputs

- bounded change difference and target service;
- current source, tests, configuration, operations, and incident evidence;
- service catalog and service-interaction/data-flow Knowledge;
- operational constraints, support ownership, and decision owner.

If evidence is missing, stale, or contradictory, record an impact-bearing
`unknown`; do not promote a guess into a pattern.

## Outputs

Produce:

- pattern inventory and scope;
- representative peer files/components/flows and selection basis;
- observed pattern rule and counterexamples;
- operational baseline: deployment, monitoring, recovery, support, data, and
  failure-handling expectations;
- complexity delta: new concepts, dependencies, states, configuration,
  runtime paths, support steps, and failure modes;
- decision basis for `follows`, `adapts`, `introduces`, or `unknown`;
- alternatives, deviation rationale, risks, owner, and handoff.

## Learning method

1. Declare the target scope and the decision the pattern study must support.
2. Search Knowledge and inspect representative peers in the same component,
   package, service, or responsibility boundary.
3. Select a local majority only when the peer set is coherent and the evidence
   is strong. Record peer paths, rule signatures, counts, exceptions, and
   confidence. One convenient example is not a rule.
4. Compare the candidate with the observed pattern across structure, contracts,
   data flow, state, errors, tests, deployment, monitoring, recovery, and
   operator actions.
5. Estimate the candidate's complexity and operational delta before deciding.
6. Hand off the decision basis to `brownfield_workflow` and
   `brownfield_execution_planning`; do not silently choose a new architecture.

## Complexity and operability guard

Prefer the existing pattern when it satisfies the approved change. An
`adapts` or `introduces` result requires explicit evidence that the existing
pattern is insufficient and must state:

- added concepts, dependencies, configuration, states, and code paths;
- deployment and migration impact;
- monitoring, alerting, diagnosis, restart, rollback, and recovery impact;
- operator skill, runbook, support, and ownership impact;
- test and evidence burden;
- why the operational owner can support the new level.

Do not reject a design only because it is different; reject or escalate it when
the complexity or operational burden is unexplained, unowned, or inconsistent
with the service's demonstrated operating level.

## Work item shape

Each result contains `id`, `target`, `peer_scope`, `pattern_rule`, `evidence`,
`exceptions`, `pattern_decision`, `complexity_delta`, `operational_delta`,
`owner`, `next_action`, and `completion_criterion`. Unknowns state reason,
impact, resolver, and owner.

## Summary

Start with `Status`, `Result`, `Evidence`, `Open Items`, and `Handoff`. Do not
approve business requirements, design, release, or residual risk on behalf of
the responsible human.
