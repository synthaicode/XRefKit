---
schema_version: 1
skill_id: pm_decision_coordination
xid: C8E4A1D760B3
summary: support PM decisions and scoped stakeholder agreement while tracing internal reflection, quality results and bounded work-start choices through project closure
applies_when:
- internal work has produced confirmation items or readiness results that need PM handling, stakeholder coordination, agreement follow-through or a bounded start decision
- changed agreements, conditions or involvement require renewed coordination during any project stage
exclusions:
- regenerating internal confirmation questions, technical readiness evaluation, product quality acceptance, automatic start approval, unapproved plan changes, external message sending, and comprehensive procurement or contract management
inputs:
- confirmed coordination settings and stakeholder roles, internal confirmation-item records, attributable answers and decisions, current requirements/design/WBS and verification links, internal start-condition results and quality-owner results
outputs:
- versioned coordination records linking PM routing and agreement judgments, stakeholder answers and conditions, AI findings, internal handoffs and reflection/quality state, impact evidence and PM work-start choices
criteria:
- id: decision_authority
  statement: PM routing and agreement judgments remain distinct from AI proposals and consistency findings, within actual organization authority.
  verification: Trace each adopted judgment to the PM or designated authority, retained findings and treatment; do not substitute invented unanimity requirements.
- id: scoped_agreement
  statement: Answers and agreements remain attributable with scope, conditions, unanswered parts, conflicts and next action across asynchronous participants.
  verification: Compare original questions, responses and decisions without treating silence or a local agreement as everyone's answer.
- id: end_to_end_trace
  statement: Answer receipt, sufficiency, internal delivery, artifact reflection and quality verification are distinct and linked to exact revisions.
  verification: Check link existence and semantic alignment from confirmation item through answer/decision to requirements, design, WBS, verification and quality-owner result; preserve missing or stale coverage.
- id: bounded_start_choice
  statement: PM work-start choices consume the existing internal readiness result and expose remaining conditions and impacts without duplicating evaluation or authorizing starts automatically.
  verification: Trace each proposed slice and PM choice to the scoped internal result, unresolved conditions, evidence limits and authorized return path.
knowledge_needs:
- id: coordination_authority_and_roles
  query: selected project confirmed PM decision scope stakeholder role responsibility consultation process organization authority conditions
  required_when: Required before proposing a consultation target or using a PM decision.
  seed_xids: []
- id: coordination_records_and_plan
  query: selected project coordination record mapping current requirements design WBS dependencies quality owners verification decision deadline delivery rules
  required_when: Required before tracing reflection, assessing decision delay or recording a coordination result.
  seed_xids: []
control_refs: []
---
<!-- xid: C8E4A1D760B3 -->
<a id="xid-C8E4A1D760B3"></a>

# Skill: pm_decision_coordination

Public draft source. Select the matching external record at
`governance/skills/pm_decision_coordination.json` for readiness or a run. Do not
omit draft governance to obtain an unassessed run. Publication is not promotion.

## Startup and ownership

Reload current coordination settings and designated records, including their
revisions and pending actions. Missing or changed decision/role settings go to
[pm_coordination_setup](../pm_coordination_setup/SKILL.v1.md#xid-F7B3C9A204D6);
base progress and persistence settings remain with
[progress_rules_setup](../progress_rules_setup/SKILL.v1.md#xid-91F7D3B6A204).
An existing configured artifact or human handoff is sufficient; no direct
communication integration or all-participant meeting is required.

Receive confirmation items from their existing internal owner, including
[requirements_discovery_coordination](../requirements_discovery_coordination/SKILL.v1.md#xid-3B8E71A5C902),
and scoped condition results from
[work_progress_coordination](../work_progress_coordination/SKILL.v1.md#xid-A4D902C7E651).
Other stages may supply their own current internal items. Keep source identity,
question, evidence, affected scope, requested decision and needed-by point.
Return an unclear or incomplete source item to its owner for clarification;
do not perform a second internal question-generation process.

## Decision and agreement cycle

1. First propose whether the PM can handle the item within their authority and
   return it directly, or whether stakeholder coordination is needed. Show the
   reason and relevant authority boundary; the PM makes the routing decision.
   A PM-handled answer retains the same attribution, condition and internal
   return trace as a coordinated answer.
2. For coordination, use the agreed stakeholder responsibility map to propose
   the relevant contact and reason. Do not identify everyone anew each cycle.
   Overlapping responsibility goes to the PM. If no role matches, or a changed
   proposal/scope needs different involvement, show the gap and candidate
   relationship to the PM and request an authorized role-map update. Do not
   silently assign responsibility or expand authority.
3. Prepare the question or request with its source links, affected scope,
   decision needed and needed-by point. Use the configured artifacts and human
   handoff; this method does not send Slack, Teams or email messages. Track
   each participant's request, answer/source, date or recorded timing, scope,
   conditions, missing answer parts, contradictions, unresolved items and next
   person/action. Keep separate exchanges and small-group agreements separate
   until the PM determines their broader applicability. Silence is not consent.
4. Check whether answers address the original question sufficiently and agree
   on conditions and target scope. Explicitly identify each missing answer
   part, contradiction or scope mismatch and its source. This is the AI's
   consistency assessment, not a product quality verdict or an agreement vote.
   Present it to the PM. If the PM judges agreement reached within actual
   authority, adopt and record that judgment with its scope and conditions;
   do not reject it using an AI-invented requirement for evidence of everyone's
   consent. When findings remain, record the PM's treatment, decision basis,
   residual follow-up and owner. Preserve actual individual answers and never
   manufacture another person's response or unanimous consent. A genuine
   organizational authority constraint still requires its designated owner.
5. Return the decision and applicable conditions to the originating internal
   owner and affected artifact/quality owners through the configured path.
   Maintain a trace from confirmation item -> proposed/confirmed contact ->
   answer and PM agreement judgment -> affected requirement, design and WBS
   items -> verification items -> quality-owner results. Record revisions and
   applicability for each link. Explicitly explain a non-applicable link under
   the project's rules; a missing required link stays a gap. Check both that
   links resolve and that their content covers the same decision, conditions,
   scope and version. Route technical interpretation or verification to the
   internal owner instead of assuming semantic consistency from an ID match.
6. Distinguish answer received, sufficiency checked, decision made, internal
   delivery, artifact reflection and quality verification. Expose, for example,
   agreement awaiting reflection, reflected awaiting verification, and a quality
   problem requiring renewed coordination as separate recorded observations,
   not new repository status enums. Consume the artifact and quality owners'
   results; do not perform product verification, issue acceptance or overwrite
   their verdict. Track the next owner/action for every outstanding stage.
7. Connect agreements and unresolved issues to quality, cost and schedule.
   Show when a decision must be made to avoid affecting which work or join
   point, and which external wait/hold may become a bottleneck. Use existing
   plan/dependency evidence and separate observations from proposed impacts.
   Where numerical support is absent, label cost/duration estimates unknown;
   do not manufacture numbers, critical paths or guaranteed delay outcomes.
8. For a PM work-start choice, consume the current scoped result already
   established by work_progress_coordination. Present which WBS work and how
   much can be considered, remaining/unmet conditions, bounded assumptions,
   potential rework and downstream/cost/date effects with their evidence limits.
   Do not reimplement technical or deterministic readiness evaluation. Missing,
   stale or changed conditions return to that owner for a refreshed result.
   The PM selects the start scope within actual authority; the AI does not
   approve a start. Record the choice, rationale, conditions, remaining holds
   and result revision and return it to internal coordination. WBS or plan
   changes use the existing authorized persistence route; do not rewrite them
   merely because a candidate was proposed or a judgment was recorded.
9. Repeat this outer/inner exchange through project closure, not just during
   requirements discovery. For agreement revisions, preserve the superseded
   decision and identify affected artifacts, work and verification evidence.
   Ask the responsible owners to reassess affected readiness and quality
   results; an old pass does not automatically cover a revised agreement.

## Completion and handoff

Persist each cycle through the configured
[persistence handoff](../progress_rules_setup/references/persistence_handoff.md#xid-62A9D4E7B103).
Return source/settings revisions, attributable answers, AI findings, PM decisions
and treatment, exact applicability, internal reflection/quality links, outstanding
owners/actions, decision timing and bounded start choices. Distinguish prepared,
delivered and confirmed reflected records using actual endpoint evidence.
Stop only the affected authority/readiness/quality claim when required evidence
is missing; continue authorized preparation and make the resolving handoff
explicit. A finished coordination cycle is not project completion, unanimous
agreement, product acceptance or permission to execute a draft Skill.
