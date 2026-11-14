<!-- xid: 84C9D6A1E730 -->
<a id="xid-84C9D6A1E730"></a>

# Brownfield understanding changes and Project Management handoff

Use this procedure when requirements understanding, technical evidence, method
selection or migration scope changes. Technical investigation and verification
remain with their existing Skills; this procedure prepares their traced inputs
and receives their evidence. Project Management owns schedules and progress.

1. Reload the previous structured understanding revision and its exact evidence.
   Record current requirements, confirmations and approach with stable item IDs,
   requirement XIDs, owner, state, change reason, Evidence, judgment/decision and
   approval references. Preserve candidate, confirmed and observed states.
   Do not convert an observed implementation into an approved requirement.
2. Use `xrefkit_skills_brownfield.understanding` to validate explicit records and
   compare revisions. It detects added, changed and removed fields, including
   evidence, artifact revisions and approval records; it does not infer semantic
   changes from arbitrary prose. The investigator owns interpreting new facts.
3. Analyze each Knowledge Requirement: the question, applicable Knowledge query,
   what judgment needs it, available Knowledge/Evidence and applicability or
   freshness gaps. Explicit `satisfied` input needs both Knowledge and Evidence;
   the program does not judge their truth. Missing, stale or conflicting input
   remains a gap with owner, reason and required resolution point.
   Resolve existing Knowledge through the active provider's catalog/search and
   XID route, using the selected Skill's `knowledge_needs` query and seed XIDs.
   Record its exact version/location in `knowledge_refs` and applicability
   evidence in `evidence_refs`. Knowledge XIDs are distinct from requirement
   XIDs; finding a document alone does not establish sufficiency. Newly published
   or materially revised Knowledge follows its existing ontology/governance route.
4. For each open Knowledge Requirement, supply the permitted investigation or
   verification method, expected evidence and target method-decision reference.
   The helper derives proposed Decision activities only when these are explicit.
   Missing methods or expected evidence remain named planning gaps. Do not invent
   durations, dependencies, permission, acceptance or a method-selection decision.
5. Link requirement XIDs to versioned artifacts and phase outputs. Include changes
   in migration volume, compatibility, cutover/rollback assumptions and method
   choice where supported. Preserve old links in the previous revision, including
   withdrawn scope. Revalidation of changed artifacts remains with the quality owner.
6. Persist exact inputs and analysis with `save_analysis` or the CLI's explicit
   `--save` destination selected by confirmed project rules. Each revision is a
   separate create-only JSON file; identical retries are idempotent and different
   bytes at an existing revision are refused. File creation is not proof of upload
   or shared visibility. Correct errors with a new revision.
7. Deliver the `brownfield.change_impact/v1` notification to the configured PM
   route. Its stable ID, previous/current revision, three-section changes,
   reason, requirement XIDs, Evidence, decisions, approvals, affected task IDs,
   proposed Decision activities and open Holds preserve causality. PM validates
   this receiver-owned contract and reports direct/dependent impact. It alone
   owns CPM, Mermaid, schedule Revision files and baselines. Notification is not
   plan approval or permission to start work; an unchanged schedule stays intact.
8. For missing PM integration, save the notification and name the receiving
   owner/action. Do not silently discard impact or duplicate scheduling logic.

## Standard user-facing output

Use exactly `要求事項`, `確認事項`, `進め方` as the top-level sections, as explicitly
requested for this workflow. Put status/result, evidence, open items and handoff
content within these sections; this output choice does not amend the shared
reporting or uncertainty contracts. Every item retains change reason and basis.

- 要求事項: current purpose/scope/acceptance and requirement-understanding changes,
  versioned artifact trace, candidate/confirmed status and responsible decisions.
- 確認事項: unanswered questions, Knowledge Requirements, conflicting/stale evidence,
  Holds, affected scope, resolver and needed decision or verification evidence.
- 進め方: proposed investigation/verification, method-selection prerequisites,
  PM impact notification and the next owner/action; approved execution remains
  distinct from a proposal. Preserve all phase/closure gates and detailed evidence.

## Executable input and limits

The package README specifies `brownfield.understanding/v1` JSON and the CLI.
Use real project evidence; examples are synthetic. JSON is the helper's source,
not a mandate to replace a project's approved storage or attachment mechanism.
The helper neither searches Knowledge nor performs tests, approves requirements,
selects a migration method, schedules resources or certifies business readiness.
Those actions remain with the applicable existing methods and responsible people.
