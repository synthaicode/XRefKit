<!-- xid: B2E5F9DA4C82 -->
<a id="xid-B2E5F9DA4C82"></a>

# Cross Constraint Derivation Catalog

## Purpose

This catalog compares DDL structure and C# processing structure as two
projections of the same use case and surfaces mismatches that imply missing
flows or undocumented assumptions.

## Match Areas

| DDL side | Code side | Derived concern |
|---|---|---|
| nullability | null checks or lack of them | missing absence handling or unstable guarantee |
| multiplicity | `Single`, `First`, collection handling | implicit existence or uniqueness assumptions |
| enum/status values | switch cases and default handling | missing state coverage or undocumented state |
| FK delete policy | delete flow checks | missing restriction, cascade, or set-null handling |
| CHECK/UNIQUE constraints | app-layer validation or lack of it | missing error path or duplicated rule ownership |
| DEFAULT values | explicit initialization or omission | duplicated default rule or hidden DB dependency |

## Priority Rule

- high: code would fail or mis-handle valid DDL states
- medium: duplicated or drifting definitions
- low: defensive or historical traces that still deserve recording

## Output Shape

- derivation basis table with `XCD-` ids
- missing-flow confirmations
- implicit-assumption confirmations
- duplicated-definition checks

