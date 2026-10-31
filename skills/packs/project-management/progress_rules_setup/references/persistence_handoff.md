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

## Update procedure

1. Read the current designated record and revision where applicable. Determine
   the configured artifact, save/delivery steps and authorized receiving route.
   Check which steps available tools or people can perform. A connection or
   read permission is not write authority, and a missing remote writer does not
   prevent authorized artifact preparation or a configured file handoff.
2. Prepare the smallest update, preserving unrelated content and history.
   Distinguish proposed changes, received human answers, applied answers and
   confirmed decisions. Link the evidence rather than copying a status claim
   without provenance. Apply configured conflict/revision protection.
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
   reload the management records; chat and internal AI state are not their owner.

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
