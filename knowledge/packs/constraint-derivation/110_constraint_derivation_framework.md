<!-- xid: 81A6C4E2B190 -->
<a id="xid-81A6C4E2B190"></a>

# Constraint Derivation Framework

## Purpose

This pack exists to surface where AI would otherwise complete unresolved design
behavior statistically across requirements, design, and implementation.

The output is not approval.
The output is a machine-derived gate list that a human must confirm before
implementation proceeds.

## Operating Flow

```text
design artifacts
  -> primary constraint-derivation Skills
  -> requirement confirmation items with traceable ids
  -> optional secondary commonality pass
  -> human confirmation
  -> implementation
```

```text
implemented code or code-plus-structure artifacts
  -> upward constraint-derivation Skills
  -> implicit assumptions, missing alternatives, or boundary-failure scenarios
  -> human confirmation
  -> design feedback or implementation correction
```

## Routing Table

| Skill | Target design area | Prefix |
|---|---|---|
| `design_constraint_derivation` | data structure, DB constraint, relation, operation | `DCD-` |
| `ui_constraint_derivation` | screen, input, action, transition | `UCD-` |
| `logic_constraint_derivation` | branch, calculation, state transition, approval logic | `LCD-` |
| `integration_constraint_derivation` | API, webhook, file, messaging integration | `ICD-` |
| `async_constraint_derivation` | queue, batch, schedule, async state | `ACD-` |
| `auth_constraint_derivation` | auth, role, session, tenant boundary | `AACD-` |
| `code_constraint_derivation` | C# code-level implicit assumptions and asymmetric branches | `CCD-` |
| `cross_constraint_derivation` | DDL and code mismatch analysis | `XCD-` |
| `integration_scenario_derivation` | DDL, code, and boundary-order integration scenarios | `ISD-` |
| `commonality_derivation` | secondary cross-skill aggregation after primary outputs | `CD-`, `CB-` |

## Shared Principles

1. Run downward derivation before implementation claims, and run upward derivation before accepting generated code behavior as design-valid.
2. A derived item is not yet a confirmed requirement.
3. Unresolved items stay explicit as `未確定`.
4. Every derived item keeps traceable ids.
5. Do not let these unresolved items leak into test cases as substitute requirements.

## Primary And Secondary Pass Boundary

- Primary Skills perform vertical derivation from one design area to required confirmations.
- Upward Skills perform reverse derivation from code or mixed code-plus-structure artifacts to implicit assumptions, mismatches, and failure scenarios.
- `commonality_derivation` performs a secondary horizontal pass over completed primary outputs.
- The secondary pass never replaces missing primary derivation.
