<!-- xid: C8E2A591D740 -->
<a id="xid-C8E2A591D740"></a>

# XRefKit Azure DevOps Client Work Integration Operating Model

## Applicability and source authority

This fragment describes the XRefKit implementation inspected on 2026-10-11,
through import, delivery and reconciliation. Its scope is Azure DevOps Services
**test** connections, local client workspaces and explicitly selected work
items. It is implementation-specific Knowledge, not a universal Azure Boards
process specification. The operation method belongs to
[azure_work_item_integration](../../skills/os/azure_work_item_integration/SKILL.v1.md#xid-A19E6D4C82B7).
Public repository content does not authorize operations against a project.

## Local-primary boundary

[Local client work management](161_local_client_work_management.md#xid-F3A8D602C951)
owns local plan persistence, projections and observations independently. Azure
operations are optional, explicitly authorized adapter operations. Connection
availability is not an instruction to synchronize. Local completion does not
require a profile, PAT, remote read/write or monitor.

## Ownership and identities

Shared MCP distributes stable procedures and domain context. The client owns
planning, execution and results in its selected registered workspace. Azure
Boards receives the permitted team-facing Task state and deterministic result
summary. PBI business acceptance remains separate from local step completion.

| Identity | Meaning |
| --- | --- |
| `workspace_id` / `connection_id` | Exact client-work boundary and selected immutable profile; no global or latest-profile fallback |
| `organization` / `project` / item ID | Exact remote identity; equal numeric IDs in another project are different targets |
| `plan_id` / `plan_revision` | Work definition identity; topology and completion criteria stay immutable within the revision |
| `observation_revision` | Local state sequence, checked explicitly against the current stored plan |
| `import_id` / `binding_id` | Immutable capture and approved external-to-local mapping |
| `report_id` / `reconciliation_id` | Immutable delivery request and separate read-only result-confirmation request |

Profiles contain only `auth.kind: pat_env` and the environment variable name.
Credentials are obtained from the named process environment after scope checks;
there is no PAT argument, credential-file discovery or browser authentication.
A changed same-ID profile is refused; identical registration is local replay.
Read success proves the selected read at its recorded time, not write authority.

## Actual support and limits

| Operation | Implemented boundary |
| --- | --- |
| Registration/read probe | Exact workspace profile and explicitly allowed item ID; network probe refuses production |
| Capture/bind/comparison | Explicit positive PBI and Task IDs selected in a test profile; PBI type, Task type and parent relationships validated; no all-project enumeration |
| Offline update candidate | Pure supplied-input reducer; no profile, credential or network access; always unsent |
| Task writer | Hard-coded parent **PBI 10** and **Task 21**; test profile operations must be exactly `read_work_item` and `update_task_state_history`, item allowlist exactly `{10,21}` |
| Delivery status/reconciliation | The same PBI 10 / Task 21 guarded delivery; status reads local records only, reconciliation performs bounded GETs only |

Organization/project/workspace can vary in explicit configuration. This does
**not** make delivery generic across arbitrary item IDs. Production delivery,
arbitrary Task writes, background synchronization, PBI acceptance, conflict
overwrite, Bug/project creation and artifact upload are not implemented by
these modules. A profile schema can represent a production read profile, but
current network operations reject it. No test result proves production use.

## Capture and immutable binding

`azure_import.capture` makes one GET for each explicitly selected ID, beginning
with the PBI. It projects verified identity, type, revision, state, title,
description, acceptance criteria, PBI priority, parent, and safe relation data.
Description/criteria HTML remains an untrusted stored string; it is not executed
or rendered. The validated PBI self-URL may anchor the project GUID; Task and
parent URLs must match it. Related URLs are checked without being followed.

Partial acquisitions preserve successful observations and failure diagnostics.
An authentication rejection stops later reads; a partial/failed capture cannot
be bound. Exact same-ID/same-input replay returns saved acquisition with no new
credential lookup or network; fresh acquisition needs a new explicit ID.

`bind` is local-only. Every selected Task appears once in `mapping`, with
nonempty disjoint `included_step_ids`, explicit `completion_criterion` and
`approval_refs`. It seals capture hash, exact external identities/revisions,
plan definition/snapshot hashes and observation revision. It does not modify
plan JSON, Markdown, approval or status. Capture and bind are distinct commits
of local records, not an atomic two-operation transaction.

A comparison capture uses an explicit `comparison_binding_id` and current
`expected_observation_revision`. It preserves the original baseline and records
changes; incomplete or changed results require resolution. Recency or filename
order never chooses the baseline.

## Deterministic delivery

State selection and History construction use explicit local status,
revalidation, completion/work-authorization assertions, captured baseline and
fresh remote metadata. They do not invoke an LLM. Assertion evidence still
requires the authorized executor's judgment: the reducer does not independently
prove business truth or human approval.

The writer rereads the stored plan, parent, Task and Task state-transition
metadata. Current remote state/revision must match the explicitly selected
baseline. The plan definition must match the binding, while the observation
must match the request's current expected revision and may advance beyond the
original bound observation. Done needs
all mapped steps completed, no unresolved revalidation, and explicit external
completion confirmation. In-progress reflection needs active work authority;
reopening Done needs explicit rework authority. Missing metadata, stale state
or unsupported transitions cause hold/conflict rather than guessed updates.

The only PATCH operations are `test /rev`, optional `add
/fields/System.State`, and one `add /fields/System.History`. History contains
escaped report ID, plan/observation identity, ordered mapped steps/status and
optional sorted local artifact IDs/versions. It excludes artifact contents,
absolute paths, evidence reference strings and arbitrary user prose. No
assignee, description, deadline, estimate, links or PBI acceptance is written.

A durable intent is sealed before a single PATCH. Success requires matching
response and fresh readback of revision, state, exact History, protected Task
fields and parent checks. `success` alone has `sent_confirmed: true`;
`hold`, `conflict`, `rejected` and `unknown` remain distinct. A receipt's
`recorded_at` is initialized at processing start and is not a verification time.
`network_attempted`, `remote_write_attempted` and `possibly_sent` are separate.

Exact report/input replay returns stored results without network. Altered input
under the same report ID is refused. Intent-only or unknown sends block other
reports against the same target, including through other connections/bindings.
Known successful successors use an explicit `previous_report_id`, the same
binding/target and newer local observation. Single-successor and ancestry checks
prevent duplicated observations or branching chains. Recency never chooses a
predecessor, and no automatic retry occurs.

## Read-only reconciliation and bounded resume

`status` inspects stored intent/receipt/reconciliation/ancestry and reports local
guidance without credential lookup or network. `reconcile` preserves original
records and reads the parent, current Task, and the specific expected applied
revision when necessary. It never PATCHes. Its request's
`source_connection_id` is the original **write** profile; in writer requests
that field is the original **import/read** profile.

Full positive proof requires exact applied revision, intended State, complete
History digest, protected fields, target and parent. A marker alone, missing
history or absence in current state does not prove not-sent. Matching historical
proof with changed current projection gives `applied_remote_changed`; it blocks
resume. Matching full current proof gives `confirmed_applied`. Missing proof
remains `unresolved`. Existing `hold/conflict/rejected` dispositions remain
`retained_non_success`; they are not converted to success by recovery.

Saved `resume_ready` is the assessment at confirmation time. Local status
recomputes eligibility against known descendants and other unresolved reports.
Only an eligible proof of an uncertain original delivery permits a subsequent
new report with `previous_reconciliation_id`, newer local observation, normal
fresh publish checks and no competing unresolved target. It is mutually
exclusive with `previous_report_id`. Reconciliation is not a resend; confirmed
absence-based retry is not implemented. Locks and original records are never
automatically erased. Reconciliation `verified_at` is distinct from original
receipt `recorded_at`.

## Local persistence and sharing

Within the selected registered workspace:

| Path | Responsibility |
| --- | --- |
| `work/plans/` | Authoritative plan JSON and derived owned Markdown/Mermaid |
| `work/sessions/` | Client execution records |
| `work/integrations/connections/` | Immutable credential-name-only profiles |
| `work/integrations/imports/` / `bindings/` | Immutable acquisition and mapping evidence |
| `work/integrations/deliveries/intents/` / `receipts/` | Durable dispatch intention and outcome |
| `work/integrations/deliveries/reconciliations/` | Separate positive-proof confirmation records |

Records use bounded JSON, confinement, exclusive locks, hashes and atomic
sibling replacement/publication. JSON records/responses are bounded at 1 MiB;
selected Task sets and per-kind records at 200. No automatic purge occurs.
Shared-filesystem/multi-host locking guarantees are not established.

HTTPS API 7.1 uses normal TLS, 30-second socket-operation timeout, bounded
responses, no retries, redirects or automatic proxy fallback. This timeout is
not an end-to-end deadline. Errors use bounded diagnostic codes, not raw
authorization headers/server bodies. Artifacts remain local-first: IDs/versions
in Azure History are references, not proof that teammates can open local files.
Human judgment owns PBI acceptance, conflict resolution and new Bug registration.

## Sources and validity

- source_type: repository_source
- source_revision: `3198070` (latest product implementation commit for this scope)
- source_path: `xrefkit/azure_connection.py`, `azure_import.py`, `azure_update_candidate.py`, `azure_writer.py`, `azure_recovery.py`, `work_management.py`
- source_locator: profile validation; capture/bind; build_candidate; publish; inspect_status/reconcile/ancestry/eligible; plan persistence
- inspected_at: 2026-10-11
- supporting_design: [Azure/local work-item mapping](../../docs/designs/113_azure_local_work_item_mapping_design.md#xid-CDEDC36349C3)
- supporting_structure: [Current source findings](../source_analysis/173_xrefkit_python_client_work_structure_findings.md#xid-D4B4C2657A63)

Revalidate after source, schema, state reducer, authentication, persistence,
target guard or transport changes. Structural authoring checks do not establish
actual remote delivery, security certification or general production readiness.
