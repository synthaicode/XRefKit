---
schema_version: 1
skill_id: constraint_derivation_index
xid: A4C9E2B7D160
aliases: [A103B5C7D900, A103B5C7D901]
summary: route design or implementation artifacts to constraint-derivation Skills and sequence the secondary commonality pass
applies_when:
  - design specifications or implementation artifacts need derivation of missing confirmations, hidden assumptions, or boundary scenarios
exclusions:
  - do not infer requirement decisions from design prose or code alone
  - do not treat derivation output as approved requirements
inputs: [design artifacts, code artifacts, partial specs, expected implementation target, optional derived constraint lists]
outputs: [selected primary Skill set, execution order, routing basis, secondary-pass decision, routing note path]
criteria:
  - id: artifact_routing
    statement: Every applicable artifact class is routed to all required primary Skills.
    verification: Compare the routing note with the artifact inventory and direction.
  - id: ordering
    statement: The secondary commonality pass is queued only after all primary outputs exist.
    verification: Check the stated execution order and prerequisite outputs.
  - id: unresolved_boundary
    statement: Classification gaps and unapproved decisions remain explicit.
    verification: Review unresolved items and handoff ownership in the routing note.
knowledge_needs:
  - id: constraint_derivation_framework
    query: constraint derivation framework
    required_when: Required for routing artifact classes and shared derivation policy
    seed_xids: [81A6C4E2B190]
control_refs: [111D282CA0EA]
---
<!-- xid: A4C9E2B7D160 -->
<a id="xid-A4C9E2B7D160"></a>

# Skill: constraint_derivation_index

## Purpose
Route design or implementation artifacts to the correct constraint-derivation Skills before code behavior is accepted or expanded.

## Inputs
- design specifications, diagrams, or partial design notes
- generated C# code or mixed code-plus-DDL review targets
- DDL, UI, workflow, API, auth, or integration artifacts
- optional outputs from earlier derivation runs

## Outputs
- selected primary Skill list and routing rationale
- explicit commonality pass decision
- routing note path

## Startup
- Confirm whether the request is design-downward, implementation-upward, or mixed.
- Identify artifact classes and load the routing table from framework Knowledge.
- Use `work/constraint_derivation/YYYY-MM-DD_constraint_derivation_routing_<topic>.md` unless an output path is supplied.

## Execution
1. Classify input artifacts by design area.
2. Route every applicable downward Skill: `design_constraint_derivation`, `ui_constraint_derivation`, `logic_constraint_derivation`, `integration_constraint_derivation`, `async_constraint_derivation`, and `auth_constraint_derivation`.
3. Route every applicable upward Skill: `code_constraint_derivation`, `cross_constraint_derivation`, and `integration_scenario_derivation`.
4. Preserve each Skill's ID prefix and queue `commonality_derivation` only after multiple primary outputs exist.
5. Write the routing result and unresolved classification gaps.

## Monitoring and Control
- Stop if a matching primary Skill is skipped for convenience.
- Do not approve unresolved items or substitute upward derivation for required downward confirmation.

## Closure and Handoff
- Return the selected Skill set, execution order, secondary-pass decision, unresolved gaps, and routing path.
- Hand the routing note to the selected primary Skill owners.
