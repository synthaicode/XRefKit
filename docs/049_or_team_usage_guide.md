<!-- xid: 4E2F91A6B8C1 -->
<a id="xid-4E2F91A6B8C1"></a>

# OR Team Usage Guide

This page explains how to use the OR Team in day-to-day AI-organization operation.

## Purpose

Use the OR Team when you need more than a local fix.

The OR Team is the cross-functional operating loop that:

1. presents current state from evidence
2. structures problems and cause hypotheses
3. proposes improvements
4. separates approval requirements
5. executes OR-owned changes or controls execution by the responsible group
6. re-observes after change

## When To Use The OR Team

Use the OR Team in the following situations:

1. return rate or rework rate increases
2. output tendency changes after model update
3. local-rule reference omission is suspected
4. escalation boundary behavior changes
5. unresolved items are no longer preserved explicitly
6. recurring defects appear across cycles
7. you need a stop versus continuation decision for high-impact work
8. you want to convert incidents into drift-detection assets

Do not use the OR Team as a substitute for normal execution work inside Planning, Design, Manufacturing, Quality, or Operations.

## What To Prepare Before Requesting OR

Prepare at least the following evidence set:

1. target scope:
   - business area, workflow, case set, or model-update window
2. minimum required observation data:
   - case ID
   - input request ID
   - knowledge reference ID
   - rule ID used
   - output revision
   - human return flag
   - escalation flag
   - rework count
   - model name and version
   - execution timestamp
3. supporting evidence:
   - deliverables
   - diffs
   - review results
   - test results
   - rework history
   - escalation history
   - drift-evaluation outputs if available
4. baseline reference:
   - normal return rate
   - normal rework rate
   - normal escalation behavior
   - normal drift-evaluation pattern
5. operating constraints:
   - whether the target is high-impact work
   - whether human approval is required for stop decisions
   - whether alternative controls exist

If minimum observation data is missing, the OR Team will treat that gap as part of the problem set.

## How To Request The OR Team

Every request should define:

1. target
2. purpose
3. input evidence
4. expected output
5. operating constraints

Recommended request format:

```text
Target:
- High-impact business area A
- cases from 2026-03-20 to 2026-03-29

Purpose:
- determine whether post-update performance degradation exists
- decide whether stop, conditional continuation, or continuation allowed is appropriate

Input evidence:
- case logs
- review findings
- diffs
- rework history
- drift-evaluation results

Expected output:
- current state
- problem list
- cause hypotheses
- improvement list
- approval requirements
- implementation method
- re-observation method
- unresolved items

Constraints:
- stop decisions require human approval
- target is high-impact work
```

## What The OR Team Returns

The OR Team must always return the following sections in this order:

1. current state
2. problem list
3. cause hypotheses
4. improvement list
5. approval requirement by improvement
6. implementation method after approval
7. re-observation method after improvement
8. unresolved items

This output order is fixed because the OR Team must close the full loop from observation to re-observation.

## How To Read The Output

### Current State

Use this section to confirm:

- what changed from baseline
- whether the issue is local or systemic
- which workflows, cases, and groups are affected

### Problem List

Use this section to confirm:

- whether the issue is assumption failure, knowledge failure, procedure deviation, role mismatch, model change effect, connection failure, or boundary violation
- whether the issue is one-off or trend-based

### Cause Hypotheses

Use this section to confirm:

- what the likely cause is
- what evidence supports the hypothesis
- what still needs confirmation

### Improvement List

Use this section to decide what should happen next.

The improvement list is a management table, not free text.
Each row must contain at least:

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

### Approval Requirement By Improvement

Use this section to separate:

1. OR self-executable changes
2. responsible-group approval required changes
3. human approval required changes

### Implementation Method After Approval

Use this section to confirm:

- who executes the change
- whether OR executes or only controls execution
- what due date and confirmation points apply

### Re-Observation Method After Improvement

Use this section to confirm:

- which metrics will be observed
- how long observation continues
- what counts as recovery
- what side effects must be checked

### Unresolved Items

Use this section to confirm:

- what is still uncertain
- who must decide next
- what additional information is required

## How To Act On The Output

Use the following sequence:

1. review the current-state section and confirm impact scope
2. review the problem list and cause hypotheses
3. prioritize the improvement list, starting from highest priority
4. route approval-required items to the right approver
5. execute only approved items
6. track implementation status until completed
7. keep the case open until re-observation is completed

Do not close the case when implementation ends.
Close it only after re-observation confirms recovery or stable conditional continuation.

## What OR Executes Directly

The OR Team may directly update:

1. monitoring settings
2. thresholds
3. dashboards
4. evaluation assets
5. drift-detection problem sets
6. intervention conditions
7. light OR-owned operating rules

## What OR Returns To Other Groups

The OR Team returns execution to other groups when the change belongs to their responsibility boundary.

Typical examples:

- Planning Group:
  - requirement clarification
  - assumption framing correction
- Design Group:
  - sequencing fix
  - role-boundary fix
  - local-rule reference design fix
- Manufacturing Group:
  - implementation correction
  - execution-step correction
  - omission correction
- Quality Group:
  - review-viewpoint correction
  - evidence-check strengthening
- Operations Group:
  - monitoring-definition correction
  - readiness-response correction

When OR returns work, it must attach:

1. executor
2. requested change
3. rationale
4. recovery condition
5. re-observation condition
6. due date

## Daily, Weekly, Monthly Use

### Daily

- present current state
- detect anomaly signs
- open OR handling when thresholds are crossed

### Weekly

- review structured problems
- review improvement list and approval routing
- confirm implementation progress and blocked items

### Monthly

- review drift-evaluation results
- update evaluation assets
- review recurrence and continuous-improvement themes

## Stop, Conditional Continuation, Continuation Allowed

Use the OR Team to obtain an explicit operating disposition.

- `stop`:
  - use when boundary violation exists, required human approval was bypassed, major drift affects high-impact work, or required local-rule reference is missing without alternative control
- `conditional continuation`:
  - use when temporary controls can absorb the issue, or when the issue is light but recurring or affects high-impact work
- `continuation allowed`:
  - use when structure, boundary, knowledge, and procedure remain aligned and only minor record weakness exists

The OR Team should not leave the operating disposition implicit.

## Example Short Request

```text
Please run the OR Team on high-impact business area A for the last two weeks.
Check whether the post-update output tendency drifted from baseline.
Use logs, review results, diffs, rework history, and drift-evaluation results.
Return the standard 8-part OR output.
Stop decisions require human approval.
```

## Related

- [OR Team operating model](048_or_team_operating_model.md#xid-1D7A8E2C5F10)
- [Group definitions](040_group_definitions.md#xid-8B31F02A4009)
- [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012)
