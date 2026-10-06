---
schema_version: 1
skill_id: csharp_error_policy_extraction
xid: F2B8D5A1C370
summary: extract the implemented C# error policy as evidence, dispositions, contradictions, and explicit coverage limits
applies_when:
- user needs the implemented error policy of a C# codebase made explicit before changing error handling, unifying conventions, or arbitrating inconsistent failure behavior — a deep-dive of the error-handling-contract viewpoint of `dotnet_change_analysis`, not a defect review
exclusions:
- do not decide what the policy should be, produce defect findings, or perform vulnerability assessment
- do not claim exhaustive coverage of omission policies or third-party internals
inputs:
- target path (repository, solution, or project), optional scope filters, optional existing change-analysis note from `dotnet_change_analysis`, optional output path
outputs:
- Markdown error-policy report containing the error-handling inventory with per-item record schema, category x disposition matrix with de-facto policy candidates, contradiction list with adjudication material, DI startup-throw triage, and a mandatory coverage-limits section
criteria:
- id: inventory_coverage
  statement: Every in-scope inventory bucket has state done, unknown, or not_applicable and each item has file:line evidence.
  verification: Compare the bucket ledger and report records with the declared scope and search-pattern set.
- id: policy_extraction
  statement: Categories, dispositions, majority candidates, contradictions, and DI startup-throw triage remain evidence-based and non-prescriptive.
  verification: Inspect representative examples, contradiction fields, and explicit candidate wording.
- id: coverage_limits
  statement: The report records omission-policy non-exhaustiveness, dynamic exception paths, and third-party swallowing limits.
  verification: Check the mandatory coverage-limits section and any additional discovered limits.
- id: extraction_only_handoff
  statement: Defect-level and security-scope discoveries are handed off and no source fix is performed.
  verification: Inspect the handoff list and changed targets for extraction-only scope.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: csharp_error_policy_detection_patterns
  query: CSharp error policy detection patterns
  required_when: Required before scanning error handling or omission policies.
  seed_xids:
  - C0DBC37E2A13
- id: common_source_analysis_criteria
  query: common source analysis criteria
  required_when: Required to classify source evidence and coverage.
  seed_xids:
  - 5F21C8A41001
- id: dotnet_change_analysis_viewpoints
  query: dotnet change analysis viewpoints
  required_when: Required when using the change-analysis error-handling viewpoint as context.
  seed_xids:
  - 2E7B5A1FD201
control_refs: []
aliases:
- FE342FB520D0
- B150A2A54169
---
<!-- xid: F2B8D5A1C370 -->
<a id="xid-F2B8D5A1C370"></a>

# C# Error Policy Extraction

Extract policy as implemented. Produce an inventory, category by disposition
matrix with de-facto policy candidates, contradiction list with adjudication
material, DI startup-throw triage, search-pattern record, explicit coverage
limits, and handoffs. This deepens the error-handling-contract viewpoint of
`dotnet_change_analysis`.

## Method

1. Confirm the target and scope. Check for a prior `dotnet_change_analysis`
   note and use only its error-handling-contract and structure sections as
   seed input. Resolve the detection-pattern Knowledge before scanning.
2. Declare the search patterns, then scan all throw sites (distinguishing
   `throw;` from `throw ex;` and `ExceptionDispatchInfo`), catch blocks by kind,
   custom exception hierarchies, global handlers, async void, fire-and-forget,
   sync-over-async, DI composition-root throws, options validation, hosted
   service startup, and Dispose/DisposeAsync handling.
3. Scan omission policies such as null returns, `Try*`, default/empty
   fallbacks, and bool-only success flags within the detected range. Record
   each item with file:line, module, kind, behavior, propagation terminus,
   logging, intent status, and basis.
4. Classify items as configuration, transient, invariant_violation,
   external_input, or `unclassified`, retaining judgment material when weak.
   Map dispositions to fail-fast, propagate, translate, retry, degrade,
   swallow, or log-only. Build counts and representative examples, then state
   the majority per category as a candidate, never a verdict.
5. For differing same-category dispositions, record the involved group,
   behavior, whether placement or processing explains the difference, and the
   adjudication evidence a human needs. Triage DI setup throws by occurrence
   time, recovery responsibility, and blast radius.
6. Write coverage limits covering omission-policy non-exhaustiveness, dynamic
   reflection/delegate paths, third-party library swallowing, and every new
   limit found. Record weak intent as `inferred`, missing evidence as
   `unknown`, and route defects or security gaps to the appropriate Skill.

## Stop and handoff

If project boundaries cannot be resolved, continue only with affected buckets
marked `unknown`. If package source is unavailable, record boundary-only
visibility. Never fix code or turn comments claiming intent into proof. The
contradiction list is decision input; a human or design phase arbitrates the
policy. Handoff the report to policy arbitration, `design_flow`, or
`dotnet_change_analysis`; suspected defects go to `csharp_review` and security
gaps to `security_review`. Closure requires every bucket state, matrix,
contradiction schema, mandatory limits, declared search patterns, report path,
and handoff list.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

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

- [Error policy report template](references/error_policy_report_template.md#xid-8A6A9B1C3223)

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
  `knowledge/source_analysis/130_csharp_error_policy_detection_patterns.md#xid-C0DBC37E2A13`,
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
  concern with `python -m xrefkit skill concern`.
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
- the run log passes `python -m xrefkit skill close`

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

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: extract the existing de-facto error policy from C# source as an inventory, a category-by-disposition matrix, detected contradictions, and explicit coverage limits

- use_when: user needs the implemented error policy of a C# codebase made explicit before changing error handling, unifying conventions, or arbitrating inconsistent failure behavior — a deep-dive of the error-handling-contract viewpoint of `dotnet_change_analysis`, not a defect review

- input: target path (repository, solution, or project), optional scope filters, optional existing change-analysis note from `dotnet_change_analysis`, optional output path

- output: Markdown error-policy report containing the error-handling inventory with per-item record schema, category x disposition matrix with de-facto policy candidates, contradiction list with adjudication material, DI startup-throw triage, and a mandatory coverage-limits section

- constraints: extraction only — record implemented behavior, never decide what the policy should be; do not fix code; never claim exhaustive coverage of omission policies; every non-trivial conclusion carries an evidence path; defect-level findings (async hangs, race conditions) hand off to csharp_review and vulnerability findings hand off to security_review; the coverage-limits section is mandatory in every report

- lifecycle:
  - startup: confirm target path, scope, output path, and whether a prior change-analysis note exists as input
  - planning: define scan scope, split inventory buckets (explicit handling, dotnet-specific paths, omission policies, global handlers), and declare the search-pattern set
  - execution: run Phase 1 inventory extraction, Phase 2 normalization into the category x disposition matrix, and Phase 3 contradiction detection with coverage limits, recording evidence paths throughout
  - monitoring_and_control: downgrade weakly supported classifications to `unclassified` or intent `inferred`; treat unrecorded buckets as leaks; keep detection limits explicit instead of claiming completeness
  - closure: return the error-policy report, the de-facto policy candidates, the contradiction list, unresolved unknowns with reasons, and the handoff list

- tags: `dotnet`, `csharp`, `analysis`, `error-handling`, `policy-extraction`, `markdown`

- knowledge_slots:
  - name=common_source_analysis_criteria; bind=5F21C8A41001
  - name=dotnet_change_analysis_viewpoints; bind=2E7B5A1FD201
  - name=csharp_error_policy_detection_patterns; bind=C0DBC37E2A13

- observation_refs:
  - `../../observations/2026-06-12_skill_run_skill_flow_authoring.md`
  - `../../observations/2026-06-12_skill_run_csharp_error_policy_extraction.md`
  - `../../observations/2026-06-12_error_policy_report_mailkit_pooling.md`
