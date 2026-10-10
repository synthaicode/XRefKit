<!-- xid: D4B4C2657A63 -->
<a id="xid-D4B4C2657A63"></a>

# XRefKit Python Client Work Management Structure Findings

## Status, target and source basis

Current bounded source finding refreshed on 2026-10-11 through product implementation commit `3198070`. Target identity `E9A4C7B2106C` is `repository:XRefKit`, nine Python client-work runtime modules. Producer is instruction-backed source inspection under `skill_flow_authoring`, with `knowledge_ontology_management` authorized canonical extension. This is not a .NET source_structure_overview run or a claim of production acceptance. Checkout byte hashes below identify inspected source, including line endings rather than Git blob hashes. Unrelated Skill adoption/governance implementation is outside this finding.

## Runtime units and composition

| Unit | Current responsibility and pivots |
| --- | --- |
| `xrefkit/work_management.py` | Registered workspace/v2 plan validation, confinement, immutable definition per revision, observation/hash/history and counts; `register_workspace`, `record_plan`, `task_counts` |
| `xrefkit/plan_observation.py` | Legacy/v2 loading and exact run/repository/correlation mapping; `resolve_mapping` never invents runs or approval |
| `xrefkit/plan_markdown.py` | Derived owned adjacent Markdown/Mermaid, provenance, confined local links and optional explicit monitor; `render_body`, `publish_projection` |
| `xrefkit/azure_connection.py` | Immutable workspace profile, credential-name reference, operations/IDs and test probe; `validate_profile`, `register_connection`, `load_connection`, `read_check` |
| `xrefkit/azure_update_candidate.py` | Pure supplied-input reducer and escaped unsent preview; `build_candidate`, no profile/credential/network access |
| `xrefkit/azure_import.py` | Explicit-ID test GET capture, complete acquisition, immutable binding and baseline comparison; `capture`, `bind`, `_mapping`, `_plan` |
| `xrefkit/azure_writer.py` | One-shot guarded State/History delivery, durable intent/receipt, live checks, replay and explicit predecessor enforcement; `publish`, `_summary`, `_patch`, `_pairs` |
| `xrefkit/azure_recovery.py` | Local status, separate read-only full-proof confirmation and ancestry/eligibility; `inspect_status`, `reconcile`, `ancestry_before`, `eligible` |
| `xrefkit/dashboard.py` | Supplemental plan/workspace/run presentation; not an execution scheduler or approval authority |

Standard-library/local function composition supplies this subsystem. There is no DI container, database migration, queue consumer, automatic background synchronization or generic delivery plugin registry here. Primary plan review uses local JSON plus generated Markdown/Mermaid; dashboard/monitor URLs are supplemental.

## Route and data-flow traces

1. Workspace registration validates exact ID/root/session scope and repository confinement, locks the registry, refuses changed identity and atomically publishes hash-named JSON. Loaders separately confine fixed local paths; there is no global workspace fallback.
2. Plan recording validates v2 identity and expected observation revision, locks records, checks exact report replay and immutable definition, retains bounded observations and atomically publishes JSON. Owned Markdown projection is attempted under the lock with its own outcome; hand-authored/edited Markdown is preserved. Replay regenerates from current stored JSON, not an obsolete caller snapshot.
3. Counts project unique steps: explicit `done` without `revalidation_needed:true` counts completed. Runs/retries are not extra steps. Original/add/remove counts require `initial_task_ids`. PBI acceptance is separate. Mermaid uses safe node identities/labels and dependency edges with stage counts, source/run links and ordinary confined file links.
4. Profile registration is immutable local publication. Read profiles allow explicitly selected test IDs. Write profiles require exactly operations `read_work_item`, `update_task_state_history` and item set `{10,21}`. Production network operations are refused before credential/network work.
5. Read probe verifies bounded revision/type/state/project/identity through exact HTTPS API 7.1 endpoints. Capture additionally projects title, description, PBI acceptance criteria/priority, parent and safe URL data. PBI self-URL may establish project GUID; Task/self/parent identities must agree. Related URLs are not followed.
6. Capture makes one GET per selected ID. Partial results retain acquired observations; authentication rejection stops later reads. Exact capture replay uses no new credentials/network. Local binding requires a complete capture, every selected Task once, disjoint nonempty included steps, explicit approval references and completion criteria. It seals capture/plan hashes and identities without altering the plan or observations. Comparison capture selects an explicit binding, retaining baseline and recording changes/incomplete results for resolution.
7. Offline candidate validates supplied local plan/target/binding/baseline/remote/metadata and explicit authorization/completion assertions. State/escaped summary generation is deterministic. Candidate/hold/conflict/invalid remain unsent, not proof of fresh state or permission.
8. Writer resolves exact test profile/capture/mapping; target is hard-coded PBI10/Task21. It validates current definition against binding and current observation against the request (observation may advance beyond initial binding), saved records and explicit ancestry under plan/delivery locks. Intent-only/unknown sends block the target across other report/connection/binding IDs. Exact replay returns historical records before credential lookup/network. Fresh execution reads parent/Task/transition metadata and applies the pure reducer; completion/work/rework authority remains recorded assertion input.
9. Sealed durable intent precedes one PATCH: `test /rev`, optional State and one deterministic History. Matching response/fresh readback of revision, State, full summary, protected Task fields and parent checks establish success. Plan/import/binding/profiles are unchanged. Dispatch/persistence uncertainty is not retried; the intent remains evidence.
10. Recovery status reads local records only. Reconciliation checks parent/current Task/expected historical revision using bounded GETs and seals a separate result. Complete intended summary/State/protected-fields/target/parent proof is mandatory. Historical match with changed current projection yields `applied_remote_changed`, blocking resume. Absence or a marker alone never proves not-sent. Eligible current positive proof can be explicitly selected by a subsequent new report's `previous_reconciliation_id`, with newer local observation, single-successor/full ancestry and normal fresh writer validation. Reconciliation itself never sends or changes original records.

## Persistence, configuration and external boundaries

Fixed `work/plans` and `work/sessions` contain client definitions/observations/runs. Integration records reside in `work/integrations/connections`, `imports`, `bindings`, and `deliveries/{intents,receipts,reconciliations}` inside the selected workspace. Exclusive local locks, hashes, confinement, temporary sibling writes, fsync and atomic publication preserve complete snapshots. JSON records/responses are bounded at 1 MiB; selected Task sets and per-kind records at 200. No automatic purge or stale-lock deletion occurs; multi-host/shared-filesystem guarantees are not established.

PAT values never belong in profiles: only environment variable names are stored. Normal TLS, 30-second socket-operation timeout, no retries/redirects/automatic proxy fallback bound transport. This is not a whole-operation deadline. Diagnostics exclude raw authorization/server bodies. Imported HTML remains inert JSON rather than executable/displayed content or instructions.

Writer changes only State/History under revision checks, not assignee/description/deadline/estimate/links/PBI acceptance/Bug items. History contains artifact IDs/versions, not uploads, absolute paths, evidence reference strings or teammate access proof. Explicit test read/import selection is broader than hard-coded write/recovery scope; this implemented distinction is not a generic sync contract.

## Naming and contract surfaces

| Surface | Meaning |
| --- | --- |
| `workspace_id/connection_id/organization/project/item_id` | Exact local/remote identity; equal numeric IDs elsewhere are different targets |
| `plan_revision/observation_revision/report_id` | Definition revision, state sequence and immutable report identity |
| `import_id/binding_id` | Immutable acquisition and approved external/local mapping |
| `candidate/hold/conflict/invalid` | Offline decisions, not delivery results |
| `success/hold/conflict/rejected/unknown` | Distinct writer outcomes; success alone confirms delivery |
| `confirmed_applied/applied_remote_changed/unresolved/retained_non_success` | Proof dispositions, not automatic retry permission |
| `previous_report_id/previous_reconciliation_id` | Mutually exclusive explicit predecessor edges, never latest-file selection |
| `recorded_at/verified_at` | Original receipt processing-start time versus recovery verification time |
| `local_only` | Trace identity with accessibility unverified, not uploaded evidence |

## Verification and limits

This refresh inspects current source and CLI/schema behavior. Public examples are verified offline against implementation request validators. Prior product validation recorded 1,360 tests passed, four platform skips and 83 subtests, independent review and bounded live read/write/reconciliation proof. These are attributed prior observations, not a full-suite rerun by this source refresh or a real run of the new Skill against Azure.

Import/binding, scoped writer and read-only reconciliation are implemented. Outside scope/unverified: arbitrary write IDs, production connections, real network fault injection, multi-host locking, team-accessible artifact storage, background sync, deployment and security certification. Abnormal delivery/resume was exercised with isolated transports in prior tests; it is not a live Azure fault experiment. PBI acceptance is a separate human judgment.

## Planning use and validity

The finding supports operation selection and changes within the nine-module scope. The [operating model](../operations/160_azure_devops_client_work_integration.md#xid-C8E2A591D740) normalizes operational facts; this navigation link does not assert a semantic dependency. No relation is added merely from runtime reuse. Recheck hashes and behavior after source/schema/entry point/authentication/target guard/persistence/reducer changes. Unrelated governance changes alone do not establish source drift here.

## Sources

- source_type: repository_source
- source_revision: `3198070`
- source_path: nine runtime units above and corresponding tests
- source_locator: module pivots and data-flow traces above
- inspected_at: 2026-10-11

## Raw Working-Tree Source Hashes

These are checkout bytes including line endings, not Git blob hashes.

| Path | SHA256 |
| --- | --- |
| xrefkit/work_management.py | 8be833e80b80a72663688c67ccc0284942703656966863a87f14a7814313f80d |
| xrefkit/plan_observation.py | c72d306de61c779084c8a697c93f84f8992fcfb5fa3969313c79e157a6befab4 |
| xrefkit/plan_markdown.py | 6ddd5d9a58ce41bc94a23d1dafdb86f5225d093be849c3a04c9e78f2cbb049cb |
| xrefkit/azure_connection.py | f0cb3d2e0b7da626fb31e42dc086430dbe7f1fd018d0346785b22fa33545fb89 |
| xrefkit/azure_update_candidate.py | 2b091e236044370a150b01a2739c63fb194dc9c824f6e9bb9f11a264f087be01 |
| xrefkit/azure_import.py | 312358bb150ebcb1e1f5d99c747057c3acc92bd73709c75dc71dfc13bf6e6493 |
| xrefkit/azure_writer.py | 2deb7db8cf9e2574730b94ba08d5431330fc1ce3b49b46604ecb7ba522947097 |
| xrefkit/azure_recovery.py | 91c3050e9799b82d9023547fd2ee877ab8c12cbdc2c1d5e64efcb1f758483d80 |
| xrefkit/dashboard.py | e61e26d6906baa81392f70467932d96ecaf8cc0baf72077e44f6e1845de49503 |
