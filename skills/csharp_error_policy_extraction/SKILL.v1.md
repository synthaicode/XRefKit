---
schema_version: 1
skill_id: csharp_error_policy_extraction
xid: F2B8D5A1C370
aliases: [FE342FB520D0, B150A2A54169]
summary: extract the implemented C# error policy as evidence, dispositions, contradictions, and explicit coverage limits
applies_when:
  - a C# or .NET source scope needs its de-facto error handling policy extracted without judging or fixing it
exclusions:
  - do not decide what the policy should be, produce defect findings, or perform vulnerability assessment
  - do not claim exhaustive coverage of omission policies or third-party internals
inputs:
  - repository, solution, project, or target path
  - optional scope filters, prior change-analysis note, and report output path
outputs:
  - inventory, category by disposition matrix, policy candidates, contradiction and adjudication material, DI triage, search patterns, coverage limits, and handoff list
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
knowledge_needs:
  - id: csharp_error_policy_detection_patterns
    query: CSharp error policy detection patterns
    required_when: Required before scanning error handling or omission policies.
    seed_xids: [C0DBC37E2A13]
  - id: common_source_analysis_criteria
    query: common source analysis criteria
    required_when: Required to classify source evidence and coverage.
    seed_xids: [5F21C8A41001]
  - id: dotnet_change_analysis_viewpoints
    query: dotnet change analysis viewpoints
    required_when: Required when using the change-analysis error-handling viewpoint as context.
    seed_xids: [2E7B5A1FD201]
control_refs: []
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
