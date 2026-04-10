<!-- xid: 8B31F02A4012 -->
<a id="xid-8B31F02A4012"></a>

# System Quality Feedback Loop

This page defines how quality degradation is traced across workflows and returned upstream for structural improvement.

This page defines the structural feedback process.
For storage-role separation across `work/` record types, see [Work record types](019_work_record_types.md#xid-4F8C21B7D4A2).
For the boundary against role definitions, matrix navigation, and flow-internal quality control, see [Group, quality, and feedback boundaries](021_group_quality_and_feedback_boundaries.md#xid-8E5D31A4C672).

## Purpose

Prevent the repository from behaving as a feed-forward-only system that fixes individual defects without improving the underlying quality mechanism.

## Problem Statement

The normal workflow chain is largely feed-forward:

- investigation
- estimation
- requirements
- planning
- manufacturing
- release planning
- CAB
- closure

That chain is necessary, but not sufficient.

If:

- CAB rejects release
- closure detects leaks
- QA repeatedly finds the same review defect
- operations repeatedly detects readiness gaps

then the system must identify:

1. which workflow failed
2. which group owned that workflow
3. which lifecycle layer failed
4. what upstream correction is required

## System-Level Responsibility

System-level quality monitoring is split as follows:

- Quality Group:
  - detect recurring or structural quality degradation
  - identify the workflow and lifecycle layer where the degradation appears
  - issue a quality feedback record
- OR Team:
  - present current operating state from logs and evidence
  - structure problems, cause hypotheses, and improvement options
  - classify stop, conditional continuation, or continuation allowed
  - control approved corrective execution and re-observation across groups
  - maintain drift-detection assets and improvement traceability
- Planning Group:
  - own prioritization of structural corrective action
  - decide which upstream workflow, requirement, or assumption framing must be corrected
- Affected owner group:
  - implement the corrective action inside its own workflow boundary
- Coordinator:
  - route cross-boundary reassignment when the corrective action falls outside the current owner boundary
- Human decision layer:
  - approve major corrective direction when business, risk, or release timing is affected

## Trigger Conditions

Start the system quality feedback loop when any of the following occurs:

- CAB rejects or conditionally rejects release
- closure detects `missing` or repeated `unknown` leakage
- the same class of defect appears across multiple cycles
- manufacturing self-check, QA review, or operations readiness evaluation detects a recurring pattern

## Feedback Record

The feedback loop must produce a record containing:

- triggering workflow
- triggering artifact or finding
- affected owner group
- suspected root workflow
- suspected lifecycle layer:
  - Startup
  - Planning
  - Execution
  - Monitoring and Control
  - Closure
- evidence for the diagnosis
- immediate containment action
- required upstream corrective action
- next responsible group
- OR improvement ID and execution owner
- recovery condition
- re-observation condition
- whether human approval is required

## Root-Cause Mapping

Typical examples:

| Observed failure | Likely root workflow | Likely failed layer |
|------|------|------|
| repeated implementation assumption gaps | requirements or planning | Planning |
| CAB rejection due to weak operational readiness | release planning | Execution or Monitoring and Control |
| closure leak due to untracked targets | investigation, planning, or manufacturing | Planning or Monitoring and Control |
| repeated QA findings on specification mismatch | requirements, planning, or manufacturing | Execution or Monitoring and Control |

## Routing Rule

The loop does not simply return work to the last execution group.

Instead, it must choose one of two return paths:

1. local correction path
   - use when the issue is local to the current workflow and not structurally recurring
2. upstream corrective path
   - use when the issue indicates a fault in an earlier workflow, earlier lifecycle layer, or repeated pattern

## Upstream Corrective Path

When upstream correction is required:

1. record the structural defect
2. identify the upstream workflow to revisit
3. identify the owner group of that workflow
4. let OR Team define improvement options, approval needs, recovery condition, and re-observation condition
5. assign corrective action through Planning Group prioritization
6. route cross-boundary reassignment through Coordinator if needed
7. preserve traceability from the observed failure back to the corrective action

## Storage And Reference Path

The feedback loop stores its outputs in two places:

- detailed record:
  - `work/retrospectives/YYYY-MM-DD_feedback_<topic>.md`
- canonical register:
  - [System quality feedback register](044_system_quality_feedback_register.md#xid-8B31F02A4013)

Later Planning Group cycles must start from the canonical register and then open the linked detailed record when a row is still `open` or `in_progress`.

## Relation To Existing Flows

- [Closure workflow](034_closure_workflow.md#xid-8B31F02A4003):
  - detects leaks and unresolved states
  - should emit structural feedback when the issue is recurring or upstream in nature
- [CAB workflow](039_cab_workflow.md#xid-8B31F02A4008):
  - evaluates release readiness
  - should emit structural feedback when rejection is caused by an upstream quality problem
- [Flow quality assurance mechanism](042_flow_quality_assurance_mechanism.md#xid-8B31F02A4011):
  - covers flow-internal quality assurance
  - this page extends that mechanism across workflows
- [System quality feedback register](044_system_quality_feedback_register.md#xid-8B31F02A4013):
  - provides the stable reference point for later cycles

## Output Rule

A system-level quality finding is not complete unless it answers both:

- what must be fixed now
- what must change upstream so the same degradation does not recur

It is also not complete unless the OR loop defines:

- who must approve the improvement
- who must execute it
- how recovery will be judged
- how re-observation will be performed

## Related

- [Group, quality, and feedback boundaries](021_group_quality_and_feedback_boundaries.md#xid-8E5D31A4C672)
- [Work record types](019_work_record_types.md#xid-4F8C21B7D4A2)
- [OR Team operating model](048_or_team_operating_model.md#xid-1D7A8E2C5F10)
