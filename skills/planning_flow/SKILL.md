<!-- xid: 486C9EEE8A9D -->
<a id="xid-486C9EEE8A9D"></a>

# Skill: planning_flow

## Purpose

Execute `CAP-PLN-001` and prepare work planning outputs from approved requirements, domain knowledge, and current-source findings.

## Required Capability Definitions (XID)

- [CAP-PLN-001 Work and Policy Planning Structuring](../../capabilities/planning/100_cap_pln_001_task_decomposition_plan_draft.md#xid-F5193313AB79)

## Inputs

- approved requirements
- change target list
- current source structure findings
- domain knowledge references

## Required Knowledge (XID)

- [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)
- [C# custom framework analysis criteria](../../knowledge/csharp/110_custom_framework_analysis_criteria.md#xid-30E6A4F6F3AB)

## Outputs

- work plan
- source modification policy
- data change policy
- test policy
- release policy
- planning basis source list

## Startup

- Confirm approved requirements exist.
- Confirm change targets are available.
- Confirm current source findings and domain knowledge references are available.
- Record `unknown` if planning inputs are missing.

## Planning

- Define planning scope and downstream design-policy targets.
- Identify which domain knowledge and current-source findings govern the target scope.
- Map the business activity to its supporting capability:
  - work planning and policy drafting -> `CAP-PLN-001`
- Prepare management rows for planning outputs and unresolved policy assumptions.

## Execution

- Perform work planning and policy drafting by executing `CAP-PLN-001`.
- Build source modification policy from the current source structure by default.
- Record an explicit reason if the plan intentionally departs from the current structure.
- Record the source files, modules, registrations, or framework artifacts used as the basis of each planning policy.
- Produce planning outputs and preserve unresolved planning assumptions explicitly.

## Monitoring and Control

- Check that all required planning outputs have a recorded result.
- Downgrade weakly supported planning assumptions to `unknown`.
- Downgrade source-structure claims to `unknown` if no current-source finding supports them.
- Preserve unresolved policy, dependency, or assignment questions.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off the planning outputs, planning basis source list, and unresolved planning items to design work.
- Escalate out-of-scope planning questions when reassignment is required.

## Rules

- Do not finalize resource allocation.
- Do not finalize business priority.
- Do not invent a target structure without checking the current codebase first.
