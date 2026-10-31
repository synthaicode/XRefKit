---
schema_version: 1
skill_id: requirements_discovery_coordination
xid: 3B8E71A5C902
summary: coordinate repeated clarification and evidence investigation from ambiguous requests while persisting questions, answers and requirement candidates
applies_when:
- a partial request needs alternating human clarification and bounded investigation before responsible humans can finalize requirements
exclusions:
- replacing technical investigation or interview methods, requiring finalized requirements before discovery, and settling stakeholder agreement or final requirements
inputs:
- goal or problem and current-state clues, confirmed applicable progress rules, selected project root and sources, and available prior question, answer and investigation records
outputs:
- versioned discovery-cycle artifacts or records linking questions and scope to evidence, candidate changes, human answers, unresolved items, next investigation, and requirement-owner handoff, with completed and remaining delivery steps
criteria:
- id: early_investigation
  statement: Bounded discovery can begin with an investigable question and permitted sources without treating finalized requirements as a prerequisite.
  verification: Compare the initial question and selected route's actual conditions with the starting request and approved access.
- id: evidence_and_candidate_separation
  statement: Observations, human statements, proposed changes, agreement and final requirement decisions remain separately traceable.
  verification: Trace each candidate to evidence or hypothesis, answer source, scope and explicit decision owner.
- id: durable_iteration
  statement: Each completed cycle persists questions, findings, human answers, changed scope and next actions in the designated records.
  verification: Inspect saved artifacts or record links and project-required delivery evidence, including unapplied answers and unresolved gaps.
knowledge_needs:
- id: project_rules_and_sources
  query: selected project progress rules discovery permissions source layout business context requirement decision owners record mapping
  required_when: Required before selecting a discovery scope or persisting its records.
  seed_xids: []
control_refs: []
---
<!-- xid: 3B8E71A5C902 -->
<a id="xid-3B8E71A5C902"></a>

# Skill: requirements_discovery_coordination

Public draft source. Select the matching external record at
`governance/skills/requirements_discovery_coordination.json` when checking readiness or
opening a run; do not omit draft governance to obtain an unassessed run.
Publication placement does not grant execution, adoption or trial maturity.

## Startup and routing

Read the current project settings and designated records, including prior
questions, answers, decisions and investigation results. If progress rules
are unresolved, hand setup to
[progress_rules_setup](../progress_rules_setup/SKILL.v1.md#xid-91F7D3B6A204).
Do not infer missing settings from a previous chat.

Use existing Skills for the substantive work. Select their current definitions
semantically and respect their runtime readiness, inputs and handoff conditions:

- [business_learning_interview](https://github.com/synthaicode/XRefKit/blob/main/skills/packs/business-intake/business_learning_interview/SKILL.v1.md#xid-B6C4E9A2D781) for goal-first learning
  from fragments; [business_intake_scoping](https://github.com/synthaicode/XRefKit/blob/main/skills/packs/business-intake/business_intake_scoping/SKILL.v1.md#xid-B6C4E9A2D782) when its readiness conditions hold.
- [investigation_flow](https://github.com/synthaicode/XRefKit/blob/main/skills/investigation_flow/SKILL.v1.md#xid-E8B2D6A4C190) or the applicable technical Skill
  for current behavior, code, design, log/data evidence and impact investigation.
- [requirements_flow](https://github.com/synthaicode/XRefKit/blob/main/skills/requirements_flow/SKILL.v1.md#xid-D4A7C91E2B60) when its post-investigation and
  estimation applicability and input conditions hold; do not route early merely
  because this coordination record mentions a requirement.
- [brownfield_workflow](https://github.com/synthaicode/XRefKit/blob/main/skills/brownfield-workflow/SKILL.v1.md#xid-E1A7C4D9B260) for its technical reconciliation,
  design, implementation and quality work, not as this coordinator's checklist.

This Skill coordinates the loop and record continuity; it does not execute a
delegated method in prose or bypass a route that refuses missing prerequisites.

## Discovery cycle

1. From the purpose, problem and current clues, state the first answerable
   question, bounded target and evidence to seek. Requirement finalization is
   not a discovery-start condition. Confirm the actual selected Skill's
   prerequisites and project permissions; ask only for the missing minimum
   material, access or scope needed for that investigation. Do not turn these
   candidate start checks into invented project governance.
2. Persist the question and intended scope before dispatch. Link a technical
   handoff to its source records, expected findings and open issues. Record an
   explicit gap if no applicable load-ready route or permitted source exists.
3. Receive the investigation result and preserve its evidence scope and
   limits. Present supported related-function and change-target candidates,
   possible after-change business flow and remaining questions. Distinguish
   observed behavior from documented rules, human statements and proposals;
   code behavior alone is not an approved specification. Unsupported links stay
   hypotheses. Do not convert a candidate into a fact or approved requirement.
4. Give the human a small set of questions with record links and the decision
   needed. Stakeholder discussion and agreement belong to people. Record who
   answered, the answer's source, affected scope and any stated agreement;
   do not infer unanimous agreement from one answer or silence.
5. Apply confirmed answers to the question/requirement-candidate record and
   adjust investigation scope. Preserve the previous version and a trace of
   what changed. Track answer received separately from answer applied. If an
   answer conflicts with evidence or a prior decision, retain both and route
   the unresolved conflict to its owner; do not silently select one.
6. Persist the updated cycle using the
   [persistence handoff](../progress_rules_setup/references/persistence_handoff.md#xid-62A9D4E7B103).
   Repeat the smallest useful investigation until the requirement owner can
   explicitly finalize the bounded requirement set, or until a named issue
   needs human resolution. No automatic iteration count grants approval.

## Completion and handoff

For a cycle, return saved artifacts or record links, evidence/version, candidate
state, completed delivery steps, unresolved item owner and next action. If upload
or linking is unsupported, prepare the authorized attachment-ready artifact and
minimal human steps; assess delivery completion against the project's chosen
endpoint. This preparation does not change the agreed destination, format or
sharing method; route any alternative through progress_rules_setup for human
confirmation. A waiting cycle is not a finalized
requirement. For finalization, link the responsible owner's explicit decision
and exact requirement version before handing approved work to planning.
Persist remaining unknowns/holds even when another bounded part can advance.
Stop only the affected discovery, delivery or readiness claim when its required
permission, route, evidence or destination is missing. Continue independent
authorized artifact preparation and return the minimum resolving handoff.
