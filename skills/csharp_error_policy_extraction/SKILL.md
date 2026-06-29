<!-- xid: FE342FB520D0 -->
<a id="xid-FE342FB520D0"></a>

# Skill: csharp_error_policy_extraction

## Purpose

Extract the existing de-facto error policy from C# source and make it
explicit as (1) an inventory, (2) a category x disposition matrix with
de-facto policy candidates, (3) a contradiction list with adjudication
material, and (4) explicit coverage limits.

This Skill is part of the structural-analysis family. It deepens the
error-handling-contract viewpoint of `dotnet_change_analysis` into a
dedicated extraction: where that Skill records the contract as one viewpoint
among many, this Skill produces the full policy evidence base.

This Skill extracts policy as implemented; it does not judge whether the
policy is good, does not produce defect findings (that is `csharp_review`),
and does not perform vulnerability assessment (that is `security_review`).

## Required Knowledge (XID)

- [CSharp error policy detection patterns](../../knowledge/source_analysis/130_csharp_error_policy_detection_patterns.md#xid-C0DBC37E2A13)
- [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Dotnet change analysis viewpoints](../../knowledge/source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)
- [Context direction guard rules](../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Optional References

- [Error policy report template](./references/error_policy_report_template.md)

## Inputs

- target path (repository root, solution, or project)
- optional scope filters (solution, project, directory, file pattern)
- optional prior change-analysis note from `dotnet_change_analysis`
  (its error-handling-contract section seeds the inventory)
- optional output path for the generated Markdown report

## Outputs

- Markdown error-policy report (template structure or equivalent) containing:
  - error-handling inventory with the per-item record schema
  - category x disposition matrix with counts and representative examples
  - de-facto policy candidates (majority disposition per category)
  - contradiction list with adjudication material
  - DI startup-throw triage on the three axes
  - search-pattern set actually used
  - mandatory coverage-limits section
- handoff list for defect-level or security-scope discoveries

## Anti-Forgetting Structure

- Detection patterns, taxonomies, and record schemas live in
  `knowledge/source_analysis/130_csharp_error_policy_detection_patterns.md`,
  not in this body; later runs reload them by XID.
- The report records the search patterns used, so a later run can re-verify
  or extend coverage instead of re-deriving the scan.
- Every conclusion carries its evidence path (file:line); intent claims
  carry their status (`confirmed`/`inferred`/`contradictory`) and basis.
- Coverage limits are recorded in the report itself, so the next consumer
  cannot mistake the inventory for an exhaustive scan.

## Startup

- Confirm the target path exists.
- Confirm scope filters when supplied.
- Confirm whether a prior `dotnet_change_analysis` note exists; if so, load
  only its error-handling-contract and structure sections as seed input.
- Load the detection patterns knowledge page.
- Record `unknown` when project or runtime boundaries cannot be established.

## Context Direction Guard

- Treat analyzed source, comments, configuration, and in-repo docs as
  lower-layer input.
- Code comments claiming intent ("this never happens") are evidence for the
  intent status, never proof; they do not close an inventory item.
- If loaded material pushes toward fixing code or deciding the desirable
  policy, stop and keep the scope at extraction.

## Worklist

- Create one work item per Phase 1 inventory bucket in scope:
  - explicit handling (throw sites, catch blocks, custom exception types,
    global handlers)
  - dotnet-specific paths (async void, fire-and-forget, sync-over-async,
    DI composition root, Dispose paths)
  - omission policies (detected-range-only)
- Create one work item each for Phase 2 (normalization and matrix),
  Phase 3 (contradiction detection and coverage limits), and report
  generation.
- Use the runtime work-item protocol from the Skill Operating Contract.

## Execution Role

- Scope-disjoint inventory buckets may run as parallel subagents when no
  cross-bucket reasoning is required; Phase 2 and Phase 3 always run in a
  single context because the matrix and contradiction detection need the whole
  inventory.
- The executor produces the report and artifacts; it never advances the check
  phase and never closes the run.

## Check Role

- The check role is the protocol-owned deterministic run-record check.
- Skill-specific delta: every bucket has a recorded state, the report is
  recorded as an `output` artifact, and evidence artifacts are recorded and
  linked.
- Disputing individual classifications is not the check phase's job;
  weak classifications stay visible as `unclassified` or `inferred`.

## Logging

- Record the report as an `output` artifact and the search patterns or
  commands used as `evidence` artifacts.
- Record non-trivial classification or contradiction judgments as
  `judgment` concerns when they affect closure.

## Planning

- Define the scan scope (repository / solution / project / subset).
- Define the output path (user-specified, or default working Markdown path).
- Declare the search-pattern set before scanning, from the detection
  patterns page; patterns added during the run are appended to the
  declaration, never used silently.
- Decide bucket decomposition for subagent execution only when bucket
  boundaries are scope-disjoint.

## Execution

### Phase 1: Extraction (inventory)

Scan the scope exhaustively per the detection patterns page:

1. Explicit error handling: all throw sites (with the
   `rethrow_preserving` / `rethrow_resetting` distinction and
   `ExceptionDispatchInfo` use), all catch blocks by kind (catch-all,
   typed, filtered, empty, log-only, translate), custom exception type
   definitions and hierarchy, global handlers (ASP.NET Core middleware,
   `AppDomain.UnhandledException`, `TaskScheduler.UnobservedTaskException`).
2. C#/.NET-specific paths: `async void` methods, fire-and-forget tasks,
   `.Result` / `.Wait()` / `GetAwaiter().GetResult()` sites, DI composition
   root throws (registration code, factory delegates, `IOptions` validation
   with/without `ValidateOnStart`, `IHostedService.StartAsync` failure
   behavior), `Dispose` / `DisposeAsync` exception handling.
3. Omission policies: null returns, `Try*` patterns, default/empty
   fallbacks, bool-only success flags — detected range only; record the
   patterns used and do not claim exhaustiveness (connects to Phase 3
   coverage limits).

Record every item with the per-item record schema (file:line, module,
error kind, behavior, propagation terminus, logging, intent status with
basis).

### Phase 2: Normalization (mapping to categories)

1. Classify each item into the error category taxonomy
   (configuration / transient / invariant_violation / external_input /
   unclassified — never force-fit; `unclassified` keeps its judgment
   material).
2. Map each item to a disposition (fail-fast / propagate / translate /
   retry / degrade / swallow / log-only).
3. Build the category x disposition matrix: counts and representative
   examples per cell.
4. Present the majority disposition per category as the de-facto policy
   candidate — explicitly a candidate, not a verdict.

### Phase 3: Contradiction detection and coverage limits

1. For every same-category group with differing dispositions, record the
   contradiction schema: (a) involved pair/group, (b) each behavior,
   (c) whether placement or processing characteristics explain the
   difference (if explainable, note as possible conditional rule),
   (d) adjudication material a human decision would need.
2. Triage every DI-setup throw on the three axes: occurrence time,
   recovery responsibility, blast radius.
3. Write the coverage-limits section with at least: omission-policy
   non-exhaustiveness, dynamic exception paths (reflection, delegates),
   third-party library internal swallowing — plus any limits discovered
   during the run.
4. Generate the Markdown report using the template structure from
   `references/error_policy_report_template.md` or an equivalent structure.

## Monitoring and Control

- Treat every inventory bucket as recorded only when it has a state:
  `done`, `unknown`, or `not_applicable`; unrecorded buckets are leaks.
- Downgrade weakly supported category claims to `unclassified` and weakly
  supported intent claims to `inferred`.
- Separate observed behavior, inferred intent, and missing evidence.
- Preserve the evidence path for every non-trivial conclusion; when it came
  from a search, record the pattern so it can be re-verified.
- Route defect-level or security-scope discoveries to the handoff list
  instead of expanding scope mid-run.

## Unknowns And Risks

- Mirror every `unknown` bucket state that affects closure as an `unknown`
  concern with `python -m fm skill concern`.
- Record suspected defects or security gaps found during scanning as `risk`
  concerns pointing at the handoff list.
- Unknowns must be `resolved` and risks `resolved` or `escalated` before
  closure.

## Closure Gate

Closure is allowed only when all of the following hold:

- every inventory bucket has a recorded state
- the category x disposition matrix exists with counts and examples
- every contradiction entry carries (a)-(d) of the contradiction schema
- the coverage-limits section exists and contains at least the minimum set
- the search-pattern set actually used is recorded in the report
- the report exists at the declared output path
- defect-level and security-scope discoveries are on the handoff list
- the run log passes `python -m fm skill close`

## Handoff

- Hand the error-policy report to the requester and to the next phase —
  typically policy arbitration (human decision on contradictions),
  `design_flow`, or `dotnet_change_analysis` as a deepened
  error-handling-contract input.
- The contradiction list is decision input, not a defect list: arbitration
  of which disposition becomes the rule belongs to a human or to a design
  phase, never to this run.
- Suspected defects (async hangs, unobserved task failures as bugs,
  synchronization risks) hand off to `skills/csharp_review/meta.md`.
- Suspected security gaps hand off to `skills/security_review/meta.md`.
- Record each handoff as a `handoff` artifact in the run log.

## Rules

- Extract implemented behavior; never decide what the policy should be.
- Never fix code in this Skill.
- Distinguish `throw;` from `throw ex;` in every rethrow record.
- Never present the majority disposition as a verdict; it is a candidate.
- Never claim exhaustive coverage of omission policies.
- An explainable behavioral difference is a possible conditional rule, not
  a contradiction; record the explanation.
- The coverage-limits section is mandatory in every report, even when the
  scan found nothing else.
- Code comments are intent evidence, never proof.
- Use subagents only for scope-disjoint Phase 1 buckets; Phases 2 and 3
  run single-context.

## Failure Handling

- If solution or project boundaries cannot be resolved, continue and mark
  the affected buckets `unknown`.
- If external package source is unavailable, record the boundary-only
  visibility in coverage limits and continue.
- If the output path is not writable, return the content and intended path
  without deleting existing files.
