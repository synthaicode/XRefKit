<!-- xid: 486C9EEE8A9D -->
<a id="xid-486C9EEE8A9D"></a>

# Skill: planning_flow

## Purpose

Execute `CAP-PLN-001` and prepare a plan draft from approved requirements.

## Required Capability Definitions (XID)

- [CAP-PLN-001 Work Decomposition Structuring](../../capabilities/planning/100_cap_pln_001_task_decomposition_plan_draft.md#xid-F5193313AB79)

## Inputs

- approved requirements
- change target list

## Outputs

- task list
- dependency map
- execution order
- effort estimate
- group assignment draft

## Startup

- Confirm approved requirements exist.
- Confirm change targets are available.
- Record `unknown` if planning inputs are missing.

## Planning

- Define planning scope and decomposition targets.
- Map the business activity to its supporting capability:
  - task decomposition and plan drafting -> `CAP-PLN-001`
- Prepare management rows for tasks, dependencies, and assignment assumptions.

## Execution

- Perform task decomposition and plan drafting by executing `CAP-PLN-001`.
- Produce a plan draft and preserve unresolved planning assumptions explicitly.

## Monitoring and Control

- Check that all required task areas have a recorded result.
- Downgrade weakly supported planning assumptions to `unknown`.
- Preserve unresolved assignment or dependency questions.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the plan draft and unresolved planning items.
- Escalate out-of-scope planning questions when reassignment is required.

## Rules

- Do not finalize resource allocation.
- Do not finalize business priority.
