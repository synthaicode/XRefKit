<!-- xid: 1D7A8E2C5F10 -->
<a id="xid-1D7A8E2C5F10"></a>

# OR Team Operating Model

This page defines the cross-functional OR Team for AI-organization performance maintenance and improvement.

This page defines the OR Team as an operating model.
For day-to-day use, request format, and interpretation, see [OR Team usage guide](049_or_team_usage_guide.md#xid-4E2F91A6B8C1).
For the boundary among operating models, usage guides, and design pages, see [Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583).

## Purpose

The OR Team is not a simple monitoring unit.

Its purpose is to maintain and improve AI-organization performance as a whole by operating one closed loop:

1. present current state from logs and evidence
2. identify problems and candidate improvements
3. organize approval requirements
4. execute approved OR-owned improvements or control execution by other teams
5. re-observe after change and confirm effects, side effects, and recurrence

The OR Team operates across judgment performance, execution performance, quality performance, operational performance, and improvement performance.

## Position In The Organization

- The OR Team is a cross-functional optimization function placed outside normal execution groups.
- It does not replace Planning, Design, Manufacturing, Quality, or Operations groups.
- It observes the whole system earlier and wider than product-quality review alone.
- It owns state presentation, problem structuring, intervention design, approval routing, execution control, re-observation, drift detection, and evaluation-asset maintenance.
- It does not become the default implementation owner for product changes.

## Standard Operating Flow

The OR Team must execute the following flow for normal degradation handling, drift handling, and improvement work:

1. present current state from logs
2. present problem list, cause hypotheses, and improvement options
3. organize approval requirements and operating disposition
4. execute or control approved improvements
5. re-observe after improvement

The standard AI output for OR work is always:

1. current state
2. problem list
3. cause hypotheses
4. improvement list
5. approval requirement by improvement
6. implementation method after approval
7. re-observation method after improvement
8. unresolved items

## Roles

The OR Team is composed of the following roles:

1. OR lead
2. state and baseline manager
3. problem structuring and diagnosis owner
4. improvement design owner
5. triage and approval-routing owner
6. execution-control owner
7. re-observation owner
8. drift evaluation owner
9. evaluation-asset owner
10. human-decision liaison
11. continuous-improvement owner

In small-scale introduction, roles may be combined, but the functions must remain explicit.

## Role Responsibilities

### OR Lead

- Own the OR mission and KGI.
- Approve major interventions and stop decisions.
- Resolve priority conflicts across groups.

### State And Baseline Manager

- Collect logs, deliverables, diffs, review results, rework history, escalation history, and drift-evaluation outputs.
- Present current state and baseline deviation.
- Detect anomaly signs early.

### Problem Structuring And Diagnosis Owner

- Convert symptoms into structured problems.
- Distinguish one-off incidents from trend changes.
- Separate likely causes into assumption failure, knowledge failure, procedure deviation, role mismatch, model change, connection failure, or boundary violation.

### Improvement Design Owner

- Prepare concrete improvement options for each problem.
- Attach priority, expected effect, risks, owner, recovery condition, and re-observation condition.

### Triage And Approval-Routing Owner

- Decide stop, conditional continuation, or continuation.
- Classify each improvement as OR-self-executable, owner-approval-required, or human-approval-required.

### Execution-Control Owner

- Track implementation status of approved improvements.
- Issue return instructions to the responsible team when OR is not the executor.
- Keep recovery conditions and re-observation conditions attached to each request.

### Re-Observation Owner

- Re-observe the system after change.
- Confirm effect, side effect, and recurrence.
- Recommend additional improvement or re-approval when needed.

### Drift Evaluation Owner

- Continuously evaluate expected judgment structure using baseline problem sets.
- Detect drift in structure, evidence, boundary, knowledge, and procedure.

### Evaluation-Asset Owner

- Maintain fixed problems, semi-fixed problems, and incident-reproduction problems.
- Maintain skeletal model answers and scoring rubrics.

### Human-Decision Liaison

- Route human approval items.
- Record approval outcomes and reflect them into OR assets and operating rules.

### Continuous-Improvement Owner

- Analyze incidents, returns, rework, and performance decline.
- Update rules, assets, thresholds, and observation points.

## Minimum Required Observation Data

The OR Team requires a minimum common evidence set for every observed case:

1. case ID
2. input request ID
3. knowledge reference ID
4. rule ID used
5. output ID
6. output revision
7. human return flag
8. escalation flag
9. rework count
10. model name and version
11. execution timestamp

Recommended additional fields:

1. AI role ID
2. applied procedure ID
3. review result
4. unresolved-item flag
5. business impact class
6. final operating status

Missing required evidence is itself treated as an operational problem.

## State Presentation Mechanism

State presentation must always show:

1. current state summary
2. deviation from baseline
3. anomaly signs
4. impact scope
5. supporting evidence
6. provisional trend or one-off assessment

State presentation consumes:

- logs
- deliverables
- diffs
- review outputs
- management rows
- test results
- rework history
- escalation history
- drift evaluation results

## Problem And Improvement Mechanism

Problems must be tracked as structured items, not raw symptoms.

Standard problem categories:

1. assumption failure
2. knowledge failure
3. procedure deviation
4. role-allocation mismatch
5. model change effect
6. connection failure
7. boundary violation
8. evidence weakness
9. unresolved-item handling failure

Each problem should have:

- problem ID
- title
- description
- category
- impact scope
- severity
- trend or one-off classification

Each cause hypothesis should have:

- hypothesis ID
- target problem
- hypothesis description
- evidence
- confidence
- additional-check requirement

## Improvement Management

Each improvement must be managed with at least:

1. improvement ID
2. target problem
3. cause hypothesis
4. improvement content
5. executor
6. approval requirement
7. approver
8. priority
9. expected effect
10. risk
11. recovery condition
12. re-observation condition
13. implementation status
14. implementation result
15. unresolved items

An improvement is invalid if recovery condition or re-observation condition is missing.

## Approval Routing And Operating Disposition

Approval classes are fixed:

1. OR self-executable
2. responsible-group approval required
3. human approval required

The operating disposition classes are fixed:

1. stop
2. conditional continuation
3. continuation allowed

### Stop Conditions

Use `stop` when one or more of the following is true:

- boundary consistency is broken
- AI self-completed a case that required human approval
- major drift affects high-impact work
- required local-rule reference is missing
- major drift exists and no alternative control can absorb it

### Conditional Continuation Conditions

Use `conditional continuation` when:

- drift is serious but can be absorbed temporarily by stronger review
- drift is light but recurring
- the issue is light in isolation but affects high-impact work

### Continuation Allowed Conditions

Use `continuation allowed` when:

- structure, boundary, knowledge, and procedure remain aligned
- only minor evidence-record weakness exists
- the event is one-off and non-reproducible

The order of decision priority is:

1. boundary violation
2. business impact
3. drift severity
4. availability of alternative control
5. trend versus one-off

## Execution And Execution Control

Only approved improvements may move to implementation.

The OR Team may execute changes inside its own boundary, such as:

- monitoring settings
- evaluation assets
- thresholds
- light operating-rule updates
- intervention conditions
- dashboards
- test items

When another team must execute the change, the OR Team returns an implementation request that includes:

1. executor
2. improvement ID
3. target problem
4. requested change
5. evidence and rationale
6. approver
7. confirmation points
8. update target
9. recovery condition
10. re-observation condition
11. due date
12. risk if not executed

Implementation status must be managed with:

- not_started
- pending_approval
- in_progress
- completed
- returned
- on_hold

`completed` does not mean closed. Closure requires re-observation completion.

## Re-Observation

Re-observation must confirm:

1. baseline deviation reduction
2. anomaly suppression or removal
3. release from conditional continuation when applicable
4. side effects
5. recurrence
6. before-after comparison result

Re-observation records should include:

- re-observation ID
- target improvement ID
- observation target
- metrics
- observation period
- judgment criteria
- side-effect checks
- recurrence checks

## Drift Detection

Drift means deviation from expected judgment structure, not just model-update detection.

Continuous evaluation must compare:

1. structure consistency
2. evidence consistency
3. boundary consistency
4. knowledge consistency
5. procedure consistency

Drift classes:

1. minor variation
2. caution drift
3. major drift

Major drift must trigger intervention even before visible product failure if impact is meaningful.

## Evaluation Assets

Required asset types:

1. fixed problems
2. semi-fixed problems
3. incident-reproduction problems

Model answers must be skeletal, not exact wording, and must include:

1. required assumptions
2. required viewpoints
3. required evidence
4. prohibited judgments
5. acceptable alternative judgments
6. escalation conditions
7. unresolved items that must remain explicit
8. required local-rule references
9. required procedure order

Approval split for evaluation assets:

- OR Team:
  - draft problems
  - draft skeletal answers
  - maintain scoring rules
- business owner:
  - approve prohibited judgments
  - approve approval boundaries
  - approve business validity
- human-decision liaison:
  - control approval reflection and version issue

## KPI And KGI

### KGI

- major degradation detected before business damage
- major incident rate reduced
- recurrence rate reduced
- post-update stabilization period shortened

### KPI

1. anomaly detection lead time
2. state-presentation lead time
3. problem-structuring lead time
4. approval-routing lead time
5. time to improvement start
6. recovery lead time
7. drift evaluation execution rate
8. major drift miss rate
9. return rate
10. rework rate
11. escalation appropriateness rate
12. unresolved-item explicitness rate
13. evidence-record completeness rate
14. incident-reproduction detection rate
15. evaluation-asset refresh count
16. post-model-update stabilization period

## Main Outputs

1. state-presentation report
2. baseline deviation table
3. anomaly list
4. problem list
5. cause-hypothesis list
6. improvement list
7. approval-routing sheet
8. implementation request
9. implementation tracking record
10. recovery confirmation sheet
11. re-observation report
12. drift evaluation report
13. evaluation-asset register
14. skeletal answer set
15. scoring rubric
16. unresolved-item register
17. KPI and KGI report

## Connection With Other Groups

- Planning Group:
  - return requirement ambiguity, assumption gaps, and approval-boundary gaps
- Design Group:
  - return sequencing, role-allocation, local-rule reference, and escalation-boundary design issues
- Manufacturing Group:
  - return procedure deviation, omission, implementation-scope leaks, and execution gaps
- Quality Group:
  - consume review findings and closure findings as observation inputs
  - avoid replacing product-quality judgment
- Operations Group:
  - consume readiness, monitoring, and event-response evidence as operating-state inputs
- Human decision layer:
  - receive stop decisions, boundary changes, business-risk decisions, and major approvals

## Related

- [Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583)
- [Group definitions](040_group_definitions.md#xid-8B31F02A4009)
- [Flow-to-group matrix](041_flow_to_group_matrix.md#xid-8B31F02A4010)
- [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012)
- [OR Team usage guide](049_or_team_usage_guide.md#xid-4E2F91A6B8C1)
