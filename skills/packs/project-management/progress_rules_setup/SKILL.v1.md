---
schema_version: 1
skill_id: progress_rules_setup
xid: 91F7D3B6A204
summary: confirm or propose project progress-management rules and persist human-confirmed settings before coordination
applies_when:
- a project needs its progress-management rules identified, checked for applicability, or established before ongoing coordination
exclusions:
- project-specific policy invention, quality acceptance, work execution, and external integration implementation
inputs:
- project root or equivalent entry point, stated purpose, available rule sources and authority, and any existing configuration or records
outputs:
- applicability record or clearly proposed rule settings, human answers and decision references, confirmed settings location or explicit setup gaps, and operating handoff
criteria:
- id: applicable_rules
  statement: Existing defaults and settings are used only with evidence of applicability, current validity, and authority.
  verification: Compare the applicability record with identified source, version, scope and confirmation evidence.
- id: settings_boundary
  statement: Proposed values remain distinguishable from confirmed project rules and are stored in the project-owned Knowledge or configured rule repository.
  verification: Check settings decisions, unresolved fields, destination, and persisted confirmation links.
- id: actionable_contract
  statement: The confirmed settings identify record destinations, formats, roles, start conditions, transition conditions, and update responsibilities.
  verification: Inspect the rule record and the persistence mapping against the selected project's actual sources.
knowledge_needs:
- id: project_progress_rules
  query: selected project progress rules record destinations roles start transition conditions authority
  required_when: Required when determining whether existing rules apply or before handing off to operational coordination; absence is a setup gap, not permission to invent values.
  seed_xids: []
control_refs: []
---
<!-- xid: 91F7D3B6A204 -->
<a id="xid-91F7D3B6A204"></a>

# Skill: progress_rules_setup

Public draft source. Select the matching external record at
`governance/skills/progress_rules_setup.json` when checking readiness or
opening a run; do not omit draft governance to obtain an unassessed run.
Publication placement does not grant execution, adoption or trial maturity.

## Method

1. Identify the project from its root and available entry documents. Discover
   only the relevant settings, Knowledge and authoritative rule records. Record
   source identity/version, scope, owner and evidence of current applicability.
   A file's existence or a remembered default does not establish validity.
2. If applicable rules are confirmed, explain which rules will be used and
   link them. Ask only about material conflicts or missing settings. Do not
   demand reapproval of an already valid rule or silently replace it.
3. If rules are absent or cannot be established, record the gap and present a
   small proposal for human review. Cover what is saved, where, format and
   responsible updater; work state, deliverables, unknowns, holds and quality
   decisions; decision/confirmation owners; bounded work-start conditions and
   separate stage-transition and completion conditions. A proposed default is
   a discussion starting point, never an applied setting.
4. For each needed record type, establish the project's authoritative
   destination, stable identity/link, format, delivery steps, revision handling
   and required access. Settings may select a Markdown/file artifact, designated
   folder, attachment/link registration, supported direct update or human
   handoff. Confirm the authoritative endpoint, evidence of completion and owner
   of any manual step; do not assume an API connection is required. Use the
   [persistence handoff](references/persistence_handoff.md#xid-62A9D4E7B103).
   Do not fix the common method to Azure DevOps, a particular folder layout,
   or a custom screen. Existing dialogue and artifact links are sufficient.
   Establish destination, format, sharing/attachment method and completion
   criteria at this setup stage. Later operational limitations do not authorize
   a coordinator to switch these settings; return a change proposal here for
   designated human confirmation before applying a replacement method.
5. Record human answers, changed proposals, confirmation scope and unresolved
   fields. Humans establish roles, adoption and stakeholder agreement. Keep
   business/system facts, material locations, existing standards and confirmed
   project values in project Knowledge or its existing authoritative rule
   repository; use the appropriate Knowledge/governance route when needed.
   The Skill owns the procedure, not those project values.
6. Persist confirmed settings through the configured authorized route and
   verify the outcome using the project's evidence rules. Distinguish file
   creation/save, upload/link registration, human handoff and confirmed shared
   visibility. If no destination is yet set, keep the
   proposal in the run's work area and hand the destination decision to the
   project owner. Such a proposal is not an operational configuration.

## Completion and handoff

Hand off to discovery or progress coordination only for the scope whose rules,
record mapping and authority are confirmed and retrievable. Identify the
settings revision, recorded answers, outstanding setup decisions, next owner
and action. Unresolved setup can finish as an explicit setup handoff; it cannot
be reported as rules applied or coordination enabled. On reload, verify the
current settings at their designated location before using prior summaries.

Stop affected delivery or readiness claims when applicability, required
destination, role or transition authority is unresolved. Continue authorized
preparation and save a reviewable proposal with the minimal remaining action.
Whether local saving or human handoff completes delivery follows the confirmed
project rules; do not infer remote registration or visibility from file creation.
