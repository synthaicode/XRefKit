<!-- xid: CDEDC36349C3 -->
<a id="xid-CDEDC36349C3"></a>

# Azure Local Work Item Mapping Design

Status: accepted trial mapping with verified read-only import/binding and selected test Task21 State/History delivery. Task22 read-only reconciliation is also verified against current and exact historical successful delivery records. Independent source review, actual product API/readback/replay checks and the repository quality gate passed; recovery fault scenarios and resumed-write chains were tested in isolation. Automatic retries, real-service fault recovery, broader targets, production and PBI acceptance are not claimed. Task23 is explicitly deferred. This document does not itself expand profiles or execute requests.

## Local-primary architecture

[Local work management](../../skills/os/local_work_management/SKILL.v1.md#xid-E7C4A916B280)
completes plan persistence, Markdown/Mermaid, execution observations and local
verification without Azure. A local PBI has its own recorded purpose and
acceptance owner. This document applies only when the human separately selects
an Azure integration and approves explicit mapping. Connection availability
never triggers synchronization. The Azure/human definition authority below
applies to connected imported items, not every local PBI.

## Identity and item mapping

Bind workspace_id + connection_id + organization + project + external item ID + observed remote revision. Local references retain plan_id, immutable plan_revision, step_id/PBI ID and observation_revision. Same numeric item ID elsewhere is not a match. Explicitly select shared Tasks; retries and fine-grained local steps remain local. One external Task may explicitly bind several included local steps. The binding enumerates stable step IDs and its own completion criterion; retries remain execution records. Export Done only when the external Task criterion is confirmed, every included step is explicitly complete and none has outstanding revalidation or unknown/unrecognized state. Counts alone never decide completion.

| Azure type | Local representation | Authority |
|---|---|---|
| Product Backlog Item | PBI purpose, acceptance criteria, priority and external reference | Azure/human owns definition and acceptance; task completion never accepts PBI |
| Task | Explicit selected local task and remote observation | Local execution owns factual execution record; approved projection shares state and outcome |
| Bug | Explicit defect reference linked to confirmation/investigation/remediation tasks | User decides new Bug registration in this trial; a failed test is not automatically a Bug |

## Field ownership and allowed writes

| Fields/information | Source of truth | Automatic reflection |
|---|---|---|
| PBI System.Title, System.Description, Microsoft.VSTS.Common.AcceptanceCriteria, Priority, State | Azure/human | Read only; no inferred acceptance |
| Task execution state, completion determination, revalidation and evidence references | Local versioned records | Selected Task System.State and append-only System.History summary only |
| Task title/description, assignee, deadline, area/iteration, priority, tags, estimates/RemainingWork, Blocked, relations | Azure/human unless separately approved | No overwrite or automatic update |
| Bug fields/state and registration | User decision | No automatic creation/update |
| ID, revision, server audit fields | Azure server | Read only |

User confirmed automatic reflection of selected Task state/summary after applicable completion criteria are checked. PBI acceptance, assignee/deadline changes and conflict overwrites are excluded. Current trial human owner for PBI acceptance, conflict resolution and new Bug registration is the user. Future project-specific delegation requires an explicit recorded change.

Summary contains exact source tuple/revision, factual outcome, confirmation/revalidation reason where relevant, and safe artifact IDs/versions marked availability=local_only. Artifacts are authoritative in the local project workspace. Do not upload attachments or invent shared URLs by default. Remote readers cannot automatically open local artifacts; no teammate-access claim is made. Keep secrets, raw logs and local absolute paths out. Preserve human descriptions. System.History is append-only result history, not a replacement for the current-state document.

## State projection

| Local situation | Azure Task action |
|---|---|
| pending, first agreed binding | To Do candidate; do not roll an existing advanced item backward |
| in_progress with current authorized work | In Progress candidate |
| done, applicable completion criteria confirmed, no explicit outstanding revalidation | Done candidate |
| blocked, unknown, escalated or unrecognized status | Retain remote state; append bounded factual reason when changed |
| done but explicit revalidation required | Do not export Done; retain state until authorized rework starts |
| authorized rework actually started after prior Done | Explicit reopening to In Progress; preserve old completion evidence |
| missing evidence/status, stale record, omitted task | No inferred completion, reopening or removal |
| Removed, incompatible binding, or unexpected remote/human change relative to the last synchronized baseline | Stop reflection and request user resolution |

An expected difference between a new local candidate and unchanged remote baseline is a normal update, not a conflict. Remote raw state is an observation; it does not replace local execution state or prove PBI acceptance. Remaining step counts continue the existing local projection. Do not manufacture effort/time estimates or RemainingWork=0 from task counts.

## Read-Only Product Import and Explicit Binding

The authorized test target is workspace `xrefkit-local`, organization
`seijim0pattern01`, project `AI01-Scrum`, PBI10 and selected Tasks19/21/22/23.
Use a separate explicitly registered read-only profile. The existing
`ai01-scrum-test` PBI10-only profile stays unchanged. Current plan is
`pbi10-remaining-integration/v2`; each operation supplies the expected current
observation revision instead of assuming a permanently fixed revision.

Import and binding are separate actions with separate success outcomes. Import
performs bounded per-ID GETs with exact project/type/ID and Task parent-PBI
validation, recording an immutable receipt and per-item outcomes. No discovery,
relation traversal, attachments or remote mutation is implied. A partial or
failed receipt retains truthful evidence and cannot be bound. Replaying an
import ID returns the captured receipt, not a fresh observation.

GUID-qualified response URLs are accepted only using the validated root PBI's
canonical self URL as the project GUID anchor, together with exact configured
TeamProject, organization, type and ID checks. Every GUID-qualified Task self
URL and parent relation must match that anchor and the expected item ID.
Task URLs cannot establish an independent project authority. Existing named
project and organization-only routes retain their checks. Response URLs are
never followed. Preserve the sanitized anchor in the receipt; absent and null
legacy anchors both mean unknown during comparison, without rewriting receipts.

Binding consumes a complete receipt and the actual current plan under revision
and lock checks, with explicit approval references and external Task criteria.
The selected groups are Task19 to I1/I2/I3,21 to W1/W2/W3,22 to R1/R2/R3 and23
to A1/A2/A3. Save binding separately and immutably; do not update local plan
status, approval, definitions or run records from remote fields.

A later import may compare against an explicitly selected binding baseline.
Remote changes produce differences and a resolution requirement; neither the
baseline nor local plan is silently replaced. A legitimate later local
observation is permitted only when its supplied expected revision matches the
actual record. Original binding provenance remains unchanged. There is no
multi-file atomic success claim when import succeeds but binding fails.

Implementation acceptance requires negative scope/hierarchy/partial-failure
checks plus actual permitted API import and binding evidence. Independent source review and permitted live import/binding checks passed.
Final-source replay and fresh acquisition at local observation revision 4
preserved the plan and old profile; see task19-product-live-proof.json and
task19-final-source-live-proof.json under work/evidence/client-work-management.
The repository-wide gate passed (1226 tests, 4 platform skips, 83 subtests), and implementation/review runtimes are closed. These results do
not prove remote write permission or complete synchronization.

## Synchronization boundary

The bounded writer targets the explicitly selected test Task21. It uses a
new immutable write profile with explicit source read-profile identity and
approval references; existing read profiles remain unchanged. The actual
import binding supplies the plan identity, grouped steps and completion
criterion. Caller-supplied patches or copied offline previews are not authority.

The writer rereads the exact current local observation under the plan lock,
fetches selected remote identity/revision and Task metadata, then uses the
unchanged pure reducer. Only a valid candidate can produce a deterministic
wire summary and the allowlisted State/History patch. Offline preview flags
remain unchanged. Root PBI is read context only; no PBI or nonselected Task
update is permitted.

A durable immutable intent precedes the single PATCH. Its terminal receipt
requires validated response and readback. An interrupted or ambiguous result
remains unknown and blocks further reports for that target; no automatic resend
is allowed. Same-report replay requires no credentials or network. A later
delivery may explicitly reference a confirmed successful predecessor for the
same binding/target, with a newer local observation and no competing successor.
This own-write chain does not resolve a human conflict or rewrite the initial
import baseline. Explicit read-only reconciliation and the guarded recovered-success chain are implemented; automatic retry and human conflict resolution are not provided.

The bounded writer is independently reviewed and verified by actual product
State/History delivery and readback. The test Task21 is confirmed Done at
revision5. The trial verified an In Progress report before W3 completion, then
used its explicit successful receipt for the Done report. Each report replay
made no network/write attempt or extra revision. Protected fields, relations,
PBI revision7 and local plan/import/binding/read profiles were preserved during
each delivery. The repository gate passed with1298 tests,4 platform skips and
83 subtests. Evidence: task21-product-live-inprogress-proof.json,
task21-product-live-done-proof.json and task21-quality-gate-final.txt under
work/evidence/client-work-management. These results do not accept the PBI.

Before each write, resolve exact binding, allowed operations, selected item, latest local observation and expected remote revision. Check/CAS the expected local observation_revision immediately before publication so concurrent revalidation invalidates a stale Done candidate. Recheck metadata transition and send only permitted State/History changes together with a JSON Patch test on /rev for optimistic revision protection. A conflict does not overwrite either side. Keep the candidate, observed differences and user's resolution. Repeated report identity must not append duplicate history; an ambiguous timeout requires remote reconciliation, not blind retry. Partial results are per item, never a batch-wide success claim. Saved local records remain authoritative even when sharing fails.

Automatic retries and background outbox processing remain unimplemented; delivery reconciliation is an explicit read-only operation. Verified selected test delivery does not establish broader write permissions. Task17 profile remains read_work_item/PBI10 only; this contract does not authorize profile replacement or production use.

## Validation and Implementation Boundary

### Verified Task22 recovery scope

Task22 adds explicit read-only reconciliation for existing Task21 delivery
records. Original intents and terminal receipts remain immutable. A separate
sealed proof correlates the exact intended revision, full History, State,
protected fields and target identity. A missing marker or unchanged current
revision never proves that a possibly dispatched request was not sent.

Historical delivery and current state are separate observations. If the exact
historical revision proves application but the current item has changed, retain
both facts and require resolution without adopting the newer baseline. An
explicit recovered-success predecessor may support a later normal writer only
when all provenance and current-state gates pass. Single-successor checks apply
to the underlying original report across recovery IDs. A validated successful
descendant may retain this discharge in its explicitly selected ancestry;
unrelated unknowns continue blocking the target.

Recovery commands perform no remote writes or automatic retries. Original
receipt timestamps retain their recorded meaning; an unrecorded verification
instant stays unknown. New reconciliation records may capture their actual
verification time. Same-ID replay returns captured evidence without credentials
or network. Task22 implementation passed independent review and the repository
gate (1360 tests,4 platform skips,83 subtests). Actual product GETs confirmed
the existing Done revision5 report and separately proved the earlier In Progress
revision4 report with current state advanced; neither observation sent a write.
Same-ID replay and local status required no credentials or network. Old local
records and PBI10/Task21/Task23 were preserved. Faults, unknown-result recovery
and resumed-write chains were verified in isolated tests, not by causing Azure
failures or a live recovery PATCH. Evidence is task22-product-live-proof.json
and task22-quality-gate-final.txt under work/evidence/client-work-management.
Task23 is explicitly deferred, including final PBI acceptance and editor
certification.

The Task18 mapping proposal contains the captured Scrum metadata, required-field/default table, transition and failure examples, and independently reviewed validation evidence. Those observations do not prove universal conditional rules or production write authority. Any extension must verify the state/ownership/revision/replay obligations against its explicitly selected project metadata and permissions.

Task states in the accepted trial are To Do, In Progress, Done and Removed. PBI/Bug states are New, Approved, Committed, Done and Removed. Do not assume another project's process uses these names. Task has no AcceptanceCriteria field in the captured process; its completion criterion stays in the local plan/binding.

Current executable capabilities are workspace-scoped test read, bounded read-only product import with explicit immutable binding, deterministic offline update-candidate generation from explicit captured snapshots, the explicitly selected test Task21 writer, and explicit read-only delivery status/reconciliation with guarded recovery ancestry. The offline generator validates grouped bindings and emits candidate/hold/conflict/invalid with not_sent and publish_ready=false; it does not fetch, send or certify evidence. Background synchronization, automatic recovery, broader target/profile expansion and production activation remain downstream work. Verified selected delivery does not enable them.

Metadata `alwaysRequired` fields (not a complete create/update payload specification):

| Type | Fields marked alwaysRequired | Metadata defaults |
|---|---|---|
| Task | System.IterationId, System.AreaId, System.Title, System.State | State=To Do |
| Product Backlog Item | System.IterationId, System.AreaId, System.Title, System.State, Microsoft.VSTS.Common.Priority, Microsoft.VSTS.Common.ValueArea | State=New, Priority=2, ValueArea=Business |
| Bug | System.IterationId, System.AreaId, System.Title, System.State, Microsoft.VSTS.Common.ValueArea | State=New, ValueArea=Business |

AreaId/IterationId are server-resolved identifiers of project classification paths; do not fabricate numeric values or infer they must all be sent on every update. Existing-item State/History updates preserve other fields. Defaults describe captured metadata, not tool-chosen business values. Conditional rules, transition validation and effective permissions require separate checks. Task has no AcceptanceCriteria field in this metadata; its completion criterion stays in local binding/plan, not an invented Azure field. Creation is outside this automatic writer mapping.

## Evidence

- Task18 mapping and test examples: `work/designs/2026-10-10_azure_local_mapping_proposal.md`
- Independent acceptance: `work/reports/2026-10-10_azure_mapping_independent_review.md`
- User authority decisions: `work/judgments/2026-10-10_azure_mapping_decisions.md`
- Microsoft API reference: [Update Work Item](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/update?view=azure-devops-rest-7.1)
