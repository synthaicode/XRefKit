<!-- xid: D9C3F0A7E412 -->
<a id="xid-D9C3F0A7E412"></a>

# C# Custom Attribute Design Principles

Design principles for **authoring** a custom attribute (a type you define that
derives from `System.Attribute`). This is the authoring axis; it is distinct
from the attribute **usage**-validation rule in
[C# review spec](100_csharp_review_spec.md#xid-30E6A4F6F3AA) (Attribute Value
Misuse), which checks how an existing attribute is applied.

Most of these principles are mechanically enforced by built-in .NET analyzers,
so detection is **delegated** (same approach as
[error-policy analyzer rule map](../source_analysis/132_csharp_error_policy_analyzer_rule_map.md#xid-C7A1E94D3B62)),
not hand-built. The remaining principles are judgment-only.

## Boundary (binding)

- These are principles for **new** custom attributes; existing attributes are
  not auto-changed. Deviations (e.g. an intentional abstract base attribute) are
  per-case exceptions, not defects.
- The analyzer-backed principles are **default-off or suggestion-only** in
  .NET 10 (see table), so they must be enabled explicitly via a collection
  profile — do not rely on SDK defaults (same finding as the error-policy
  Collection Profile). Candidates flow through the existing
  `collect_analyzer_sarif.py` -> `sarif_to_locator.py` pipeline if an
  attribute locator family is added (follow-up).

## Principles (analyzer-backed)

| # | Principle | Enforcing rule | Category / default (.NET 10) |
|---|---|---|---|
| 1 | Name a custom attribute with the `Attribute` suffix (`FooAttribute : Attribute`) | **CA1710** Identifiers should have correct suffix | Naming / off |
| 2 | Mark the attribute with `[AttributeUsage]` and specify valid targets (omitting it defaults to `AttributeTargets.All`) | **CA1018** Mark attributes with AttributeUsageAttribute | Design / suggestion |
| 3 | Provide an accessor property for every constructor argument (required args -> read-only property; optional args -> read/write property; same name, Pascal property vs camel parameter) | **CA1019** Define accessors for attribute arguments | Design / off |
| 4 | Seal the attribute type (or make it `abstract` for a deliberate base) — sealing skips the inheritance-hierarchy search in `GetCustomAttribute` | **CA1813** Avoid unsealed attributes | Performance / off |

Verified 2026-06-16 against Microsoft Learn (see Sources).

## Argument design (from CA1019 / Framework Design Guidelines)

- **Required arguments are positional**: constructor parameters, each with a
  corresponding **read-only** property (`public string Name { get; }`).
- **Optional arguments are named**: settable properties (`public bool Strict
  { get; set; }`), not extra constructor overloads.
- Constructor parameter and property differ only by casing (camel parameter,
  Pascal property), so the value is retrievable at execution time.
- Prefer a single constructor; avoid overloads that blur which arguments are
  mandatory.

## Principles (judgment-only — no single analyzer)

- **Immutable / minimal**: an attribute is metadata. Keep required state in
  read-only properties; avoid behavior/side effects in the attribute itself.
- **Attribute-legal argument types only**: constructor/property argument types
  must be the compile-time constant set the C# spec allows (primitives,
  `string`, `Type`, enums, `object`, and single-dim arrays of these). This is a
  compiler constraint, but choosing argument shape that stays within it is a
  design decision.
- **`AllowMultiple` and `Inherited` are deliberate choices** on
  `[AttributeUsage]`: decide whether the attribute may repeat on one target and
  whether it is inherited by derived types/overrides, rather than accepting the
  defaults silently.

## Detection / Collection

Enable CA1018, CA1019, CA1710, CA1813 in a collection profile (they are not on
by default) and collect them through the verified
`-p:ErrorLog=<file>%2cversion=2.1` build, then normalize. A future
`cs.attr.*` locator family in `sarif_to_locator.py` would map:

- `CA1710` (on an `Attribute`-derived type) -> `cs.attr.suffix`
- `CA1018` -> `cs.attr.attribute_usage`
- `CA1019` -> `cs.attr.argument_accessors`
- `CA1813` -> `cs.attr.sealed`

These never auto-fail; they are candidates for the authoring decision.

## Relationship

- Usage axis: [C# review spec — Attribute Value Misuse](100_csharp_review_spec.md#xid-30E6A4F6F3AA)
  checks how attributes are *applied*; this page governs how they are *authored*.
- The `Attribute` suffix is also a naming convention; CA1710 is its canonical
  enforcer, complementing the de-facto suffix vocabulary in
  [naming-convention extraction](../source_analysis/140_csharp_naming_convention_extraction.md#xid-B4F7E1A2C903).

## Sources

- CA1018 — `learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1018`
- CA1019 — `.../ca1019`
- CA1710 — `.../ca1710`
- CA1813 — `.../ca1813`
