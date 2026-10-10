<!-- xid: D4B4C2657A63 -->
<a id="xid-D4B4C2657A63"></a>

# XRefKit Python Client Work Management Structure Findings

## Status and Identity

Current source finding independently accepted for the explicit bounded target below. This is instruction-backed analysis, not a source_structure_overview Skill run. Workflow e3f78188-2448-4ca0-9d39-736a73ebe3e7 records fallback because that Skill's applicability is .NET-only. Common source criteria5F21C8A41001 applied. Producer: instruction-backed source analysis; normalization/registration: source_structure_findings_registration (authorized apply).

Repository: XRefKit, local C:/dev/itsm/XRefKit. Inspected source basis commit f83bf70d2b9da37e1833bf5e8c1d86684cfd6df7 (checkpoint commits do not alter these modules). Target scope: xrefkit/work_management.py, plan_observation.py, plan_markdown.py, azure_connection.py, azure_update_candidate.py and dashboard.py's plan/workspace loading. Tests: corresponding work_management, plan_observation, plan_markdown, azure_connection, azure_update_candidate and dashboard tests. Governance adoption modules under concurrent implementation are explicitly separate from this source finding; they are not Azure importer/writer structure. Raw working-tree byte hashes (including checkout line endings, not Git blob hashes) accompany this report in python-client-work-source-basis.json.

## Purpose and Runtime Units

| Unit | Current responsibility and source pivots |
|---|---|
| work_management | Validates registered workspace and v2 plans; confined JSON persistence, revision/hash/history, immutable definition within revision, task count projection. validate_plan_v2, record_plan, register_workspace, task_counts are main pivots. |
| plan_observation | Legacy/v2 plan loading and exact run mapping; presentation does not invent runs/status. resolve_mapping checks repository, unique run_id and optional flow/work_item/node correlation. |
| plan_markdown | Derived adjacent Markdown with Mermaid, source provenance, ordinary confined local links and optional explicitly supplied monitor base. render_body and publish_projection separate content from owned atomic publication. |
| azure_connection | Workspace-scoped immutable connection profile registration, exact loader and explicit test-only GET read_check. PAT env-name reference only; current allowed operation read_work_item and explicit IDs. |
| azure_update_candidate | Pure bounded supplied-input validation and state reducer producing unsent candidate/hold/conflict/invalid and constrained patch preview. No transport, profile access or credential lookup. |
| dashboard | Supplemental plan/run UI. Imports plan_observation and work_management; loads registered workspace-specific plans/run records and renders plan panel. It does not make completion/approval decisions. |

Each persistence/transport module exposes a module CLI main. There is no new dependency injection container, job scheduler, queue consumer, database migration or background synchronization in this bounded subsystem. Python standard library and local functions compose these paths directly.

## Route and Data-Flow Traces

1. Workspace registration validates exact ID/workspace_root and session-scope overlap, confines root inside repository; writer/loader separately confine fixed work/plans and work/sessions, takes .registry.lock, refuses changed same-ID registration and atomically writes hash-named JSON under work/workspaces.
2. Plan recording validates submitted v2, resolves exact workspace/directory and identity, takes .records.lock, checks report replay and expected observation revision, rejects same-plan-revision topology mutation, retains bounded prior observations, atomically replaces JSON and attempts owned Markdown projection under the same lock. JSON save and Markdown projection outcome are separate. A replay regenerates from the stored current snapshot rather than replaying an older observation.
3. Task counts count unique steps. Completed means explicit done and revalidation_needed is not true. Retries are runs, not added tasks. Unknown initial_task_ids leaves original/add/remove counts unrecorded. PBI acceptance is a separate record.
4. Markdown generation emits fixed generated ownership receipt/body hash, safe Mermaid node identities/labels, readable stage/dependency tables and source/run links. Existing hand-authored or edited generated Markdown is preserved with projection failure. Source JSON remains authoritative; manual regeneration uses the same lock/current reread. Optional monitor URLs are supplemental and explicitly supplied, not a guessed localhost service.
5. Azure profile register_connection validates strict target/auth-reference/scope, resolves workspace directory, locks .connections.lock, treats identical registration as replay and changed identity as conflict. load_connection refuses missing/duplicate identity. It performs no request.
6. Azure read_check validates exact allowed test item before env lookup; resolves named PAT, builds HTTPS dev.azure.com project/item endpoint, makes one GET7.1 selecting TeamProject/WorkItemType/State with redirect/proxy fallback disabled and bounded response. Validates response destination/project/item/revision and sanitized fields, returns read outcome only. No PBI description/criteria/relations import or local plan binding occurs.
7. build_candidate accepts stored local plan plus exact target/binding/captured baseline/remote/metadata and explicit criterion/authorization assertions. It checks revisions, conflict and ordered states, emits deterministic escaped summary and at most test /rev plus State/History preview. Results always not_sent/publish_ready=false; local artifact IDs/versions are local_only with accessibility unverified.

## Persistence, Configuration and External Boundaries

Workspace JSON defines workspace_root; writer/loader derive fixed work/plans and work/sessions; repository_root and workspace identity constrain reads/writes. No global workspace fallback. Local JSON schemas and explicit versions are extension boundaries. plan_revision is definition identity; observation_revision is state sequence; report_id/hash handles local idempotency. _publish uses temporary sibling file, fsync and os.replace. Locks use exclusive file creation, with failure rather than optimistic parallel writes; distributed lock/remote filesystem guarantees are not established.

Profile files contain PAT environment variable name, never a stored PAT. Current read probe only permits test; production flag is representable but refused before token lookup. HTTP errors are bounded diagnostic codes, not raw server content or inferred root causes. Generic API adapters/importer/write operations do not exist in these modules. Offline candidate captured snapshots do not prove current remote/local state or effective permission.

No ORM/data store, tenant router or plugin registry is used here. Variation comes from registered workspace, exact connection/project/environment/item allowlist, plan versions/statuses/dependency kinds and optional monitor base. Dashboard/run matching is an observation boundary, not an execution scheduler.

## Naming and Contract Surfaces

| Surface | Meaning retained |
|---|---|
| workspace_id/connection_id/organization/project/item_id | Exact local/external identity; same numeric external ID elsewhere is distinct |
| plan_id/plan_revision/step_id/observation_revision/report_id | Definition, stable task, state sequence and report identity; do not conflate |
| candidate/hold/conflict/invalid | Offline decision outcomes, not delivery results |
| not_sent/read_verified/write_permission_verified | Separate transport/observation/authority facts |
| completion.confirmed/work_authorization refs | Supplied assertions consumed deterministically, not evaluated as business approval |
| artifact_id/version/local_only | Safe trace reference, not public URL or teammate accessibility |

Public CLI/API names and schema enums are contract surfaces. Existing report/run IDs, revision fields and safe-path rules must be preserved by future import/write work unless an explicit migration is designed.

## Existing Verification and Limits

The independently reviewed prior implementation evidence records 95 focused tests passed,3 platform skips,81 subtests for candidate/read/Markdown/work-management/observation/dashboard. Parent's actual synthetic CLI proof covers deterministic replay, source immutability, criterion hold, remote revision conflict and local-only artifact preview. This analysis did not rerun tests, call Azure, measure performance or certify transport writes. Read source confirms mechanics; those attributed tests support only their reported cases.

Unresolved verification: actual Task19 import and binding are absent; Task21 writer, live local/remote reread, permission verification, send idempotency/reconciliation and Task22 fault recovery are absent. Test-profile expansion requires explicit new target scope. Team-accessible artifact storage is not assumed; chosen policy is local-first. Windows symlink tests have platform skips. Full multi-host/shared-filesystem locking, production runtime, security assessment and deployment are outside this finding, not passed.

## Knowledge Relations

No semantic relation is asserted beyond the bounded target identity. Common source criteria are methodology, not an inferred domain dependency.

## Planning Use and Validity

This finding supports PBI10 remaining importer/writer/recovery/acceptance planning. It states current extension points and missing capabilities; it does not decide new implementation architecture or authorize writes. Recheck whenever listed source files/schema/entry points or authentication/persistence boundaries change. Changes only to unrelated governance modules do not by themselves invalidate this bounded finding, but actual source hashes must still be matched at planning time.


## Raw Working-Tree Source Hashes

These are checkout bytes including line endings, not Git blob digests.

| Path | SHA256 |
|---|---|
| xrefkit/work_management.py | 8be833e80b80a72663688c67ccc0284942703656966863a87f14a7814313f80d |
| xrefkit/plan_observation.py | c72d306de61c779084c8a697c93f84f8992fcfb5fa3969313c79e157a6befab4 |
| xrefkit/plan_markdown.py | 6ddd5d9a58ce41bc94a23d1dafdb86f5225d093be849c3a04c9e78f2cbb049cb |
| xrefkit/azure_connection.py | f0d34240fbfc6ab91e132fe3a1632680d24161c77dc298c781309744e97ba9f6 |
| xrefkit/azure_update_candidate.py | 2b091e236044370a150b01a2739c63fb194dc9c824f6e9bb9f11a264f087be01 |
| xrefkit/dashboard.py | e61e26d6906baa81392f70467932d96ecaf8cc0baf72077e44f6e1845de49503 |
