<!-- xid: 73E20A8D9C51 -->
<a id="xid-73E20A8D9C51"></a>

# Project Management scheduling interface

`xrefkit_skills_project_management.schedule` is an explicit local tool, independent
of Skill readiness. It does not run or promote a Skill. Use it only
for a project-authorized destination and recorded settings. JSON is authoritative;
Mermaid is a generated view. This interface is package behavior, not a replacement
for project governance, a resource optimizer or a start-condition matcher.

## Roles and data

`progress_rules_setup` establishes applicable rules and record mapping.
`requirements_discovery_coordination` maintains Decision investigation/verification
plans and decision handoffs. `work_progress_coordination` maintains Execution
observations, forecasts, baseline comparisons and affected-work/Hold coordination.
Brownfield owns technical investigation, requirement-understanding changes,
Knowledge Requirement analysis and method/migration findings. Humans retain
adoption, assignment, quality, transition and approval authority.

Requirement XIDs identify the requested behavior being traced; they are not
Knowledge references. Existing Skill `knowledge_needs` still selects applicable
project/domain Knowledge through the configured provider. A Brownfield Knowledge
Requirement records the specific question, linked Knowledge and applicability
evidence needed for the decision. The scheduler consumes the resulting trace
records; it neither resolves Knowledge truth nor invents missing project rules.

The version-1 JSON plan has required fields:

| Field | Contract |
| --- | --- |
| `schema_version` | Integer `1` |
| `plan_id`, `kind` | Stable ASCII identifier; `decision` or `execution` |
| `start`, `rules_ref` | ISO date and exact applicable rules record |
| `calendar` | `working_weekdays` (Monday=0 through Sunday=6), explicit `holidays` ISO dates |
| `tasks` | Nonempty list of the task objects below |
| `links` (optional) | Typed cross-record links; never CPM dependency edges |

Each task carries `id`, `label`, nonnegative integer working-day `duration`,
`depends_on`, `requirement_xids`, `evidence_refs`, `decision_refs`, `hold_refs`,
and `work_ref`. The four reference lists may be empty when no link is established;
absence is not evidence or approval. Requirement XIDs are twelve uppercase hex
characters. Optional `not_before` is an ISO release date. A dependency object is
`{"task":"predecessor-id","type":"FS","lag":0}`. Only finish-to-start
relationships and nonnegative integer working-day lags are supported. Unknown
tasks, duplicate IDs, cycles, unsupported fields and other dependency types refuse
calculation. Zero duration is a milestone. Do not encode unknown duration as zero.

Each optional link has `relation`, `target_ref`, `requirement_xids`,
`evidence_refs`, `decision_refs`, `hold_refs`. Relations are `requirement_change`,
`investigation`, `method_decision`, `data_migration`, `informs`, or `reopens`.
Use exact revisions in target references. Cross-plan impacts are explicit handoffs
with Holds/decisions; they never silently become local dependency edges.

## Deterministic calculation and views

`calculate(plan)` returns deterministic topological scheduling with lexicographic
task-ID tie breaking, earliest/latest start/finish, total float, all critical
tasks and tight critical edges, and finish date. Forward/backward passes use the
declared working calendar. Finish dates are exclusive working-day boundaries;
release dates on nonworking days normalize forward. All terminal tasks connect to
the common finish. Multiple critical branches are retained. Input order does not
change output. No resource leveling, probabilistic duration, negative lag,
start-to-start constraint, deadline float or cross-plan CPM is inferred.

`mermaid(plan, result)` emits a fenced Gantt view with explicit computed dates,
critical tags and zero-duration milestones. It does not ask Mermaid to recalculate
dependencies or exclusions. Labels are stripped of diagram-control characters.
The structured result and source dependencies retain details absent from the view.

`calculate(plan, snapshot)` computes a remaining-work forecast. Snapshot fields
are `as_of` and a `tasks` object covering every task ID. Each observation has
`actual_start`, `actual_finish` (ISO date or null), integer `remaining`, and
`evidence_refs`. Finished observations require actual start, zero remaining and
evidence. Unsupported pre-plan/future observations or actual starts inconsistent
with the current dependency network refuse calculation and need reconciliation.
Unfinished work starts no earlier than the observation date, declared release or
predecessor finish. Finished work is an observed boundary and is not labeled
critical remaining work. Hold impacts remain explicit; an unresolved Hold does
not acquire a guessed duration. Forecasts are conditional on the input plan and
do not prove that work can start or finish.

`compare(before_result, after_result)` reports finish movement in calendar days,
added/removed tasks, task-result differences and critical-set changes.
`compare_plans(before_plan, after_plan)` additionally retains changed dependencies,
trace fields and other structured plan changes even when the dates stay equal.
Compare a saved baseline calculation with a current plan/forecast explicitly;
the program does not select a new baseline from the latest observation.

## Immutable history

`save(root, plan, metadata, snapshot=None, baseline=False)` creates separate files:

```text
<authorized root>/
  gantt-history.json
  decision/<plan_id>/plan-r001.json
  decision/<plan_id>/gantt-r001.md
  execution/<plan_id>/plan-r001.json
  execution/<plan_id>/gantt-r001.md
  execution/<plan_id>/plan-r001-s002.json
  execution/<plan_id>/gantt-r001-s002.md
```

Revision numbers are independent per kind/plan. Each plan save adds a Revision;
observations add a Snapshot to the exact latest plan content without changing
that Revision. Each immutable JSON record contains the structured plan,
optional observations, calculation and history metadata. The index links previous
records and stores SHA-256 identities for source and view. `read_history(root)`
verifies file identities, immutable metadata, chain and current/baseline pointers
before reuse or mutation. Errors are corrected through a new Revision/Snapshot.

Metadata requires timezone-bearing `created_at`, `reason`, `requirement_xids`,
`evidence_refs`, `decision_refs`, `judgment`, and `approval`. Approval is an object
with `status` (`proposed`, `approved`, `rejected`), `actor`, `record_ref`; approved
or rejected status requires a named actor and evidence record. This records an
existing decision; the tool cannot authenticate or grant human authority.

`current` means the latest saved record, including proposals and observations.
`approved` separately points to the latest plan revision with recorded approval;
neither pointer changes project configuration automatically. `baselines` retains
all explicitly designated approved plan references. `baseline=True` refuses
observations or unapproved plans. An actual update never moves a baseline.

Cooperating writers use an exclusive lock, create-only files and one atomic index
replacement. A failed index replacement rolls back newly created files. A hard
process interruption can leave a lock or unindexed files; inspect and recover them
explicitly before retrying. Existing files are never overwritten to recover.
This is application-level immutability and drift detection, not filesystem access
control, signed audit storage or backup. An attacker replacing both index and
files is outside this local integrity model. Remote delivery/visibility is still
verified under the configured persistence handoff.

## Brownfield impact boundary

`validate_impact_notification(value)` owns the receiver contract
`brownfield.change_impact/v1`. Brownfield emits proposed data with notification
identity, source/previous revision, reason, requirement XIDs, evidence, decision
and approval references, affected task IDs, changes, Decision activities and Holds.
Changes identify `requirements`, `confirmations`, or `approach` items with before/
after records and reasons. Activities retain their Knowledge Requirement,
question, method, expected evidence, owner and decision; Holds retain reason,
resolver, next action and resolution point. The executable validator defines exact
field names/types and refuses unsupported payloads or automatic approval/resolution.

`assess_impact(plan, notification)` validates both inputs, maps explicit task IDs
and requirement XIDs, computes dependent closure, and returns unmapped references,
proposed Decision activities and Holds with trace evidence. It changes no schedule
and returns `readiness: not_evaluated`. Investigate an unmapped change instead of
calling it unaffected. Reconcile findings with Decision/Execution owners, obtain
the required decision and write a new plan Revision before adopting an impact.

## Invocation

```console
python -m xrefkit_skills_project_management.schedule plan.json
python -m xrefkit_skills_project_management.schedule plan.json --snapshot actual.json
python -m xrefkit_skills_project_management.schedule plan.json --save management --metadata change.json
```

The last command writes only to the explicit authorized local destination.
Attach `--baseline` only for a recorded approved baseline decision. For retrieval,
select an entry from `read_history`, read its source JSON and use its stored
calculation/plan for comparison. No custom UI or external service is required.
