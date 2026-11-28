---
schema_version: 1
skill_id: work_progress_coordination
xid: A4D902C7E651
summary: coordinate multiple contributors from confirmed start conditions, current recorded work and separate quality decisions
applies_when:
- contributors share a goal and need evidence-linked guidance on who can do what next, including bounded overlap between stages
exclusions:
- quality or integration verification, acceptance decisions, automatic assignment or priority changes, external message sending, remote adapter implementation, and completion inferred from percentages
inputs:
- confirmed progress rules and authoritative record mapping, shared goal and bounded plan, current task and artifact revisions, new requests, versioned benefit and risk records, issue and change decisions, start and exit conditions, investigation and quality evidence, holds, and designated decisions
outputs:
- current-state evidence and scope assessments, persisted dependency and condition assessments, change decisions, plan revisions and affected-work reassessments, investigation items and scoped results, separate quality definitions and confirmation plans, WBS hierarchy and separate dependencies, discovered-subtask registrations, human interaction records and notices, focused SubAgent review evidence, linked holds and owner actions, and resumable coordination handoff
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
- id: plan_revision_boundary
  statement: Plan generation, execution and replanning use distinct checks; retained results and repeated exceptions have an evidence basis.
  verification: Trace the authorized goal, affected ancestor, recurrence assessment, evidence applicability and proposed revision separately from Runtime transitions.
- id: request_and_investigation_trace
  statement: Initial and changed work resolve unknowns through the same scoped investigation record, and actual task changes produce an informational notice.
  verification: Trace requests, decision and plan revisions, investigation IDs and applicable evidence, and notices through the configured owners and delivery route.
- id: quality_confirmation_plan
  statement: Confirmation preserves condition coverage and required independence, with eligible plans ranked by human interaction burden, cost, then elapsed time.
  verification: Trace each applicable condition to current evidence or a planned owner check, and compare the selected plan against eligible alternatives and their estimates.
- id: wbs_and_interaction_trace
  statement: WBS hierarchy and execution dependencies remain independently traceable, and human interactions and discovered subtasks are tracked through actual reflection.
  verification: Inspect stable IDs, parent and dependency links, attributable interaction results, origin evidence, completion effects, approved revisions and actual reflection.
- id: focused_subagent_review
  statement: Material plan decisions receive focused SubAgent review and retain the PM integration, decision, and quality ownership boundaries.
  verification: Trace the trigger, review scope, evidence and affected IDs, disposition or handoff, and separate authorization and verification results.
- id: decision_to_execution_trace
  statement: Benefit, risk and change records inform scoped reassessment and only authorized changes become reflected plan revisions.
  verification: Trace source revisions, authorized disposition and authority, impacted priorities, conditions and dependencies, applicable review or holds, and any reflected plan change and notice.
- id: current_state_and_scope
  statement: A bounded survey grounds scope and verification in existing implementation and current, applicable evidence.
  verification: Trace provisional criteria through observed call paths, versions and covered cases to retained evidence, changed or integration work, and explicit gaps.
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

Public trial source. Select the matching external record at
`governance/skills/work_progress_coordination.json` for readiness or a run. Trial
uses an authoring/readiness observation, not operational validation. Preserve
project-specific prerequisites and human authority; publication is not adoption.

## Startup and preparation

Read applicable rules and the latest designated management records, not only
chat or local cached summaries. Capture the selected plan and observation
revisions, deliverable versions, quality decision sources and unresolved holds.
If rules are missing, route to
`progress_rules_setup` (XID `91F7D3B6A204`).

## Plan generation

1. Record the confirmed goal, final deliverables, governing acceptance
   criteria and constraints against the current plan revision. Return any
   unconfirmed governing decision to the designated owner. Derive provisional
   work-level quality criteria from those inputs.
2. Apply the bounded current-state survey before finalizing work scope,
   work-level quality criteria, or the verification plan. Use its findings
   to identify necessary work and preserve the agreed goal and constraints.
3. Derive only subordinate goals needed to satisfy the parent criteria. Link
   each to the criteria it supports. Keep unresolved implementation methods at
   goal level, with the decision or investigation needed to refine them; do
   not present them as executable tasks. For approved software requirements,
   consume the approved breakdown or route to `planning_flow` (XID
   `6A4F8C2D1E71`) under its own readiness conditions.
4. For executable tasks, record the parent goal, output, dependencies, start
   and exit conditions, verification method and owner, and the discretion
   granted to the executor. Record evidence required at each gate. Keep
   proposed assignment, priority and plan changes separate from the
   authorized plan.
5. Separate executable tasks when differences in outputs, ownership, start
   or exit conditions warrant advancing, holding or retrying them
   independently. Split at the boundary where a result can be verified and
   acted on independently. Task size alone does not determine that boundary.
6. Record a stable task ID, WBS number and direct parent ID (or its root
   designation). Use the parent links to build the WBS hierarchy in the
   available view. Where deeper nesting is unavailable, show an indented
   list or full numbered path while preserving the direct parent link.
   Preserve identity across revisions and record any display renumbering or
   reparenting. Record dependencies and actual execution order separately.
   A parent link, sibling order or WBS number does not establish readiness
   or a predecessor.

## Bounded current-state survey

Read the actual implementation, entry and call paths, and relevant versions.
Check existing fixtures, tests and recorded verification for their inputs,
environment, path and scope. Limit the survey to the paths, interfaces and
evidence that can affect the provisional criteria or the proposed change.
Classify each relevant criterion as already supported within the verified
scope, requiring changed or integration work, or unverified. Record the
source revisions, observed path and applicable evidence for each assessment.

Reuse current evidence only within its verified scope. Separate observing an
existing component or reproducing an existing path from building new
behavior and verifying a changed or integrated path. Route material evidence
gaps through the shared investigation process. Repeat the affected part of
the survey when a change alters an existing boundary or evidence may no
longer apply, before firming the revised scope, criteria or checks. Route
decisions requiring authority to the designated owner through existing rules.

## Investigation in initial and changed work

For each unknown that affects a decision, plan or task, use the same
investigation record during initial planning and later changes. Record an
investigation item ID, the question and decision it informs, affected
goal/task and revision, what scope and input versions the evidence must
cover, the required result, and the responsible owner. Look up the question
and scope in the current records. Link applicable evidence and its scope
to the item, including partial coverage. If an equivalent investigation
is pending, link it and update or route its uncovered scope through its
owner instead of adding duplicate work. If neither applicable evidence nor
pending work covers a gap, propose a bounded investigation task for that
gap. Add it through the authorized plan route and record start, exit and
verification conditions. Keep unresolved parts explicit and use the
existing uncertainty and decision routes for holds, findings and resolution.
Batch related investigations where they can share execution. Keep separate
item IDs, findings and evidence scope for each question.

## Execution rules (coordination cycle)

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
   checks remain with `brownfield_workflow` (XID `E1A7C4D9B260`) or the applicable quality route. Do not repeat their checks or reinterpret their acceptance.
6. Explain the recorded current state, what can advance within authority, next
   person/action, and what needs a decision. Do not authorize a start, approve
   completion, change an assignee or reprioritize beyond granted authority.
   Persist actual results, answers, hold updates and proposals through the
   [persistence handoff](../progress_rules_setup/references/persistence_handoff.md#xid-62A9D4E7B103).
7. When input artifacts or decisions change, identify affected assessments and
   request the appropriate owner to revalidate them. Preserve old evidence;
   do not erase completion history or assume that an old quality result covers
   changed artifacts. Refresh authoritative state before the next guidance.

Before recommending completion or a dependent transition, match the recorded
exit conditions against current results and required owner verification. A
recorded finish, recommendation or forecast does not satisfy an exit condition.
Keep missing, stale or failed results explicit and route them to their owner.

## Quality definition and confirmation

1. Record the applicable quality conditions for the task or transition, their
   scope, revisions, required evidence, and verification or quality owner.
   Use the confirmed conditions and independence requirements. Route missing
   or changed conditions to their designated decision or quality owner.
2. Build a separate confirmation plan. Map every applicable condition to
   current evidence covering its scope and version, or to a specific
   confirmation action and owner for the uncovered part. Mark pending,
   stale and failed coverage explicitly. Link evidence to multiple
   conditions, or combine checks, when the evidence remains applicable to
   each condition and the combination preserves required scope and checker
   independence.
3. Compare only plans that satisfy the coverage, independence and authority
   requirements. Prefer lower human interaction burden first, then lower
   cost among equally burdensome alternatives, then shorter elapsed time
   among remaining ties. Record the basis for each comparison, such as
   participant effort and coordination exchanges, and flag estimates or
   unknowns. Reuse current applicable answers and batch related questions
   to the same owner when their timing, scope and authority allow it. When an unknown prevents ranking, record the gap and route the
   choice to the designated owner. Keep planned confirmation actions
   distinct from evidence received. Collect or request checks through the
   existing routes and leave the quality judgment with its owner.
4. Once confirmation results arrive, reconcile every applicable condition
   against current authoritative evidence and record the final coverage.
   Distinguish missing or stale evidence from an applicable result that
   failed. Request the missing or refreshed checks and route failures to
   the designated owner. Recommend a transition only when the required
   evidence, owner decisions and existing gates are satisfied.

## Human interactions

Register each required human interaction as a separately trackable task when
its timing, owner, result or dependency can differ. Record a stable task ID,
trigger, actual
predecessor or entry condition, responsible person or role, expected and
recorded result, successor or affected task, and whether a reply or an
explicit decision is required. Record the applicable hold or release
condition and retain the answer, decision or delivery evidence. Group
compatible questions into one contact when appropriate, while keeping each
question's result and any outstanding dependency traceable.

Use the existing decision and quality routes for responses requiring
authority or verification. Record informational notices through the
configured channel or sender handoff. For a task-change notice, link the
notice task to the actual plan reflection that triggers it. An informational
notice has no reply or agreement gate. Any independent task gate still applies.

## Discovered subtasks

When an execution result reveals an independently verifiable unit of work,
record the origin result and its revision, the direct parent and criterion
served, and the newly needed output. Check current evidence and equivalent
open work first. Reuse applicable results or link existing work. For any
remaining gap, define only the new subtask needed, with start and exit
conditions, verification method and owner, and authorized discretion.
Record the dependency changes and whether the parent's existing completion
criteria require this result. Route proposed changes to criteria or
authority to the designated owner.

Register the subtask incrementally using the next authorized plan revision,
with its stable ID, WBS number, direct parent, dependency records and origin
evidence. Keep proposal and actual reflection traceable, then issue the
task-change notice through the existing route. Reassess affected readiness
and parent completion against the reflected revision.

## New requests and task-change notices

During execution, record a new request against the current plan and assess
its effect on goals, constraints, dependencies, work, quality conditions
and evidence. Route unresolved facts to the common investigation process.
Work within recorded discretion when granted. Route other decisions to the
designated owner through `pm_decision_coordination` (XID `C8E4A1D760B3`)
or the project's applicable decision route. Use the replanning rules when
task definitions must change. Track the request, decision and rationale,
affected tasks, plan revisions, and actual reflection separately.

After a task is added, modified or withdrawn in the authoritative plan,
look up the notice by actual reflected change, effective plan revision and
affected audience. All entry routes and resumed work use this same lookup.
Reuse the existing record, including confirmed delivery evidence or a
pending sender handoff. If delivery is uncertain, reconcile it with the
configured route or responsible sender before retrying. Create a notice
record only if none covers that change, revision and audience, then route
the notice through the configured delivery path or responsible sender.
Include the change and its reason, affected tasks, effective revision and
practical effect. A notice requires no reply or agreement. Existing
approval, hold and quality conditions continue to apply.

## Apply decisions and reassess affected work

Consume current, versioned and attributable benefit observations, risk
records, actual issues and decisions from `pm_decision_coordination`
(XID `C8E4A1D760B3`) or the configured owner. Check the source revision,
scope, trigger or observation, authority, and effective conditions. Assess
whether a benefit deviation, new or met risk trigger, actual issue or
authorized change affects priorities, start or completion conditions,
dependencies, capacity, or evidence coverage. Route material gaps or stale
records to the owner. If the counterpart route or required record is
unavailable, record the gap and use the configured owner handoff. Keep
dependent authorization and gates open pending applicable evidence. Use investigation, focused SubAgent review and holds
where their existing rules apply. Scope holds to the affected work and
dependent transitions. Continue authorized work with satisfied gates.

Record recommended changes and affected work against the current baseline.
Before reflecting a change, compare the attributable decision ID and version
with the current authoritative decision record. Verify its scope, authority
and baseline mapping against the current authoritative plan or baseline.
Confirm that the decision's disposition explicitly authorizes the proposed
change. Record pending, declined, deferred, or otherwise non-authorizing
dispositions and withhold their proposed changes, including when the
coordinator can ordinarily edit the plan. Check the latest applicable evidence
for each effective condition. Approval can be recorded before it becomes
effective. Keep conditional approvals whose conditions are unmet or
unverified, and decisions that are stale, superseded, or based on an outdated
baseline, on record without reflecting their changes.
Reassess impacts against the current baseline, repeat the affected survey
when evidence or existing boundaries change, and seek missing evidence or
refreshed authority from the designated owner as applicable. Record the exact
dependent transitions on hold and continue unaffected authorized work.

When the current, applicable decision authorizes the change, its effective
conditions are verified, and existing gates are satisfied, reflect the change
within granted authority through the existing plan route. Link the decision and evidence,
changed WBS entries, impacts on priorities, dependencies and conditions, and
any downstream reassessment or verification to the authorized revision.
Record actual reflection and use the common notice lookup. Keep observations,
proposals, decisions and reflected revisions separately linked.

## Exception handling and replanning

1. Compare unexpected events with the current task conditions, dependencies,
   goal and constraints. Propose local response only within existing
   discretion and where dependencies, verification coverage and acceptance
   criteria remain valid. Keep affected work on hold through the existing
   route when impact cannot be established, and identify the resolving owner.
2. When similar events recur, stop treating them as independent fixes. Group
   them by observed failure pattern, affected dependency or verification gap.
   Reassess classification, potential common cause, verification method and
   coverage, and the adequacy of the task breakdown. Record what is known and
   route remaining questions through the shared investigation process. Record
   a supported cause separately from a hypothesis based on similarity. Resume
   affected work only through normal conditions and authority.
3. Identify goals and tasks whose definitions must change, including any
   required changes to downstream dependencies, work or exit conditions.
   Re-decompose at the lowest ancestor covering those changes. When changes
   span branches owned by different plans, record a coordination handoff to
   the designated owners with affected definitions and dependencies.
   Reassess readiness and evidence for downstream tasks whose definitions
   still apply without expanding the decomposition to those tasks. Follow
   the confirmed goal, criteria and constraints. Route any proposed change
   to them to the designated decision owner.
4. Preserve prior records and review result reuse individually. Record the
   basis for reuse within the original evidence scope by checking the result
   against current scope, input and artifact revisions, criteria, dependencies
   and owner evidence. Ask the designated verification or quality owner to
   determine applicability or revalidate when a change in those inputs,
   scope, dependencies or criteria leaves coverage uncertain. Keep the old
   result in history and hold carry-forward until the owner's applicable
   result is recorded. Record the old and proposed revisions, impact, retained
   evidence, evidence requiring revalidation and next owner.

## Focused SubAgent review

Before advancing an initial plan decision or proposed plan change, identify
whether it introduces or changes any of these material dependencies or risks:

- Plan and dependencies, including effects across branches, on dependent
  task readiness, or on parent completion.
- Quality evidence, including changed verification coverage or reliance on
  disputed or stale evidence.
- Human interactions, including a dependency on a human decision, a hold or
  release condition, or delivery under the existing rules.

A routine informational notice alone does not require review. Its delivery
is reviewed only when the plan introduces or changes a material dependency
on that delivery. The notice retains its no-reply and no-agreement rule.
Routine work with no applicable trigger uses the ordinary checks.

Record each applicable review question and start with one qualified,
independent reviewer. That reviewer may cover multiple questions if
competence, scope and required independence allow it. Add another reviewer
only when competence, required independence or a distinct focus makes it
necessary. Account for each applicable question by linking the result and
recording its disposition. Keep any required question without an applicable
answer unresolved.

Use the existing workflow binding for dispatch. A delegated PM coordinator
requests independent dispatch through the main agent or host under the
Skill Operating Contract (XID `B7A2C94F0E61`). Give each reviewer the plan
revision, proposal, relevant criteria, evidence and XIDs, and the assigned
questions. Request findings, evidence links and affected goal, task or
interaction IDs. Bind actual results to the exact reviewed revision and
proposal. Request a fresh review when reviewed inputs change.

When a required review is unavailable, partial, or conflicting, record the
open questions and evidence, and use the existing hold and handoff route to
the designated owner. Name the exact dependent transitions on hold, including
plan approval or reflection, integration or merge, parent completion, or
closure of the affected work wherever they depend on the unresolved question.
Continue unrelated authorized work whose gates are satisfied. A coordination
handoff records the unresolved work and its owner. Apply ordinary Skill-run
verification and close separately. Record a review as performed only when
an actual result exists.

The PM integrates the findings and records disposition before advancing each
dependent transition. Deterministic checks, designated independent quality
acceptance and authorization retain their existing procedures and owners.

## Runtime handoff

Record the recommendation with the plan revision, affected goals and tasks,
condition results, evidence references, outstanding holds and decisions, and
the requested next action. Link any investigation IDs, quality condition
coverage, interaction results, discovered subtasks and task-change notices
and applicable SubAgent review findings and disposition relevant to the
transition. The Skill owns this judgment; the existing decision
and quality owners retain their authority. Runtime owns deterministic
state-transition enforcement where a supported operation exists. It checks
current revisions, required condition results and applicable authorization,
and does not transition on absent, stale or conflicting inputs. This method
does not define status values, implement a matcher, or treat a recommendation
as permission to transition. Where no supported control exists, keep the gap
and the authorized handoff explicit.

## Execution forecast, baselines and impact

For configured scheduling, use the scheduling interface (XID `73E20A8D9C51`)
with the current structured Execution plan and separately recorded actual-start,
actual-finish, remaining-duration and evidence observations. Preserve the exact
approved baseline reference. A progress observation does not revise the plan or
baseline; a scope, estimate or dependency change requires a new immutable plan
revision with its reason, requirement XIDs, Evidence, judgment and approval.

Report independently calculated planned and remaining-work CPM results, all
critical branches and float, then compare against the selected baseline. Explain
calendar/dependency assumptions and retained Holds. A computed date, critical
flag, zero remaining duration or recorded actual finish grants no readiness,
quality or completion approval; continue the existing condition/quality-owner
checks above. A scheduler result is not the start-condition matcher.

Consume Brownfield impact notifications through the receiver's deterministic
assessment. Show directly mapped work, dependent work, unmapped requirement/task
references, proposed Decision activities and Holds. Return unmapped or unclear
impact to its owner, not as clearance. Route requirement-understanding changes,
investigation results, method decisions and data-migration findings to their
exact records. A Decision delay does not automatically move Execution dates:
record the impact/Hold, obtain the responsible decision, then persist a reviewed
Execution revision. Preserve actual and quality evidence from earlier revisions.

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
