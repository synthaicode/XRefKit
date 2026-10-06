---
schema_version: 1
skill_id: constraint_derivation_index
xid: A4C9E2B7D160
summary: route design or implementation artifacts to constraint-derivation Skills and sequence the secondary commonality pass
applies_when:
- design specifications or implementation artifacts need derivation of missing confirmations, hidden assumptions, or boundary scenarios without implicit AI completion
exclusions:
- do not infer requirement decisions from design prose or code alone
- do not treat derivation output as approved requirements
inputs:
- design artifacts, code artifacts, partial specs, expected implementation target, and optional already-derived constraint lists
outputs:
- selected primary Skill set, execution order, shared derivation policy reminder, optional secondary-pass trigger decision, and a routing note written under `work/constraint_derivation/` unless the user specifies another path
criteria:
- id: artifact_routing
  statement: Every applicable artifact class is routed to all required primary Skills.
  verification: Compare the routing note with the artifact inventory and direction.
- id: ordering
  statement: The secondary commonality pass is queued only after all primary outputs are complete.
  verification: Check the stated execution order and prerequisite outputs.
- id: unresolved_boundary
  statement: Classification gaps and unapproved decisions remain explicit.
  verification: Review unresolved items and handoff ownership in the routing note.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: constraint_derivation_framework
  query: constraint derivation framework
  required_when: Required for routing artifact classes and shared derivation policy
  seed_xids:
  - 81A6C4E2B190
control_refs:
- 111D282CA0EA
aliases:
- A103B5C7D900
- A103B5C7D901
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
4. Preserve each Skill's ID prefix and queue `commonality_derivation` only after all primary outputs are complete.
5. Write the routing result and unresolved classification gaps.

## Monitoring and Control
- Stop if a matching primary Skill is skipped for convenience.
- Do not approve unresolved items or substitute upward derivation for required downward confirmation.

## Closure and Handoff
- Return the selected Skill set, execution order, secondary-pass decision, unresolved gaps, and routing path.
- Hand the routing note to the selected primary Skill owners.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Source summary discrepancy

The historical metadata says primary outputs exist; the detailed source procedure requires all primary lists complete before the secondary pass. Apply the detailed completion gate.

### Original Skill-specific procedure

# Skill: constraint_derivation_index

## Purpose

Route design or implementation artifacts to the correct constraint-derivation
Skills before code behavior is accepted or expanded.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Inputs

- design specifications, diagrams, or partial design notes
- code artifacts such as generated C# code or mixed code-plus-DDL review targets
- known artifact classes such as DDL, UI spec, workflow, API contract, auth matrix, or integration boundary notes
- optional outputs from earlier derivation runs

## Outputs

- selected primary Skill list
- routing rationale by artifact class
- explicit decision on whether `commonality_derivation` should run afterward
- routing note file in `work/constraint_derivation/` unless another output path is specified

## Startup

- Confirm whether the request is design-downward, implementation-upward, or mixed-direction derivation.
- Identify which artifact classes are present.
- Load the routing table and shared principles from the framework knowledge page.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_constraint_derivation_routing_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Classify the input artifacts by design area.
2. Route to every applicable downward Skill when design artifacts are present:
   - `design_constraint_derivation`
   - `ui_constraint_derivation`
   - `logic_constraint_derivation`
   - `integration_constraint_derivation`
   - `async_constraint_derivation`
   - `auth_constraint_derivation`
3. Route to every applicable upward Skill when implementation artifacts are present:
   - `code_constraint_derivation`
   - `cross_constraint_derivation`
   - `integration_scenario_derivation`
4. Preserve each Skill's ID prefix so later outputs stay traceable.
5. If more than one primary Skill produced outputs, queue `commonality_derivation` after all primary lists are complete.
6. Keep unresolved items explicit; do not answer them from context completion.
7. Write the routing result to the output file and return that path.

## Monitoring and Control

- Stop if someone tries to skip a matching primary Skill for convenience.
- Do not treat derivation output as already approved requirements.
- Do not treat upward derivation as a substitute for downward design confirmation when the design artifacts still exist.
- Do not run the secondary pass before the primary outputs are complete.

## Closure

- Return the selected Skill set and execution order.
- State whether the secondary pass is required.
- Carry forward unresolved classification gaps as explicit open items.
- Return the written routing-note path.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: route design or implementation artifacts to the correct bidirectional constraint-derivation Skills and sequence the secondary commonality pass

- use_when: design specifications or implementation artifacts need derivation of missing confirmations, hidden assumptions, or boundary scenarios without implicit AI completion

- input: design artifacts, code artifacts, partial specs, expected implementation target, and optional already-derived constraint lists

- output: selected primary Skill set, execution order, shared derivation policy reminder, optional secondary-pass trigger decision, and a routing note written under `work/constraint_derivation/` unless the user specifies another path

- constraints: do not infer requirement decisions from design prose or code alone; route to all applicable primary Skills before the secondary commonality pass; keep shared rules in knowledge instead of duplicating them across pack Skills; write the routing result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the input is design-oriented, implementation-oriented, or mixed and collect the artifact types that must be inspected
  - planning: map artifact types to primary Skills in the downward or upward direction and determine whether a secondary commonality pass will be needed
  - execution: route the request, preserve prefix separation, and sequence `commonality_derivation` only after primary outputs exist
  - monitoring_and_control: stop if the task tries to approve unresolved items or skip derivation for applicable artifact classes
  - closure: return the selected Skill set, routing basis, unresolved gaps, and the next execution handoff

- tags: `design`, `review`, `routing`, `requirements-derivation`

- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
