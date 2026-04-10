<!-- xid: D94E3B3A7C11 -->
<a id="xid-D94E3B3A7C11"></a>

# Skill: dotnet_change_analysis

## Purpose

Analyze an existing .NET application structure and produce a Markdown change-analysis note that can be used as working material before design or implementation changes.

Use the canonical viewpoints in `knowledge/source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201`.

## Required Knowledge (XID)

- [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)
- [Dotnet change analysis viewpoints](../../knowledge/source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)

## Optional References

- [Dotnet change analysis template](./references/change_analysis_template.md)

## Inputs

- target path (repository root, solution, or project)
- change request or analysis objective
- optional scope filters (solution, project, directory, feature, file pattern)
- optional output path for the generated Markdown

## Outputs

- Markdown change-analysis note
- scoped target list
- impacted boundary list
- uncertainty list
- check results by viewpoint

## Startup

- Confirm the target path exists.
- Confirm the change request or analysis objective exists.
- Confirm the review scope is defined when filters are supplied.
- Load the dotnet change-analysis viewpoints.
- Record `unknown` when project or runtime boundaries cannot be established cleanly.

## Planning

- Define the analysis scope:
  - repository
  - solution
  - project
  - directory or file subset
- Define the output path:
  - user-specified path
  - default working Markdown path when no path is supplied
- Prepare viewpoint buckets for:
  - structure and responsibility split
  - entry points and dependency direction
  - configuration boundary
  - API, database, and external integration boundary
  - logging policy
  - attribute usage
  - concurrency and execution timing
  - performance and resource efficiency
  - test boundary
  - change impact and unresolved items
- If the scope can be separated by solution or project without cross-scope consistency risk, decompose the read-only investigation by scope and execute through subagents.

## Execution

- Identify the solution, projects, startup paths, and major module boundaries.
- Trace the current execution entry points and main dependency directions.
- Record configuration sources, option bindings, and environment-dependent behavior.
- Record API, database, messaging, and external service boundaries.
- Record logging policy, sensitive-data handling, and operational monitoring impact.
- Analyze attribute usage with the following rule:
  - extract attribute usage candidates from `[]` syntax
  - exclude numeric tokens and syntax that is not an attribute
  - resolve each candidate as both `Xxx` and `XxxAttribute`
  - confirm namespace and definition origin
  - record usage location, arguments, and target
  - confirm the consuming code and the activation condition
  - mark the attribute as `unknown` when the consuming mechanism cannot be confirmed
- Record concurrency, scheduling, shared state, cancellation, and transactional boundaries.
- Record performance-sensitive paths and resource lifetime/ownership points.
- Record test boundaries and the tests that should detect the intended change.
- Generate the Markdown note by using the template structure from `references/change_analysis_template.md` or an equivalent structure.

## Monitoring and Control

- Treat every viewpoint as recorded only when it has a state:
  - `done`
  - `unknown`
  - `not_applicable`
- Treat unrecorded viewpoints as analysis leaks.
- Downgrade weakly supported conclusions to `unknown`.
- Separate:
  - observed structure
  - inferred change impact
  - missing evidence
- Preserve the evidence path for every non-trivial conclusion.

## Closure

- Return the Markdown change-analysis note.
- Return scoped targets, impacted boundaries, and unresolved items.
- Mark every uncertain or out-of-scope conclusion with its missing evidence or reason.

## Rules

- Do not decide implementation policy unless the user explicitly asks for it.
- Do not invent a cleaner target architecture without explicit evidence and change intent.
- For custom attributes, do not stop at inventory; confirm definition, usage, consuming mechanism, and activation condition.
- For logging analysis, include both emitted information and forbidden information exposure risk.
- For concurrency analysis, include execution timing, shared state, and transaction boundaries.
- For performance analysis, include hot paths, avoidable overhead, and resource lifetime ownership.
- Use subagents only when scope boundaries stay explicit and cross-scope reasoning is not required.

## Failure Handling

- If solution or project boundaries cannot be resolved, continue and mark `unknown`.
- If external package or framework source is unavailable, record the unresolved dependency and continue.
- If the Markdown output path is not writable, return the content and the intended path without deleting any existing files.
