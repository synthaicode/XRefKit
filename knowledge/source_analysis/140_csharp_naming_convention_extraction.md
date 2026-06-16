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
| property | modifier-bearing `Type Name { get/set/init` or `Type Name =>` (no parens) | dominant casing (typically `PascalCase`) |
| field | modifier-bearing `Type Name = ...;` / `Type Name;` (no `{`/`(`) | casing distribution + **underscore-prefix** rate; **bimodal** (private `_camelCase` vs public/const `PascalCase`) |
| parameter | identifiers parsed from detected method headers' parameter lists | dominant casing (typically `camelCase`) |

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
- field underscore prefix: share of fields starting with `_`. Field casing is
  **bimodal** (private `_camelCase` vs public/const `PascalCase`), so the
  underscore-prefix rate is a better signal than a single dominant casing.

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

## Applying Strictly To New Code Only (delta scope)

Enforcing a derived convention against the whole tree would flag the codebase's
own existing deviations (the outliers above) — strictness on a brownfield repo
lights up its history. The fix is to separate the **derivation** scope from the
**application** scope:

- derive the convention from the whole tree (accuracy), then
- apply the strict check only to declarations on lines **added vs a base ref**.

`csharp_naming_profile.py --changed-vs <gitref>` does exactly this: it derives
the profile from the tree, then checks only declarations whose line is in the
`git diff --unified=0 <ref>` added set. **Existing code is never re-checked, so
historical outliers are not reported** — only new/changed names are held to the
existing convention. New files must be tracked (staged or committed) to appear
in the diff, per standard git semantics.

Two more guards keep strictness honest:

- **Confidence gate**: a convention is enforced only when its dominant share is
  high enough (the interface `I` prefix is demanded only when its existing share
  is `>= 90%`); a split distribution is left advisory, not guessed.
- **Field casing is not strictly enforced on the delta**: field naming is
  visibility-dependent (private `_camelCase` vs public/const `PascalCase`) and
  the extractor does not resolve visibility, so a changed field is reported but
  not flagged on casing. Use the underscore-prefix rate as the descriptive
  signal instead.
- **Advisory, per-case**: a flagged new name is a candidate for judgment, never
  an auto-rename. Deviating is acceptable when it matches an existing deliberate
  exception; otherwise conform.

This is the same "derive globally, apply to the delta, escalate the rest"
pattern used to keep the error-policy locators from drowning a brownfield repo
in known findings.

### Baseline ratchet (full-scan complement)

When a git delta is not available (a periodic full scan rather than a PR check),
use a baseline instead: `--write-baseline <path>` snapshots the current outliers
as accepted (keyed `file::name` per kind), and `--baseline <path>` then reports
only outliers **not** in that snapshot. Existing deviations are suppressed; only
*new* ones since the baseline surface. This ratchets a brownfield repo — it does
not force existing names to change, but stops new deviations from accumulating.
Delta-scope and baseline are complementary: delta gates a change at PR time,
baseline gates the whole tree over time.

## Limits (first version)

- **Member detection is heuristic**: method, property, and field declarations
  must carry at least one access/declaration modifier, which cleanly excludes
  call sites, locals, and most constructors but **misses interface-body and
  modifier-less (implicitly private) members**. Public-surface members — the
  ones that matter most for matching — almost always carry a modifier, so the
  casing profile stays representative. Full coverage is a Roslyn follow-up.
- Constructors are excluded by dropping method names equal to a known type name.
- **Parameters** are read from detected method headers; constructor and
  modifier-less method parameters are therefore missed.
- Enum members are not yet a separate kind; suffix detection is a single
  trailing PascalCase token.

## Relationship

- Pairs with [.NET change analysis viewpoints](120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)
  (placement / responsibility / prohibited changes) — that page answers *where*
  and *what* to change; this one answers *what to call it*.
- Same descriptive, candidate-only philosophy as the error-policy locator tiers
  ([131](131_csharp_error_policy_locator_tiers.md#xid-D1F4A7C3E209)).
