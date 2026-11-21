<!-- xid: 62A9D4E7B103 -->
<a id="xid-62A9D4E7B103"></a>

# Persistence and receiving-route handoff

Read this reference when a work-practice Skill prepares or records project
updates. It specifies reusable handling, not a project schema or status enum.

## Record mapping

Use the confirmed project mapping for each record: work status, deliverable,
unknown, hold, assignment/next action, human answer/confirmation/agreement, and
quality result. Preserve project identifiers and meanings. Minimum trace content
is the relevant item and scope, source/evidence version, current recorded fact
or proposal, owner and next action, linked answer/decision, and destination.
Add resolution point and impact for holds, and exact scope/version/issuer for
quality decisions. Do not make up absent people, decisions or values.

The project chooses the record form and delivery path: Markdown or other file
artifacts, saving to a designated folder, attachment or link registration in a
management item, direct supported updates, or an explicit handoff to a person.
Establish which artifact/location is authoritative, who performs any remaining
step, and what evidence establishes completion under those project rules.
A designated local file or human handoff can be the agreed endpoint; direct API
access and a remote receipt are not universal completion requirements.
Establish destination, format, sharing/attachment method and completion criteria
during `progress_rules_setup`. Operational coordinators must use those confirmed
settings. Markdown/file output is an option for setup, not permission to replace
an approved delivery method. If settings are absent or a method is unsupported,
propose the alternative and obtain the designated confirmation through setup;
until then any authorized prepared artifact is a provisional handoff only.

## Human View and authoritative records

Apply this procedure to Issue and Project updates, progress reports, reviews and
approval requests. Follow the confirmed project mapping and classify content
by meaning, even when an older artifact mixed several roles.

| Content | Current location and owner |
| --- | --- |
| Work intent, requirements, acceptance criteria, current decisions and approval state, next action and owner | The canonical Issue or the existing authoritative work item. In GitHub, keep these in the current Issue work record, together with its verified reference declarations and links to the applicable decisions and approvals. |
| Board status, priority, assignment and configured hold fields | The mapped GitHub Project item when GitHub is configured. Verify its identity and field values. A Project label such as Todo can coexist with an evidenced dependency hold. |
| Decision and Execution plans, dependencies, schedules and CPM, approvals, baseline, plan revisions and actual snapshots | Existing Project Management records and their configured owners. Link the exact applicable versions from the current Issue. |
| Design, API contracts, investigation, technical unknowns, tests and evidence | The configured Evidence, Knowledge, document, Brownfield or Runtime stores. Preserve applicable ownership, scope, revisions, XIDs and hashes. |
| Older Issue text, decisions as recorded at that time and prior evidence references | Use GitHub's native Issue edit history by default. Use a separate immutable copy only when the confirmed record rules require one or the owner approves a preservation route for a concrete history gap. Resolve current obligations from the live Issue and its current sources. |
| Concise display of current state, material changes, decisions due now, blockers, risks and next action | The regenerable Human View at the top of the Issue. Link the current sources and clearly identify archive links as history. |

Keep existing stores, access rules and authority boundaries. One item of
information has one current owner. A reference from an Issue conveys that
source's scope and revision. Resolve required references and check that their
content supports the work before showing a status or preparing a handoff.
Clarify an unresolved mapping through the existing project setup.

## Write work-specific requirements

Keep the current Issue requirements focused on what this item must change,
deliver or constrain. Leave standard XRefKit startup, Runtime binding and XID
handling in their existing contracts. Include a startup, binding or XID rule
in Requirements when this item changes it or depends on an Issue-specific
condition. Retain the acceptance checks that establish this item's required
behavior, including work-specific validation of existing controls.

## Prepare the Human View

1. Read the current authoritative records. On progress updates, compare them
   with the identifiable source revision from the last report and lead with
   material changes in status, verified facts, decisions, risks, plans, dates,
   owners or blockers. Report no material change when the comparison shows
   none. If the prior basis cannot be established, label the baseline unknown
   and report current state without claiming a change.
2. Put the conclusion first. Include the decision needed (when there is one),
   its reason and impact, material risks or unknowns, and the next action and
   responsible person or role. Keep confirmed facts, proposals, hypotheses and
   unverified claims distinct. For a review result, show the verdict, covered
   scope and the gaps that affect the current decision. State the concrete
   work or decision and its current status in plain language. Use a verified
   project-specific meaning for stage and status codes. Include the code only
   when it helps readers locate the record or decide. If its meaning is unknown,
   state what the records establish and flag the gap when it affects the decision.
   Preserve exact identifiers and enum values in formal records and fields. For
   example, Issue #199 can say "The API executor design is awaiting the requester's
   decision. Implementation start is separately on hold." Here `P0` is a
   project-specific stage label. Link details through references the intended
   reader can access. Keep identifiers and technical
   detail in the linked records unless the reader needs them to decide. Aim for
   one screen (roughly 300–500 Japanese characters for an ordinary Japanese
   update). Preserve meaning and split by decision when necessary.
3. First check the authoritative blocker, review and acceptance records.
   A dependency hold, planned approval or reviewer assignment does not by
   itself create a decision for the reader. Ask only for a decision explicitly
   actionable at the current record revision. For each request, state the
   question, why it is due now, options and their effects, any evidenced
   recommendation, the authorization scope and the impact of deferral. Identify
   the decision owner from the configured rules and link the exact scope and revision. Keep design
   approval, work start, external API execution and data changes as separate
   grants of authority. Record an approval only from an explicit, attributable
   human decision within that scope. AI recommendations, review verdicts and
   test results remain evidence. Omit the request when no human decision is
   needed.
4. Compare the view against its sources. Keep every decision-changing condition,
   relevant blocker, material unknown and next owner visible. Keep the current
   Issue work record and its reference declarations outside the single managed
   Human View. Replace the view at the top in place and preserve manual content
   outside the declared blocks byte for byte. Check the prior delivery before
   replacing a managed block. An unexpected edit requires reconciliation.
   Preserve Issue identity, comments and native edit history for GitHub.
   Verify the exact Issue revision and complete pre-edit body against the
   designated history source before an update that replaces existing content.
   Read back the prior version through native edit history after delivery.
   For an authorized legacy migration, bind approval to the exact Issue and
   revision, and preserve old fragment names through a checked mapping to the
   relevant surviving content. If required history or link preservation cannot
   be verified, hold the change for review. Use a separate archive only through
   an agreed route that addresses the verified preservation need.
5. For AI handoff and restart, read the current Issue work record at its verified
   revision. Follow its current references to applicable PM decisions, execution
   plan and verified technical evidence. Carry the exact work intent, requirements,
   acceptance criteria, open unknowns, authorization limits and stop conditions
   into the existing Workflow Runtime Binding. A summary, an old Issue archive
   or an earlier passed check is insufficient for current implementation input.
   Stop the affected handoff when any required current source is missing, stale,
   mismatched or outside the approved scope. Keep other authorized work moving.

## Update procedure

1. Read the current designated record and revision where applicable. Determine
   the configured artifact, save/delivery steps and authorized receiving route.
   Check which steps available tools or people can perform. A connection or
   read permission is not write authority, and a missing remote writer does not
   prevent authorized artifact preparation or a configured file handoff.
2. Prepare the smallest update. Record confirmed changes with their existing
   owners first and verify saved revision, scope and content identity before
   linking them from the Issue. Keep proposed changes distinct from applied
   answers and human decisions. Prepare the compact summary from the current
   Issue work record, mapped Project fields and verified applicable sources.
3. Refresh the Issue, Project item and required current sources before updating.
   Use the guarded writer for automated Issue and Project revision comparison.
   If the receiving route lacks the required guarantee, deliver the prepared
   candidate through the configured review handoff. If a record was saved but
   the Issue update failed or its result is uncertain, record each result with
   evidence. Read back the actual Issue, Project and linked records before
   retrying. Reuse verified saved records, reconcile stale or conflicting
   content, and repeat only the unresolved authorized step. Distinguish saved,
   linked, handed off and visible. Confirm completion only from the configured
   endpoint's readback or receipt.

4. Return artifact paths or record links, the specific questions the human needs
   to answer, and the smallest remaining delivery actions with their owner.
   Persist those answers through the same route when they arrive. Next time,
   reload the authoritative management and detail records as the basis for work.

## Existing routes and limits

- [local_work_management](../../../../os/local_work_management/SKILL.v1.md#xid-E7C4A916B280) persists approved local plans and
  explicit observations. Use it only when the configured local plan schema and
  required approvals support the requested record; do not treat it as a generic
  team issue or Knowledge writer. Local persistence is not team accessibility.
- [azure_work_item_integration](../../../../os/azure_work_item_integration/SKILL.v1.md#xid-A19E6D4C82B7) is an optional separately
  authorized adapter. Load its current operating-model Knowledge before using
  it. Do not assume arbitrary target IDs, record types or production writes are
  supported. An illustrative Azure destination is not a configured integration.
- Other delivery steps use an actually available authorized tool or the
  project's human handoff route. Do not
  create a custom UI, SDK adapter or integration as an implicit part of these
  coordination Skills.

If a delivery step is unsupported, finish authorized artifact preparation
and supported save steps without changing the agreed destination or method.
For example, when Azure attachment upload is not supported, produce the
requested or otherwise authorized attachment-ready Markdown/file, identify the
target item when known, and hand over the file plus minimal upload/link steps.
If that artifact or delivery alternative was not authorized, propose it through
setup for confirmation. Do not implement a new adapter as part of this work.

If destination, permission or mapping is unresolved, preserve the prepared
artifact in the authorized work area and record the specific remaining gap,
affected records, impact, resolving owner and next action. Ask for owner or
destination identification only when needed. Stop the unsupported delivery or
dependent readiness claim, not independent authorized artifact preparation.

Assess completion against the configured endpoint. A file saved in the agreed
folder or an evidenced agreed human handoff may complete that record's delivery.
If the rules additionally require upload, linking or shared visibility, retain
those steps as outstanding and do not claim them from local creation alone.
Chat-only notice remains insufficient when the configured output is an artifact
or management record. On resume use the configured authoritative artifact/record
and preserve outstanding human actions rather than assuming they were performed.
