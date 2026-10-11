---
schema_version: 1
skill_id: azure_work_item_integration
xid: A19E6D4C82B7
summary: operate workspace-scoped Azure work-item import, explicit plan binding, deterministic Task delivery, and read-only reconciliation
applies_when:
- a user authorizes XRefKit client-work integration operations against an explicitly selected Azure DevOps Services test project
exclusions:
- production connections, arbitrary Task writes, PBI acceptance, conflict overwrite, Bug creation, project creation, artifact upload, and automatic background synchronization
inputs:
- requested operation and authorization, registered repository/workspace, selected connection identity, exact external IDs, local plan/revision/observation, approval and completion evidence, and explicit predecessor records when applicable
outputs:
- selected operation inputs, immutable import/binding/delivery/reconciliation records or explicit diagnostic, local evidence links, verification scope, and next-owner handoff
criteria:
- id: exact_scope
  statement: Every operation uses the selected workspace and explicitly permitted test target; current hard-coded delivery limits are respected.
  verification: Compare the request, profile, binding and selected operation with the operating-model Knowledge and current implementation.
- id: deterministic_delivery
  statement: Delivery uses explicit recorded assertions and the constrained reducer; completion and business acceptance are not inferred.
  verification: Inspect observation revision, completion and authorization evidence, patch scope, and disposition.
- id: immutable_recovery
  statement: Replay and recovery preserve original records and never perform a blind resend or erase a lock.
  verification: Inspect report/reconciliation identities, proof, ancestry and explicit predecessor selection.
- id: honest_handoff
  statement: Outcomes distinguish local preparation, historical replay, remote read and confirmed delivery; local evidence is not claimed as team accessible.
  verification: Compare the report with saved records and identify remaining human judgments.
knowledge_needs:
- id: azure_operating_model
  query: XRefKit Azure DevOps client work integration operating model import binding delivery reconciliation
  required_when: Required before selecting or executing any integration operation.
  seed_xids:
  - C8E2A591D740
- id: current_source_findings
  query: XRefKit Python client work management current import writer recovery structure findings
  required_when: Required when determining implementation support or investigating a rejected or uncertain operation.
  seed_xids:
  - D4B4C2657A63
control_refs: []
---
<!-- xid: A19E6D4C82B7 -->
<a id="xid-A19E6D4C82B7"></a>

# Skill: azure_work_item_integration

## Local-primary boundary

Local planning, Markdown/Mermaid and observations are independently handled by
[local_work_management](../local_work_management/SKILL.v1.md#xid-E7C4A916B280).
This Skill is an optional explicitly authorized adapter. A configured connection
does not trigger it; it does not own or regenerate local plan state. Complete
local work without invoking this Skill when Azure integration is not requested.

## Startup and selection

Use the repository Skill runtime envelope and its operating contract. Load the
[operating model](../../../knowledge/operations/160_azure_devops_client_work_integration.md#xid-C8E2A591D740)
through its XID before executing commands. Select only the operation requested
or already authorized by the human; creating this public Skill does not
authorize a remote operation. Verify the implementation version if the selected
operation depends on the
[source finding](../../../knowledge/source_analysis/173_xrefkit_python_client_work_structure_findings.md#xid-D4B4C2657A63).

Identify the registered workspace, explicit test connection, exact organization
and project, external IDs, and current stored plan/observation. Keep credentials
in the named process environment only. Inspect profile and request input without
printing secrets. Use new explicit connection identities for changed profiles.
Current writer/recovery support is **PBI 10 / Task 21 only**, even in a different
organization/project. Other authorized test IDs support read/import/binding,
not arbitrary delivery. Stop an unsupported operation with this limitation.

## Planning and preparation

Record concrete items for the selected operations and their evidence. Prepare
strict schema inputs from recorded identities and evidence using the
[request examples](references/request_examples.md#xid-B27C9E15A640).
Examples are inert format samples, not approved scope or completion proof.
Do not guess observation revisions, select records by modification time, or
create synthetic approval/completion evidence. Establish which outputs belong
to import, binding, delivery, reconciliation, and human judgment separately.

## Execution branches

Run only the selected branch using the chosen repository root and workspace:

| Operation | Command shape | Evidence to inspect |
| --- | --- | --- |
| Register profile | `python -m xrefkit.azure_connection register --root ROOT --workspace-id WORKSPACE --input PROFILE.json` | Exact immutable registration, no network claim |
| Read check | `python -m xrefkit.azure_connection read-check --root ROOT --workspace-id WORKSPACE --connection-id CONNECTION --item-id ID` | Read scope, diagnostic and checked time; no write-permission claim |
| Capture | `python -m xrefkit.azure_import capture --root ROOT --workspace-id WORKSPACE --input IMPORT.json` | All explicitly selected items, partial failures, target and capture hash |
| Bind | `python -m xrefkit.azure_import bind --root ROOT --workspace-id WORKSPACE --input BINDING.json` | Complete capture, approved mapping, immutable plan definition and observation |
| Offline preview | `python -m xrefkit.azure_update_candidate --input ENVELOPE.json` | Supplied snapshots and `not_sent`; no current-state claim |
| Publish | `python -m xrefkit.azure_writer publish --root ROOT --workspace-id WORKSPACE --input DELIVERY.json` | Durable intent, constrained patch, receipt and readback |
| Inspect local delivery | `python -m xrefkit.azure_recovery status --root ROOT --workspace-id WORKSPACE --report-id REPORT` | Local records and explicit guidance; no network |
| Reconcile | `python -m xrefkit.azure_recovery reconcile --root ROOT --workspace-id WORKSPACE --input RECONCILIATION.json` | Read-only full historical/current proof and separate reconciliation |

For capture, do not bind a partial result. For binding, cover every selected Task
exactly once with disjoint included step IDs and explicit completion criteria.
For a comparison capture, select `comparison_binding_id` explicitly and retain
the baseline; a changed result requires resolution rather than replacement.

For publish, verify actual authorization for Task state/summary reflection,
current observation and completion/work authorization evidence. Allow the
implementation to reduce the state and generate History; do not replace its
patch with arbitrary content. Do not treat a successful read as write approval.
After the operation, report the saved disposition and confirmation fields.
Exact replay returns historical records, not a new execution or fresh check.

For uncertain delivery, inspect locally first. If authorized, reconcile under a
new explicit reconciliation ID, preserving the original intent/receipt. A
confirmed historical application followed by remote changes is not resumable.
Where saved proof and current guidance permit a new delivery, require a new
local observation, a new report ID and exactly one explicit predecessor:
`previous_report_id` for confirmed success, or
`previous_reconciliation_id` for an eligible confirmed reconciliation. Repeat
the normal publish checks. Reconciliation itself never sends.

## Monitoring, stop and handoff

Stop on unknown target/observation, unsupported scope, incomplete capture,
mapping ambiguity, stale revision, unrecorded transition, unresolved
revalidation, pending uncertain send, unsupported ancestry or protected-field
change. Preserve `hold`, `conflict`, `rejected`, `unknown` and recovery outcomes;
do not reinterpret them as success or confirmed absence of sending.

Hand PBI acceptance, conflict resolution and new Bug registration to the human
decision owner. Preserve locks and records; deleting them or changing IDs to
bypass an uncertain send is outside this Skill. Keep artifacts local-first and
report accessibility as unverified. A request to expand hard-coded targets or
production support requires separately designed implementation work.

## Completion and continuity

Record selected target and operation, input identities, outputs, outcome and
timestamps, local evidence links, replay/fresh distinction, outstanding
judgments and next owner in the run/session records. Complete the selected
operation only when its saved result is verified or the blocker is explicitly
handed off. Follow runtime verification and closure; operation success does not
accept the PBI. Public repository placement does not establish maturity,
production adoption or remote distribution.
