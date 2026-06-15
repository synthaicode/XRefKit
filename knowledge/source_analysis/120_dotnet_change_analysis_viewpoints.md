<!-- xid: 2E7B5A1FD201 -->
<a id="xid-2E7B5A1FD201"></a>

# Dotnet Change Analysis Viewpoints

This page defines .NET-specific viewpoints for analyzing an existing application structure before change planning, design, or implementation.

For the naming axis (matching new class/method names to existing de-facto
conventions), see [CSharp naming-convention extraction](140_csharp_naming_convention_extraction.md#xid-B4F7E1A2C903).

## Core Viewpoints

| Viewpoint | What to confirm |
|------|------|
| Solution and project structure | which solutions, projects, assemblies, and module boundaries define the current unit of change |
| De-facto responsibility split | which responsibilities each layer or component actually carries, derived from behavior evidence rather than names or folders, including name-behavior mismatches and duplicated rule ownership |
| Entry points | where execution starts for web requests, background jobs, workers, scheduled tasks, functions, or message consumers |
| Dependency direction | how application, domain, infrastructure, shared libraries, and framework code depend on one another |
| DI registration and lifetimes | where services are registered, with which lifetimes, and where captive-dependency, hosted-service, or container-bypass risks exist |
| Pipeline structure and order | which execution pipelines exist in this codebase, where their stage order is established, which local rule governs that order, and which behavior the order controls |
| Convention-based discovery | where naming, placement, or assembly scanning determines runtime wiring, which local convention governs it, and which renames or moves would silently break it |
| Security boundary placement | where authentication and authorization are structurally enforced and which entry paths are unprotected (placement only; vulnerability assessment belongs to security review) |
| Configuration boundary | where settings are loaded, bound, overridden, and consumed across environment-specific behavior, including feature toggles and the local rules for environment-dependent switching |
| Build-configuration-dependent behavior | where conditional compilation, multi-targeting, or MSBuild conditions create behavior variants that a single compilation pass cannot see |
| API and integration boundary | where controllers, endpoints, gRPC handlers, clients, queues, and external service adapters connect, and which serialization contract conventions (naming policy, enum and null representation, compatibility rules) apply on the wire |
| Data boundary | where persistence, transactions, caching, mapping, and database migrations are controlled, including local serialization and mapping contract conventions |
| Error handling contract | which local rules govern error representation, translation, and propagation across boundaries — contract extraction only, not defect detection |
| Logging policy | where logs are emitted, which events are recorded, how levels are configured, and what sensitive information must not be emitted |
| Attribute usage | which standard and custom attributes affect routing, authorization, validation, serialization, transactions, DI, or custom framework behavior |
| Concurrency and execution timing | where async execution, background processing, retries, scheduling, shared state, cancellation, and transactional timing constraints exist |
| Performance-sensitive paths | where high-frequency paths, heavy I/O, expensive serialization, avoidable allocations, or repeated computation create risk |
| Resource efficiency | where disposable objects, connections, streams, buffers, threads, or singleton state require lifetime and ownership checks |
| Test boundary | which tests currently protect the target behavior and where additional regression coverage is needed |
| Change impact and uncertainty | which targets are directly or indirectly affected and which conclusions remain `unknown` because evidence is missing |

## Attribute Analysis Rule

- Extract attribute usage candidates from `[]` syntax.
- Exclude numeric tokens and syntax that is not an attribute.
- Resolve each candidate as both `Xxx` and `XxxAttribute`.
- Confirm namespace and definition origin.
- Record usage location, arguments, and target.
- Confirm the consuming code and the activation condition.
- Mark the attribute result as `unknown` when the consuming mechanism cannot be confirmed.

## Responsibility Extraction Rule

In brownfield code the responsibility split is usually not documented; it
must be derived from behavior evidence, not from names or folder claims.

- Derive each component's actual responsibility from evidence: what calls
  it, which data it owns or mutates, which business rules it evaluates.
- Record name-behavior mismatches as findings (a "Service" doing data
  access, a "Repository" holding business rules); the name never decides
  the responsibility.
- Detect duplicated rule ownership: the same business rule implemented or
  partially implemented in more than one place. Record every owner — a
  later fix must know whether it changes one owner or all of them.
- Extract implicit responsibility conventions ("validation happens in layer
  X") and record whether they are documented or implicit.
- Mark the responsibility `unknown` where the evidence is contradictory,
  and record the contradiction itself as a finding.

## Change Placement Basis Rule

The note must give the modification phase its placement basis — facts, not
the placement decision itself.

- Identify the de-facto home of the logic the change touches: where this
  kind of rule or behavior currently lives according to the extracted
  responsibility split.
- For each realistic placement option, record its responsibility impact:
  whether it follows the extracted local rules, and whether it would create
  a second owner for an existing rule.
- Do not select the placement; that decision belongs to planning or design.
  Record the facts that make the decision checkable.

## Prohibited Changes Derivation Rule

Convert the extracted local rules into explicit prohibitions for the
modification phase. A prohibition is a change that would break behavior
silently — without any compiler or analyzer diagnostic.

- Derive every prohibition from an extracted local rule or observed
  structural fact; never from generic best practices. No evidence, no
  prohibition.
- Do not prohibit what the compiler or a configured analyzer already
  rejects — those mistakes cannot land silently and need no prohibition.
- Each prohibition must record:
  - the prohibited change, stated concretely
  - the extracted local rule it derives from
  - the silent breakage mode (what behavior changes, with no diagnostic)
  - the evidence (file path, and command or pattern where relevant)
  - the safe alternative or the condition under which deviation is
    acceptable (including who decides)
- Classify each entry:
  - `hard`: the change silently breaks behavior in all known cases
  - `conditional`: the change is safe only with an accompanying step (for
    example a rename is safe only together with an explicit attribute)
- Deliberate design rules extracted from the code (documented or implicit)
  produce prohibitions against removing them casually; the deviation
  condition routes that decision to a human.

## DI Registration And Lifetime Rule

- Confirm registration sites and the lifetime chosen for each service
  (singleton, scoped, transient) including options, factories, and decorators.
- Confirm captive dependencies: a longer-lived service holding a
  shorter-lived one (for example scoped injected into singleton).
- Confirm hosted services and background registrations and their startup or
  shutdown ordering assumptions.
- Confirm components constructed with `new` inside layers that otherwise
  resolve through the container, and whether that bypass is intentional.
- For custom or wrapped containers, derive lifetime semantics from local
  evidence (container code, registration helpers, existing usage) instead of
  assuming a known container's behavior.

## Pipeline Structure And Order Rule

The goal is to extract this codebase's own pipeline rules from local
evidence, not to check the code against well-known framework ordering
recipes.

- Enumerate the pipelines that actually exist here, from local evidence:
  where execution chains are assembled (builder call sequences, registration
  order, custom pipeline or handler-chain classes, message processing
  chains, batch stage definitions).
- For each pipeline, extract the local ordering rule:
  - what establishes the order (code order, configuration, attributes,
    naming or placement conventions, a custom registry)
  - whether that rule is written down anywhere (docs, comments, tests) or
    exists only as an implicit convention — implicit rules are themselves a
    finding to record
- Determine what the order controls from local behavior and cite the local
  evidence; do not assume well-known framework ordering semantics for
  custom, wrapped, or extended pipelines — mark such assumptions `unknown`
  until local evidence confirms them.
- Confirm which order-dependent behavior the intended change could disturb,
  and whether the extracted local rule would make that disturbance visible.

## Convention-Based Discovery Rule

Runtime wiring decided by reflection, scanning, or conventions is invisible
to the compiler: a rename or move can break behavior without any diagnostic.

- Enumerate where runtime wiring is decided by naming, placement, or
  scanning: assembly-scanning registrations, suffix or marker-interface
  conventions, folder- or namespace-based routing, source-generator
  conventions.
- Extract the convention itself: what pattern is matched, where the scan
  runs, which assemblies or namespaces are included or excluded.
- Record rename-and-move sensitivity: which identifier or location changes
  would silently break discovery.
- Mark the discovery behavior `unknown` when the scanning mechanism cannot
  be confirmed from local evidence.

## Build Configuration Behavior Rule

A compilation pass sees one configuration at a time; this viewpoint records
the variants that exist across configurations. Rules the compiler itself
enforces within one configuration (nullable policy, warnings-as-errors,
analyzer config) are out of scope here.

- Enumerate conditional compilation symbols and the behavior differences
  they gate.
- Enumerate multi-target frameworks and per-TFM implementation splits.
- Enumerate MSBuild conditions that change project content per
  configuration or environment.
- Record which configurations the intended change must be verified against.

## Error Handling Contract Rule

The goal is to extract this codebase's error contract, not to detect defect
patterns — individual analyzer-detectable issues are out of scope.

- Confirm the representation convention: custom exception hierarchy, result
  or either types, error-code systems, and which layers use which.
- Confirm translation points: where infrastructure or third-party exceptions
  are wrapped or translated, and which local rule decides the target type.
- Confirm propagation conventions: what may cross each layer boundary, what
  is logged versus rethrown versus absorbed by design.
- Confirm retry and compensation conventions as local rules, including where
  they are allowed to apply.
- Record whether the contract is documented or implicit.

## Ambient Dependency Convention Rule

- Confirm whether local abstractions exist for time, ID generation,
  randomness, and environment access (for example a clock interface), and
  where the convention requires their use.
- Record the convention's enforcement status: when a configured analyzer
  (for example a banned-API rule) already enforces it, bypass enumeration is
  out of scope — record only the convention and that it is enforced.
- Where no enforcement exists, record bypasses only when they sit inside the
  intended change scope.

## Security Boundary Placement Rule

- Confirm where authentication schemes and authorization policies are
  defined and where they are structurally enforced (attributes, endpoint
  conventions, middleware).
- Confirm entry paths without protection — explicit opt-out markers (for
  example `AllowAnonymous` or an application-specific equivalent), unmapped
  endpoints, background entry points — and whether the exposure is
  intentional. Where protection is enforced by a local convention, extract
  that convention from local evidence first.
- Record placement and coverage only; suspected vulnerabilities are recorded
  for handoff to the security review skill, not assessed here.

## Logging Policy Rule

- Confirm where logs are emitted in request paths, batch paths, and integration paths.
- Confirm logging level control, sinks, enrichment, and environment-specific overrides.
- Confirm whether business events, exceptions, audit events, and performance signals are intentionally recorded.
- Confirm whether personally identifiable information, credentials, secrets, or oversized payloads could be emitted.
- Confirm whether the intended change alters monitoring, alerting, or operational procedures.

## Concurrency Rule

- Confirm async call chains, background workers, schedulers, queue consumers, and retry handlers.
- Confirm shared mutable state in singleton services, static fields, caches, and in-memory coordination.
- Confirm locking, semaphore, and transaction boundaries.
- Confirm cancellation and timeout propagation.
- Confirm duplicate execution and ordering risks.

## Performance And Resource Rule

- Confirm high-frequency or heavy-I/O paths before proposing or evaluating a change.
- Confirm resource lifetime and ownership for `IDisposable` and `IAsyncDisposable` objects.
- Confirm whether the change increases allocation, serialization, logging, connection, or retry overhead.
- Confirm whether long-running or background processes can retain memory, threads, or connections unexpectedly.

## Output Rule

Produce a Markdown note that records, for each viewpoint:

- state (`done`, `unknown`, or `not_applicable`)
- evidence
- change impact
- unresolved follow-up

Evidence must name the file path, and when the conclusion came from a command
or search, also the command or pattern used, so the check can be reproduced.

For each extracted local rule — ordering, discovery, error contract, ambient
dependency, configuration switching — record its source: documented (and
where) or implicit. Implicit rules are unresolved follow-up candidates by
default.

The note must also carry the prohibited-changes list derived from the
extracted rules (see Prohibited Changes Derivation Rule): each entry with its
basis, silent breakage mode, evidence, classification, and safe alternative.
