<!-- xid: A103B5C7D901 -->
<a id="xid-A103B5C7D901"></a>

# Skill: constraint_derivation_index

## Purpose

Route design-oriented input to the correct constraint-derivation Skills before
implementation starts.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)
- [Working area policy](../../../../docs/014_working_area_policy.md#xid-111D282CA0EA)

## Inputs

- design specifications, diagrams, or partial design notes
- known artifact classes such as DDL, UI spec, workflow, API contract, or auth matrix
- optional outputs from earlier derivation runs

## Outputs

- selected primary Skill list
- routing rationale by artifact class
- explicit decision on whether `commonality_derivation` should run afterward
- routing note file in `work/constraint_derivation/` unless another output path is specified

## Startup

- Confirm the request is about pre-implementation design confirmation, not final approval.
- Identify which artifact classes are present.
- Load the routing table and shared principles from the framework knowledge page.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_constraint_derivation_routing_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Classify the input artifacts by design area.
2. Route to every applicable primary Skill:
   - `design_constraint_derivation`
   - `ui_constraint_derivation`
   - `logic_constraint_derivation`
   - `integration_constraint_derivation`
   - `async_constraint_derivation`
   - `auth_constraint_derivation`
3. Preserve each Skill's ID prefix so later outputs stay traceable.
4. If more than one primary Skill produced outputs, queue `commonality_derivation` after all primary lists are complete.
5. Keep unresolved items explicit; do not answer them from context completion.
6. Write the routing result to the output file and return that path.

## Monitoring and Control

- Stop if someone tries to skip a matching primary Skill for convenience.
- Do not treat derivation output as already approved requirements.
- Do not run the secondary pass before the primary outputs are complete.

## Closure

- Return the selected Skill set and execution order.
- State whether the secondary pass is required.
- Carry forward unresolved classification gaps as explicit open items.
- Return the written routing-note path.
