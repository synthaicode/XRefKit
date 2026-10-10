---
schema_version: 1
skill_id: local_work_management
xid: E7C4A916B280
summary: persist approved local plans, generate Markdown and Mermaid, and record evidence-backed observations independently of remote services
applies_when:
- a user needs local client work planning records, plan views, or execution observations without requiring an external work tracker
exclusions:
- business acceptance decisions, inferred completion from logs, automatic execution, remote operations, and modification of immutable plan definitions within a revision
inputs:
- approved work breakdown and source, selected root and workspace, explicit plan and report identities, expected observation revision, and recorded status and evidence
outputs:
- registered workspace, authoritative plan JSON, derived Markdown and Mermaid, preserved observation history, evidence references, and explicit remaining judgments
criteria:
- id: work_package_assignment
  statement: Approved work packages share one purpose and result; each task belongs to exactly one package, counts use tasks only, and package verification remains distinct from task completion.
  verification: Inspect the approved source table, task membership and both completion indicators; reject unsupported structured package fields.
- id: local_independence
  statement: Local registration, recording, rendering and completion verification require no Azure connection, PAT, browser or monitor.
  verification: Execute the local-only fixture and inspect imports and generated output.
- id: recorded_truth
  statement: Work status, revalidation, confirmation application and business acceptance remain distinct recorded facts.
  verification: Compare source evidence, submitted observations and displayed counts.
- id: immutable_identity
  statement: Definitions stay immutable within a plan revision and observation updates retain history using explicit expected revisions.
  verification: Inspect identities, update results and historical snapshots.
- id: projection_boundary
  statement: Saved JSON and generated projection outcomes are checked separately.
  verification: Inspect saved/replayed fields and projection status, then inspect the generated file.
knowledge_needs:
- id: local_operating_model
  query: XRefKit local client work management plan persistence Markdown Mermaid observations
  required_when: Required before local registration, recording or rendering.
  seed_xids:
  - F3A8D602C951
control_refs: []
---
<!-- xid: E7C4A916B280 -->
<a id="xid-E7C4A916B280"></a>

# Skill: local_work_management

## Startup and preparation

Use the repository runtime envelope and operating contract. Load the
[local operating model](../../../knowledge/operations/161_local_client_work_management.md#xid-F3A8D602C951).
Identify the root, registered workspace and exact plan/revision. For work
breakdown from approved requirements, route to
[planning_flow](../../planning_flow/SKILL.v1.md#xid-6A4F8C2D1E71)
under its own governance; this Skill persists that approved output and does not
replace planning or approve scope. Existing approved breakdown is also valid input.
Record missing approvals or evidence explicitly rather than generating them.
Prepare concrete work items and local evidence links. Before submission, group
the approved tasks by purpose and result using the operating model work-package
definition. Record package ID, title, purpose, output, task IDs, completion
criterion, dependencies and confirmation owner in a separate local approved
breakdown Markdown. Verify unique package IDs, exactly one membership per task
and complete coverage of the approved task set. Record missing decisions explicitly.
Use that breakdown as the plan `source`; if other approved sources exist, link
them from the breakdown instead of discarding them. Changing an existing plan
source requires a new plan revision because source is an immutable definition.
Adapt the
[inert examples](references/local_examples.md#xid-D6B2E491F730)
to the selected root; examples are not authorization or completion evidence.

## Execution

1. Register the selected portable workspace with
   `python -m xrefkit.work_management register --root ROOT --input WORKSPACE.json`.
   Verify returned identity and saved/replayed outcome; do not replace an existing
   identity with changed content.
2. Prepare a schema-v2 submission from approved breakdown: stages, uniquely
   identified steps and dependencies, local PBIs and completion conditions,
   source/baseline/candidate versions and evidence references. External references
   may be empty. New work definitions require a new explicit plan revision;
   preserve predecessor linkage instead of rewriting existing topology.
   Schema v2 has no work-package field: do not add unsupported fields or rename
   stages as packages. Keep package definitions in the approved source Markdown.
   A supplemental authored PBI -> package -> Task Mermaid can accompany that
   source; it is not an automatically generated or authoritative status view.
3. Record the initial plan with
   `python -m xrefkit.work_management record --root ROOT --input PLAN.json --expected-observation-revision 0`.
   For observations, read the current stored revision and use that exact expected
   value. Supply a new report ID and recorded timestamp for a new observation;
   preserve unchanged definition fields and omit writer-managed hash/history/revision
   fields from the submission.
4. Inspect saved/replayed and projection status separately. JSON can be saved
   before projection fails; a nonzero CLI result is not proof that saving failed.
   Read the returned stored JSON path before deciding another action. Exact replay
   retains history and projects the current stored snapshot rather than rolling back.
5. Inspect adjacent generated Markdown: total/completed/remaining counts, stage
   rows, dependency Mermaid, selected step evidence and confirmation links.
   To regenerate only the projection, use
   `python -m xrefkit.work_management render --root ROOT --input STORED_PLAN.json`.
   This calls `plan_markdown.regenerate`; use stored JSON, not an unsaved submission.
   View Markdown/Mermaid in a compatible local client or VS Code. Monitor links
   require explicit optional `--monitor-base`; omit it for local-only operation.
6. Record execution observations from actual evidence: step status and
   status_evidence, exact run references, artifact versions, validation records,
   concerns and judgment references. The recorder does not ingest client logs,
   execute work, infer completion or make approval decisions automatically.
7. For a discovered impact, preserve prior completion evidence, explicitly mark
   revalidation and affected versions, and record the confirming test result.
   If topology or completion conditions change, create a new plan revision.
   Track confirmation answer and its application independently; keep judgment
   history separate from the current design decision.

## Monitoring, completion and handoff

Stop for unknown workspace/identity, stale observation revision, changed
same-ID reports, invalid dependency/schema, definition conflicts or missing
completion evidence. Inspect counts as step counts, not effort, duration or
business acceptance. A completed step needing revalidation remains in remaining;
missing evidence alone does not rewrite recorded status.

Before completion, verify package membership against the saved task IDs and
report task completion counts separately from package completion verification.
All member tasks done does not establish the package criterion or PBI acceptance.
Read the supplemental source independently; the generated Markdown remains
stage-based and does not currently project packages. Hand off structured package
persistence and automatic package projection as implementation gaps when required.

Before completion, verify stored JSON, current projection, preserved history
and explicit unresolved confirmations/revalidation. Record paths, identities,
outcomes, limitations and next owner in the run/session records; use normal
runtime verification and closure. Local work management can complete without
Azure/PAT/monitor. Business acceptance stays with its designated human owner.

Only when separately requested/authorized, hand exact local identities and
recorded evidence to
[azure_work_item_integration](../azure_work_item_integration/SKILL.v1.md#xid-A19E6D4C82B7).
A connection's existence never triggers synchronization. Azure operation outcomes
are integration records; local observations remain the local source of truth.
Public placement does not imply adoption, maturity promotion or MCP distribution.
