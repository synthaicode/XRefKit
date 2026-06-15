<!-- xid: B4F7E1A2C903 -->
<a id="xid-B4F7E1A2C903"></a>

# CSharp Naming-Convention Extraction (Brownfield)

In a brownfield codebase, new classes and methods must match the names that are
already there, not an external style guide. This page defines how to extract the
**de-facto** naming conventions from existing C# so new code conforms.

It is the naming axis of brownfield local-rule extraction; it complements the
placement / responsibility / prohibited-change viewpoints in
[.NET change analysis viewpoints](120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201).
The deterministic extractor is `tools/csharp_naming_profile.py`.

## Boundary (binding)

- **Descriptive, not enforcing.** The dominant convention is *guidance for new
  code*. It is never auto-applied and existing names are not renamed.
- **Outliers are exceptions to understand, not defects.** A name that deviates
  from the dominant casing is reported with `file:line` so a human can see
  whether it is legacy debt or a deliberate local exception — it is not a
  verdict.
- **Representative, not exhaustive.** Method detection is heuristic (see below);
  the profile characterizes the dominant rule, it does not enumerate every
  identifier.
- Comments and string literals are scrubbed before matching so identifiers
  inside them are not mistaken for declarations.

## What To Extract

| Kind | Detection | Convention signals |
|---|---|---|
| type (`class` / `record` / `struct`) | `class`/`struct`/`record`/`record struct`/`record class` + name | dominant casing; common **type suffixes** (role vocabulary: `Service`, `Builder`, `Visitor`, `Options`, `Result`, `Exception`, ...) |
| `interface` | `interface` + name | dominant casing; **`I` prefix** rate |
| method | declaration carrying >= 1 access/declaration modifier + return type + name `(` | dominant casing; **`Async` suffix** rate among async methods |

### Casing taxonomy

`PascalCase`, `camelCase`, `_camelCase` (underscore-prefixed field style),
`SCREAMING_SNAKE` (const), `other`. Underscore-prefixed names keep the `_`
marker (`_camelCase`, `_PascalCase`) because the prefix is itself a convention.

### Affix rules (de-facto, with share)

- interface `I` prefix: share of interfaces matching `^I[A-Z]`.
- method `Async` suffix: share of methods ending in `Async` (paired with whether
  they are actually async is a Roslyn follow-up; the suffix share alone is the
  first signal).
- type suffix vocabulary: the top single-token PascalCase suffixes, which encode
  the codebase's role naming (a new repository class should likely end in the
  suffix the codebase already uses for that role).

## How To Derive The Rule

For each kind: take the **most common casing** as the convention (with its
share), list the **top suffixes** as the role vocabulary, compute **affix
shares**, and list the **outliers** (names not in the dominant casing) with
`file:line`. A high dominant share (e.g. >= 95%) means a strong rule new code
must follow; a split distribution means the codebase itself is inconsistent and
the choice should be escalated rather than guessed.

## How New Code Uses It

- Name new types/interfaces/methods in the dominant casing.
- Reuse the existing **suffix vocabulary** for the role (don't invent `Helper`
  if the codebase uses `Service`/`Manager`).
- Honor the interface `I` prefix and the `Async` suffix if their share is high.
- Before deviating, check the outliers: deviating is only safe if it matches an
  existing, deliberate exception pattern — otherwise conform.

## Limits (first version)

- **Method detection is heuristic**: a declaration must carry at least one
  access/declaration modifier, which cleanly excludes call sites and most
  constructors but **misses interface-body and modifier-less (implicitly
  private) method signatures**. Public-surface methods — the ones that matter
  most for matching — almost always carry a modifier, so the casing profile
  stays representative. Full coverage is a Roslyn follow-up.
- Constructors are excluded by dropping method names equal to a known type name.
- Properties, fields, parameters, enum members, and constants are out of scope
  in the first version.
- Suffix detection is a single trailing PascalCase token.

## Relationship

- Pairs with [.NET change analysis viewpoints](120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)
  (placement / responsibility / prohibited changes) — that page answers *where*
  and *what* to change; this one answers *what to call it*.
- Same descriptive, candidate-only philosophy as the error-policy locator tiers
  ([131](131_csharp_error_policy_locator_tiers.md#xid-D1F4A7C3E209)).
