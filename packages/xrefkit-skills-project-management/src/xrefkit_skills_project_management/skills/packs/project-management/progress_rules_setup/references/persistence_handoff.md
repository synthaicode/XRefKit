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

Apply this procedure to human-facing Issue and Project updates, progress reports,
review results and approval requests. Use the confirmed record mapping. For
projects that designate a GitHub Project, use it as the progress entry point:

- GitHub Project owns the configured status, priority, assignee, blockers and
  decisions awaiting a response. Use its existing fields and links.
- GitHub Issue shows the work purpose, acceptance criteria, current decision
  requests and next action. Link the Project item and evidence as applicable.
- The configured evidence and execution records retain investigation, sources,
  selected Knowledge XIDs, revisions and hashes, execution and verification
  logs, model and tool receipts, Decision and Execution history, unknowns and
  hypotheses, approval history, baselines, differences, snapshots, test
  results and failure conditions, and related Issue and Knowledge links.
  Keep each record with its existing owner and access rules. Knowledge supplies
  applicable rules and source-backed findings. Run-specific records stay in
  their designated evidence stores.

Identify the authoritative location for each record type. Reuse existing
records and link their exact revision wherever it matters to a judgment. Preserve
history and existing references, including substantive legacy Issue content,
before replacing any part of a current display. If a move would break a
reference, lose history, or expose restricted evidence, keep the affected
content and report the unresolved mapping, access or preservation step.

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
3. For each approval request, state what is being approved, what approval
   enables, what remains outside its scope, what stays held if deferred and
   the material unresolved risks. Identify the decision owner from the
   configured rules and link the exact scope and revision. Keep design
   approval, work start, external API execution and data changes as separate
   grants of authority. Record an approval only from an explicit, attributable
   human decision within that scope. AI recommendations, review verdicts and
   test results remain evidence. Omit the request when no human decision is
   needed.
4. Compare the view against the source for each decision and its evidence.
   Retain every decision-changing condition, relevant blocker, material
   unknown, and next owner or unresolved ownership in the view. Update only
   the existing current-state portion of an Issue or the applicable Project
   fields. Recompute the view from current records on each update instead of
   appending successive reports to that portion. If no safe update boundary or
   authorized preservation route is established, prepare the view for handoff
   without overwriting the existing body.
5. For AI handoff and restart, return the authoritative detailed records,
   revisions and unresolved items to the receiving owner. A Human View is a
   regenerable display of those records. It cannot serve as the source for an
   AI handoff, an approval, or a Runtime or Brownfield progression decision.

## Update procedure

1. Read the current designated record and revision where applicable. Determine
   the configured artifact, save/delivery steps and authorized receiving route.
   Check which steps available tools or people can perform. A connection or
   read permission is not write authority, and a missing remote writer does not
   prevent authorized artifact preparation or a configured file handoff.
2. Prepare the smallest update, preserving unrelated content and history.
   Distinguish proposed changes, received human answers, applied answers and
   confirmed decisions. Link the evidence rather than copying a status claim
   without provenance. Prepare the Human View from the applicable records and
   apply configured conflict/revision protection.
3. Perform the supported authorized steps and verify their actual outputs
   against project rules. For files, inspect the saved artifact at the intended
   path; for attachment/link registration or direct updates, inspect the
   available result and configured confirmation evidence. Require readback or a
   receipt only when the applicable project/adapter contract requires it. Keep
   artifact produced, saved at the designated location, uploaded/linked, handed
   to the designated person, and team visibility confirmed distinct; report only
   the outcomes supported by evidence. Inspect partial or uncertain operation
   results before retrying to avoid duplicate actions.
4. Return artifact paths or record links, the specific questions the human needs
   to answer, and the smallest remaining delivery actions with their owner.
   Persist those answers through the same route when they arrive. Next time,
   reload the authoritative management and detail records as the basis for work.

## Existing routes and limits

- [local_work_management](https://github.com/synthaicode/XRefKit/blob/main/skills/os/local_work_management/SKILL.v1.md#xid-E7C4A916B280) persists approved local plans and
  explicit observations. Use it only when the configured local plan schema and
  required approvals support the requested record; do not treat it as a generic
  team issue or Knowledge writer. Local persistence is not team accessibility.
- [azure_work_item_integration](https://github.com/synthaicode/XRefKit/blob/main/skills/os/azure_work_item_integration/SKILL.v1.md#xid-A19E6D4C82B7) is an optional separately
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
