<!-- xid: A1D4E8C93B71 -->
<a id="xid-A1D4E8C93B71"></a>

# Code Constraint Derivation Catalog

## Purpose

This catalog extracts only explicit implementation choices from C# code that
indicate hidden preconditions, alternative flows, invariants, or business-rule
embeddings.

## Signal Areas

| Signal | Typical code shape | Derived concern |
|---|---|---|
| guard plus throw | `if (...) throw ...` | precondition that must already hold |
| `ArgumentNullException` or `ArgumentException` | explicit argument guard | caller contract and missing upstream rule |
| `Debug.Assert` | development-only expectation | assumption not enforced in production |
| `return null` | absence path delegated to caller | alternative flow exists and needs agreement |
| empty catch | failure is silently ignored | risky extension flow |
| log-only catch | failure is observed but processing continues | continuation policy needs agreement |
| `Single()` or `SingleAsync()` | exact one-item assumption | invariant or missing multiplicity handling |
| `First()` or `FirstOrDefault()` | existence assumption or partial multiplicity handling | alternative flow or implicit multiplicity rule |
| nullable-type asymmetry | `Type?` vs non-null peer | asymmetrical business rule |
| magic values | hardcoded numbers or strings | embedded business threshold or state rule |
| transaction boundary choice | transaction span or per-step commit | atomicity or partial-failure policy |
| visibility choice | `private set`, `internal class` | update-path or boundary decision |

## Classification Rule

- default to business-layer confirmation when the signal changes business rule,
  threshold, state, failure handling, or atomicity
- keep implementation-layer notes only for local structure choices that do not
  alter business behavior unless missing guarantees escalate them

## Output Shape

- derivation basis table with `CCD-` ids
- high-priority confirmation items
- implementation-layer notes when justified

