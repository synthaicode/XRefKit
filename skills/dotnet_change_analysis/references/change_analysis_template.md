<!-- xid: 6B38F0E4C2A7 -->
<a id="xid-6B38F0E4C2A7"></a>

# .NET Change Analysis Note

## Request Summary

- request:
- target path:
- scope:
- generated_at:

## Scope Targets

| Item | State | Evidence | Notes |
|------|------|------|------|
| solution |  |  |  |
| project |  |  |  |
| feature/module |  |  |  |

## Semantic-Inventory Mode (only if used)

Leave empty unless a grep-weak question required the deterministic pack (DI
lifetimes, attribute values, async-CT, IDisposable ownership, reflection binding,
transitive impact). Inventory output is a candidate fact, not a verdict.

| Grep-weak Question | Inventory Tool / File | Generated | Notes |
|------|------|------|------|
|  |  |  |  |

## Structure And Responsibility Split

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| major layers and responsibilities are identified |  |  |  |  |
| de-facto responsibilities are derived from behavior evidence (not names) |  |  |  |  |
| name-behavior mismatches are recorded |  |  |  |  |
| duplicated rule ownership is checked |  |  |  |  |
| dependency direction is identified |  |  |  |  |
| extension points are identified |  |  |  |  |

## Entry Points And Dependency Direction

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| startup path is identified |  |  |  |  |
| request, batch, and event entry points are identified |  |  |  |  |
| main call chain is identified |  |  |  |  |

## Structure Pivots

Record local artifacts that decide runtime structure. For non-standard or
custom-framework systems, this section is required. Do not list every binding
token here; put non-compiler-enforced tokens in `Implicit Runtime Binding`.

| Pivot | Kind | Behavior Controlled | Activated Code / Artifact | Source | State | Evidence | Silent Breakage Mode |
|------|------|------|------|------|------|------|------|
|  |  |  |  | documented / implicit |  |  |  |

## DI Registration And Lifetimes

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| registration sites and lifetimes are identified |  |  |  |  |
| captive-dependency risks are checked |  |  |  |  |
| hosted services and background registrations are identified |  |  |  |  |

## Pipeline Structure And Order

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| local pipelines and their stages are identified |  |  |  |  |
| the local ordering rule and its source (explicit or implicit) are extracted |  |  |  |  |
| order-dependent behavior risks are checked |  |  |  |  |

## Route / Usecase Trace Matrix

Trace representative runtime paths across structural authority, code, output,
state, and persistence boundaries. A route list without the cross-file binding
path is incomplete. Use this for representative paths, not as a duplicate of
the full command or endpoint inventory.

| Trace | Entry Identity | Structural Authority | Binding Mechanism | Executable Owner | Result Selector | Output Boundary | Model/Input Binding | State Boundary | Persistence Boundary | Evidence | Unknown / Follow-up |
|------|------|------|------|------|------|------|------|------|------|------|------|
|  |  |  |  |  |  |  |  |  |  |  |  |

## Convention-Based Discovery

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| convention-based wiring points (scanning, naming, placement) are identified |  |  |  |  |
| the matching convention and scan scope are extracted |  |  |  |  |
| rename-and-move sensitivity is recorded |  |  |  |  |

## Implicit Runtime Binding

Record non-compiler-enforced bindings such as XML/config strings, reflection
type names, controller return strings, view/ref names, request/form fields,
serialization names, model keys, command names, redirect targets, and custom
registry keys. Do not repeat the same item as a generic change checklist; promote
only actionable silent-break rules into `Prohibited Changes`.

| Binding | Producer | Consumer | Token | Mechanism | State | Evidence | Silent Breakage Mode | Safe Alternative |
|------|------|------|------|------|------|------|------|------|
|  |  |  |  |  |  |  |  |  |

## Configuration Boundary

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| configuration sources are identified |  |  |  |  |
| options binding and consumers are identified |  |  |  |  |
| environment-dependent behavior and feature toggles are identified |  |  |  |  |

## Build Configuration Behavior

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| conditional compilation symbols and gated behavior are identified |  |  |  |  |
| multi-target and MSBuild-condition variants are identified |  |  |  |  |
| configurations requiring verification for this change are recorded |  |  |  |  |

## API, Database, And External Integration Boundary

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| API boundary is identified |  |  |  |  |
| database boundary is identified |  |  |  |  |
| external service or messaging boundary is identified |  |  |  |  |

## Error Handling Contract

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| error representation conventions are identified |  |  |  |  |
| translation and propagation points are identified |  |  |  |  |
| retry and compensation conventions are identified |  |  |  |  |

## Security Boundary Placement

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| authentication and authorization enforcement points are identified |  |  |  |  |
| unprotected entry paths are checked |  |  |  |  |
| security-review handoff items are recorded when needed |  |  |  |  |

## Logging Policy

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| logging points are identified |  |  |  |  |
| sensitive-data exposure risk is checked |  |  |  |  |
| monitoring or operations impact is identified |  |  |  |  |

## Attribute Usage

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| standard and custom attributes are identified |  |  |  |  |
| attribute definition origin is identified |  |  |  |  |
| consuming mechanism and activation condition are identified |  |  |  |  |

## Concurrency And Execution Timing

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| async and background execution paths are identified |  |  |  |  |
| shared state and locking points are identified |  |  |  |  |
| transaction and retry boundaries are identified |  |  |  |  |

## Performance And Resource Efficiency

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| hot paths and heavy I/O are identified |  |  |  |  |
| resource lifetime and ownership are identified |  |  |  |  |
| avoidable overhead risk is identified |  |  |  |  |

## Test Boundary

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| related tests are identified |  |  |  |  |
| missing regression coverage is identified |  |  |  |  |
| test isolation risks (shared state, real time, ordering) are identified |  |  |  |  |

## Change Placement Basis

| Check Item | State | Evidence | Change Impact | Unknown / Follow-up |
|------|------|------|------|------|
| de-facto home of the affected logic is identified |  |  |  |  |
| placement options and their responsibility impact are recorded |  |  |  |  |
| second-owner risks are checked |  |  |  |  |

## Prohibited Changes

Derived from extracted local rules only — silent breakage with no compiler or
analyzer diagnostic. Compiler-caught mistakes do not belong here. This section
replaces any separate change-impact checklist for structure-sensitive tokens.

| Prohibited Change | Class | Basis (extracted rule) | Silent Breakage Mode | Evidence | Safe Alternative / Deviation Condition |
|------|------|------|------|------|------|
|  |  |  |  |  |  |

## Domain Knowledge Candidate

Include only if the analysis reveals reusable current structure knowledge that
later Skills can select and use. Do not add redundant `applies_to`; Skill-side
selection owns applicability. Do not require path when stable document identity
can resolve the content. Use the table only; do not duplicate the same metadata
as prose bullets.

| Field | Value |
|------|------|
| framework_family |  |
| routing_authority |  |
| entry_binding |  |
| controller_binding |  |
| view_binding |  |
| model_binding |  |
| state_boundary |  |
| persistence_boundary |  |
| change_sensitive_tokens |  |
| prohibited_change_rules |  |
| unresolved_verification |  |

## Impacted Targets

Found grep-first (full reference surface), then classified by impact pattern.
Separate the two boundaries: every referencing file is in the review boundary; only
the sites the change actually breaks are must-change. Use this section for the
specific change objective, not to restate the structure pivot or implicit binding
inventories.

### Must-change boundary (sites the change breaks)

| Target | Why it breaks | Evidence |
|------|------|------|
|  |  |  |

### Review boundary (references to thread the change, may not break)

| Target | Why review | Evidence |
|------|------|------|
|  |  |  |

## Unresolved Items

| Item | Missing Evidence | Suggested Next Check |
|------|------|------|
|  |  |  |

## Summary

- key structure finding:
- key change impact:
- highest risk:
- recommended next investigation:
