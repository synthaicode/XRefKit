<!-- xid: C4B8A5D2E970 -->
<a id="xid-C4B8A5D2E970"></a>

# Skill: or_team_operations

## Purpose

Execute the OR Team operating loop for cross-group AI-organization optimization:

1. present current state from evidence
2. structure problems and cause hypotheses
3. produce improvement options
4. organize approval requirements
5. execute OR-owned changes or control execution by the responsible group
6. re-observe after change

## Required References (XID)

- [OR Team operating model](../../docs/048_or_team_operating_model.md#xid-1D7A8E2C5F10)
- [OR Team usage guide](../../docs/049_or_team_usage_guide.md#xid-4E2F91A6B8C1)
- [Group definitions](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- [System quality feedback loop](../../docs/043_system_quality_feedback_loop.md#xid-8B31F02A4012)

## Inputs

- target scope
- minimum observation data
- supporting evidence
- baseline reference
- operating constraints

Minimum observation data means:

1. case ID
2. input request ID
3. knowledge reference ID
4. rule ID used
5. output ID or output revision identity
6. output revision
7. human return flag
8. escalation flag
9. rework count
10. model name and version
11. execution timestamp

## Outputs

Always return the following sections in this order:

1. current state
2. problem list
3. cause hypotheses
4. improvement list
5. approval requirement by improvement
6. implementation method after approval
7. re-observation method after improvement
8. unresolved items

## Startup

- Confirm the target scope.
- Confirm baseline reference exists or explicitly record it as `unknown`.
- Confirm minimum observation data exists for the target set.
- Confirm operating constraints such as high-impact classification, stop-approval boundary, and alternative controls.
- If minimum observation data is missing, record that evidence gap as a problem instead of silently proceeding.

## Planning

- Define the observation window, affected workflows, and affected groups.
- Prepare IDs for problems, hypotheses, improvements, and re-observation rows.
- Define which baseline metrics will be compared.
- Define whether the OR Team is expected only to diagnose or also to control approved corrective execution.

## Execution

### 1. Present Current State

- Summarize current state from logs, deliverables, diffs, review results, rework history, escalation history, and drift-evaluation results.
- Show deviation from baseline.
- Show anomaly signs and impact scope.
- Distinguish provisional trend versus one-off behavior.

### 2. Structure Problems

- Convert symptoms into structured problems.
- Use at least these categories when applicable:
  - assumption failure
  - knowledge failure
  - procedure deviation
  - role-allocation mismatch
  - model change effect
  - connection failure
  - boundary violation
  - evidence weakness
  - unresolved-item handling failure

### 3. Build Cause Hypotheses

- Attach one or more cause hypotheses to each problem.
- Cite supporting evidence for each hypothesis.
- Mark confidence and additional-check need.

### 4. Build Improvement List

- Produce concrete improvements, not abstract advice.
- Every improvement must include at least:
  - improvement ID
  - target problem
  - cause hypothesis
  - improvement content
  - executor
  - approval requirement
  - approver
  - priority
  - expected effect
  - risk
  - recovery condition
  - re-observation condition
  - implementation status
  - implementation result
  - unresolved items

### 5. Organize Approval And Operating Disposition

- Classify each improvement into:
  - OR self-executable
  - responsible-group approval required
  - human approval required
- Classify the operating disposition into:
  - stop
  - conditional continuation
  - continuation allowed

Use `stop` when boundary violation exists, required human approval was bypassed, major drift affects high-impact work, required local-rule reference is missing, or no alternative control exists for a major drift.

Use `conditional continuation` when temporary controls can absorb the issue or when the issue is light but recurring or affects high-impact work.

Use `continuation allowed` only when structure, boundary, knowledge, and procedure remain aligned and only minor record weakness exists, or the event is one-off and non-reproducible.

## Monitoring and Control

- Track implementation status for approved improvements only.
- Do not start implementation for items still pending approval.
- When OR can act directly, update only OR-owned assets such as monitoring settings, thresholds, dashboards, evaluation assets, test items, and light OR-owned operating rules.
- When another group must execute the change, issue a controlled implementation request containing:
  - executor
  - improvement ID
  - target problem
  - requested change
  - rationale
  - approver
  - confirmation points
  - update target
  - recovery condition
  - re-observation condition
  - due date
  - risk if not executed
- Keep unresolved items explicit at all times.

Implementation status values:

- `not_started`
- `pending_approval`
- `in_progress`
- `completed`
- `returned`
- `on_hold`

## Closure

- Re-observe after implementation.
- Confirm effect, side effect, recurrence, and recovery.
- Do not close when implementation merely reaches `completed`.
- Close only after re-observation confirms recovery or stable conditional continuation.

## Rules

- Do not replace the responsibility boundary of Planning, Design, Manufacturing, Quality, or Operations.
- Do not silently approve prohibited judgments or approval-boundary changes.
- Do not hide uncertainty; preserve unresolved items explicitly.
- Do not return free-text advice only. Return a managed improvement list.
- Do not omit recovery condition or re-observation condition from any improvement.
