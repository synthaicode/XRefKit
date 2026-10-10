<!-- xid: CDEDC36349C3 -->
<a id="xid-CDEDC36349C3"></a>

# Azure Local Work Item Mapping Design

Status: accepted trial mapping contract, independently reviewed. This is the downstream integration contract. Implemented Task17 remains test-only read; this document does not expand any connection profile or execute writes.

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

## Synchronization boundary

Before a future write, resolve exact binding, allowed operations, selected item, latest local observation and expected remote revision. Check/CAS the expected local observation_revision immediately before publication so concurrent revalidation invalidates a stale Done candidate. Recheck metadata transition and send only permitted State/History changes together with a JSON Patch test on /rev for optimistic revision protection. A conflict does not overwrite either side. Keep the candidate, observed differences and user's resolution. Repeated report identity must not append duplicate history; an ambiguous timeout requires remote reconciliation, not blind retry. Partial results are per item, never a batch-wide success claim. Saved local records remain authoritative even when sharing fails.

Task18 settles mapping, not implementation of retries, outbox, transport or write permissions. Future writer must implement the above acceptance obligations before being enabled. Task17 profile remains read_work_item/PBI10 only; this contract does not authorize profile replacement or production use.

## Validation and Implementation Boundary

The Task18 mapping proposal contains the captured Scrum metadata, required-field/default table, transition and failure examples, and independently reviewed validation evidence. Those observations do not prove universal conditional rules or production write authority. Future writer implementation must test the state/ownership/revision/replay obligations above against the selected project's current metadata and permissions.

Task states in the accepted trial are To Do, In Progress, Done and Removed. PBI/Bug states are New, Approved, Committed, Done and Removed. Do not assume another project's process uses these names. Task has no AcceptanceCriteria field in the captured process; its completion criterion stays in the local plan/binding.

Current executable capability is workspace-scoped test read only. Automatic synchronization, grouped-binding execution, profile expansion and production activation remain downstream implementation. Contract acceptance does not enable them.

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
