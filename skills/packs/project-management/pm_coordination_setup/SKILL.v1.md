---
schema_version: 1
skill_id: pm_coordination_setup
xid: F7B3C9A204D6
summary: configure PM decision and stakeholder coordination records from valid organization rules and confirmed project settings
applies_when:
- PM decision authority, stakeholder responsibilities, consultation paths or agreement-to-delivery traceability need initial setup or a bounded revision
exclusions:
- replacing progress_rules_setup, inventing organizational authority, assigning stakeholders, and comprehensive procurement or contract management
inputs:
- selected project, applicable organization Knowledge and project settings with source authority, existing progress_rules_setup result, and known decision and stakeholder roles
outputs:
- confirmed decision-coordination settings or a bounded proposal with source applicability, human answers, role and record mapping, unresolved fields and setup handoff
criteria:
- id: existing_rule_applicability
  statement: Valid organization rules are reused separately from project-specific settings, and only missing or conflicting decisions are proposed to humans.
  verification: Trace each setting to its source, applicability and confirmation or explicitly unresolved decision.
- id: complementary_setup
  statement: Progress and persistence rules retain their existing owner while PM coordination adds only decision, consultation and traceability settings.
  verification: Compare the setup result with progress_rules_setup and identify the owner of each proposed change.
- id: usable_record_mapping
  statement: Each required coordination record has a designated location, updater, evidence basis, revision handling and links to internal reflection and quality results.
  verification: Inspect the record mapping and unresolved handoff without inferring delivery or operational adoption from a proposal.
knowledge_needs:
- id: organization_decision_rules
  query: selected organization valid decision authority meeting mandates referral conditions required materials communication rules record ownership
  required_when: Required before proposing or confirming the project's decision and consultation arrangements.
  seed_xids: []
- id: project_coordination_settings
  query: selected project progress rules stakeholder responsibilities decision boundaries record destinations internal artifact quality ownership
  required_when: Required before deciding what setup is already established and before persisting confirmed changes.
  seed_xids: []
control_refs: []
---
<!-- xid: F7B3C9A204D6 -->
<a id="xid-F7B3C9A204D6"></a>

# Skill: pm_coordination_setup

Public draft source. Select the matching external record at
`governance/skills/pm_coordination_setup.json` for readiness or a run. Do not
omit draft governance to obtain an unassessed run. Publication is not promotion.

## Setup boundary

Use [progress_rules_setup](../progress_rules_setup/SKILL.v1.md#xid-91F7D3B6A204)
for the existing progress, persistence and delivery setup. Consume its confirmed
result; route missing base settings or changes to that owner. This method adds
PM decision and stakeholder coordination settings without repeating base setup.

1. Resolve only the organization and project Knowledge needed for this scope.
   Record source/version, authority, scope and evidence that a rule is current
   and applicable. Separate organization-wide rules from project-specific
   choices. Reuse valid rules without asking people to approve them again;
   retain conflicting or unestablished applicability as a named setup gap.
2. Identify the existing decision arrangements: what each body or person may
   decide, referral conditions, required materials, decision records and
   communication methods. Meetings are an optional local arrangement, not a
   universal requirement. Do not fix a committee, template, storage location
   or messaging service in this common Skill.
3. Confirm the PM's delegated scope, decisions requiring another authority,
   and the agreed stakeholder roles and responsibility boundaries. Use an
   existing role map; propose only missing or changed involvement for the PM
   or designated authority to settle. Record who may confirm updates and their
   evidence. Neither the AI nor this setup assigns people or changes authority.
4. Extend the existing record mapping for internal confirmation items, proposed
   consultation targets and reasons, requests, attributable answers, AI
   sufficiency/consistency findings, PM agreement judgments, applicable scope
   and conditions, unresolved matters, role changes, internal return,
   requirements/design/WBS reflection, verification items and quality-owner
   results. For each needed record, establish who records what, where, on what
   evidence, with which stable link and revision rule. Reuse existing artifacts
   and avoid introducing a parallel tracker. Decide how responses from separate
   people and times remain attributable and how the next owner/action is shown.
5. Present only gaps or proposed changes to the responsible humans. Record
   questions, answers, confirmed scope, conditions and unresolved decisions.
   Keep adopted organizational rules in their existing authoritative Knowledge;
   store confirmed project values in project Knowledge or its configured rule
   repository through the applicable authorized route. The Skill owns this
   procedure, not the values. Missing Knowledge remains missing, not fabricated
   organization policy.
6. Save confirmed settings using the existing
   [persistence handoff](../progress_rules_setup/references/persistence_handoff.md#xid-62A9D4E7B103).
   Preserve the configured delivery endpoint and evidence rules. If a destination
   or authority is unresolved, retain a reviewable proposal in the work area
   with its owner and next decision; do not call it an applied configuration.
   This Skill provides artifacts or handoff through existing means, not direct
   Slack, Teams or email sending.

## Completion and reload

Return the settings revision and source links, confirmed responsibility map,
record mapping, human decisions, unresolved fields, delivery evidence and next
owner/action. Hand only the confirmed scope to
[pm_decision_coordination](../pm_decision_coordination/SKILL.v1.md#xid-C8E4A1D760B3).
On reload or a role/scope change, compare current authoritative settings and
the prior revision before reusing them. Stop affected operational guidance when
required authority or record mapping is unresolved; continue bounded proposal
preparation. A completed setup handoff does not imply operational readiness for
the unresolved scope.
