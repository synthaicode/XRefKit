<!-- xid: C3F60AEB5D93 -->
<a id="xid-C3F60AEB5D93"></a>

# Integration Scenario Derivation Catalog

## Purpose

This catalog derives boundary-crossing failure and retry scenarios from the
combination of DDL, processing order, and external system boundaries.

## Scenario Areas

| Structure | Derived concern |
|---|---|
| DB save then external call | saved data remains when the external step fails |
| external call then DB save | external state commits without internal record |
| multi-step external chain | compensation need for earlier successful steps |
| batch over N-related records | partial completion and rerun policy |
| unique constraint plus retry | duplicate registration or replay behavior |
| logical delete plus delayed action | stale-read or state-drift handling |
| external nullability or deletion semantics | hidden assumption about external data shape |
| timeout plus no explicit handling | indeterminate in-flight state |
| non-idempotent external API plus retry | duplicate side effects |
| parallel jobs or delayed operations | state skew between steps |

## Classification Rule

- compensation design needed
- implementation design needed
- test-case candidate only after the above are confirmed

## Output Shape

- derivation basis table with `ISD-` ids
- compensation-design items
- partial-failure matrix
- post-confirmation test-case candidates

## Knowledge Relations

- part_of: [Constraint Derivation Framework](110_constraint_derivation_framework.md#xid-81A6C4E2B190)
