---
schema_version: 1
skill_id: work_progress_coordination
xid: A4D902C7E651
summary: coordinate multiple contributors from confirmed start conditions, current recorded work and separate quality decisions
applies_when:
- contributors share a goal and need evidence-linked guidance on who can do what next, including bounded overlap between stages
exclusions:
- quality or integration verification, acceptance decisions, automatic assignment or priority changes, remote adapter implementation, and completion inferred from percentages
inputs:
- confirmed progress rules and authoritative record mapping, shared goal and bounded plan, current task and artifact revisions, start conditions, holds, and designated quality-owner decisions
outputs:
- persisted dependency and start-condition assessments, linked holds and owner actions, proposed next steps, separate quality-result references, and resumable coordination handoff
criteria:
- id: scoped_readiness
  statement: Each suggested start is tied to a specific prerequisite slice, confirmed artifacts and conditions rather than whole-stage percentage or completion approval.
  verification: Trace each next-step recommendation to scoped confirmed inputs and the deterministic condition result.
- id: quality_boundary
  statement: The coordinator consumes applicable quality-owner decisions without performing or replacing quality or integration acceptance.
  verification: Inspect decision source, scope, versions and unresolved or absent judgments; ensure the coordinator does not issue a quality verdict.
- id: holds_and_combination
  statement: Holds retain impact, resolver and required resolution point; combining work requires no applicable unresolved holds and the required quality results.
  verification: Compare each combination scope with current hold links, deadlines and quality-result coverage.
- id: current_persistence
  statement: Guidance comes from current authoritative artifacts or records and updates follow the configured delivery endpoint with evidence of completed steps and explicit remaining actions.
  verification: Inspect source revisions, update outcomes, record links and restart instructions.
knowledge_needs:
- id: project_progress_rules
  query: selected project work state start transition rules roles dependencies holds quality owners record destinations authorized operations
  required_when: Required before interpreting state, recommending start or transition, or recording updates.
  seed_xids: []
control_refs: []
---
<!-- xid: A4D902C7E651 -->
<a id="xid-A4D902C7E651"></a>

# Skill: work_progress_coordination

Public draft source. Select the matching external record at
`governance/skills/work_progress_coordination.json` when checking readiness or
opening a run; do not omit draft governance to obtain an unassessed run.
Publication placement does not grant execution, adoption or trial maturity.

## Startup and preparation

Read applicable rules and the latest designated management records, not only
chat or local cached summaries. Capture the selected plan and observation
revisions, deliverable versions, quality decision sources and unresolved holds.
If rules are missing, route to
[progress_rules_setup](../progress_rules_setup/SKILL.v1.md#xid-91F7D3B6A204).

Map the shared goal to proposed bounded work, responsible people, dependencies
and outputs. For approved software requirements use `planning_flow` (XID
`6A4F8C2D1E71`) under its own readiness conditions; consume an existing approved
breakdown when available. This coordinator does not approve scope or duplicate
planning policy. Keep proposed assignment/priority changes distinct from the
current authorized plan until the designated human confirms them.

## Coordination cycle

1. For each potential next task, link its start conditions to the exact
   prerequisite part: confirmed fact or contract, artifact version,
   confirmation source, applicable quality result and decision owner. Keep
   whole-stage completion and the permission to start one bounded task as
   separate records. WBS completion or a percentage is not a substitute.
2. Use the project's supported deterministic program to aggregate and match
   explicit conditions. Preserve input revisions, rule/version, output and
   unmet/missing conditions. The AI explains that result and proposes next
   actions; it does not silently perform the matching as an undocumented
   judgment. If no such operation exists for the configured conditions,
   record a tooling gap and hand it to the appropriate tooling owner/Skill;
   do not claim an executable matcher or infer a pass.
3. A later task may start for a bounded slice when its confirmed prerequisites
   satisfy the recorded conditions, even if the preceding stage is incomplete.
   For example, a confirmed API input/output contract may support downstream
   work on that interface; the actual project conditions still decide scope.
   This is not approval of the whole stage, all requirements, or integration.
4. Keep every remaining hold separately linked to affected tasks/artifacts:
   content, impact, resolver, next action, and the point by which it must be
   resolved (specific combination or stage, plus date if configured). A start
   recommendation must show which holds remain and why they do not block that
   bounded start under the recorded rules. Unclear impact is not clearance.
5. At a proposed combination or stage transition, match the exact combined
   scope against holds and the required quality results. Any applicable
   unresolved hold, missing result, failed result, stale version or uncovered
   scope prevents a readiness claim. Request the responsible quality Skill or
   owner to verify or revalidate. Technical consistency and integrated behavior
   checks remain with [brownfield_workflow](https://github.com/synthaicode/XRefKit/blob/main/skills/brownfield-workflow/SKILL.v1.md#xid-E1A7C4D9B260) or the applicable
   quality route. Do not repeat their checks or reinterpret their acceptance.
6. Explain the recorded current state, what can advance within authority, next
   person/action, and what needs a decision. Do not authorize a start, approve
   completion, change an assignee or reprioritize beyond granted authority.
   Persist actual results, answers, hold updates and proposals through the
   [persistence handoff](../progress_rules_setup/references/persistence_handoff.md#xid-62A9D4E7B103).
7. When input artifacts or decisions change, identify affected assessments and
   request the appropriate owner to revalidate them. Preserve old evidence;
   do not erase completion history or assume that an old quality result covers
   changed artifacts. Refresh authoritative state before the next guidance.

## Completion and handoff

A coordination cycle finishes with the configured saved artifacts/record links
or explicit delivery-gap handoff, scoped condition results, quality references, remaining
holds and next responsible people. It does not certify product quality or
project completion. On restart reload those designated records and compare
their revisions before resuming. Stop the affected recommendation on missing
authority, ambiguous dependencies, conflicting current state, missing condition
evaluation, or missing quality coverage; retain the concrete resolving action.
Missing upload/link capability does not prevent authorized preparation of the
progress report or attachment-ready file. Report file creation, designated save,
upload/link registration, human handoff and confirmed team visibility separately;
use the project's actual endpoint and evidence rules to judge delivery completion.
Do not substitute Markdown, attachment or another method for the confirmed
settings. Return a proposed setting change to progress_rules_setup and its human
confirmation owner; provisional artifact preparation is not adoption of that change.
