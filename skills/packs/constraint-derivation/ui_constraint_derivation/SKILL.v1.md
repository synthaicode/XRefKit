---
schema_version: 1
skill_id: ui_constraint_derivation
xid: 6B1F8D3A5E20
summary: derive requirement confirmation gates from UI structure, interaction states, and screen transitions
applies_when:
- screen specifications, wireframes, or UI behavior notes may leave states or transitions to implicit AI completion
exclusions:
- do not silently align UI behavior with backend assumptions
inputs:
- screen specs, wireframes, UI notes, interaction flows, and client-side validation descriptions
outputs:
- UCD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and explicit design-time UI decisions
criteria:
- id: ui_evidence
  statement: Every UCD item is grounded in a visible UI element, action, state, or transition.
  verification: Check each item against the supplied screen or interaction evidence.
- id: state_coverage
  statement: Validation gaps, transition edge cases, asynchronous behavior, and concurrent actions remain explicit.
  verification: Review the interaction inventory and unresolved items.
- id: output_closure
  statement: The derivation file exists at the declared output path with grouped confirmations and decisions.
  verification: Check the output path before handoff.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: constraint_derivation_framework
  query: constraint derivation framework
  required_when: Required for deriving and classifying UI signals
  seed_xids:
  - 81A6C4E2B190
- id: ui_constraint_derivation_catalog
  query: UI constraint derivation catalog
  required_when: Required for selecting UI signal categories
  seed_xids:
  - 31C5A06B7E22
control_refs:
- 111D282CA0EA
aliases:
- C325D7E9F122
- C325D7E9F123
---
<!-- xid: 6B1F8D3A5E20 -->
<a id="xid-6B1F8D3A5E20"></a>

# Skill: ui_constraint_derivation

## Purpose
Derive requirement confirmation gates from UI structure before implementation locks in implicit behavior.

## Inputs
- screen specs, wireframes, UI behavior notes, and interaction flows

## Outputs
- UCD-prefixed derivation basis table
- grouped requirement confirmation list
- explicit UI design-time decisions
- written output path

## Startup
- Confirm the input contains UI elements or screen transitions.
- Load framework and UI catalog Knowledge.
- Identify validation, action, list, transition, and real-time behavior surfaces.
- Use `work/constraint_derivation/YYYY-MM-DD_ui_constraint_derivation_<topic>.md` unless an output path is supplied.

## Execution
1. Enumerate inputs, buttons, lists, transitions, and asynchronous UI elements.
2. Apply the UI catalog and assign `UCD-` ids.
3. Group results by screen or interaction element.
4. Separate requirement confirmations from design-time UI decisions.
5. Keep unconfirmed states explicit and write the result using the primary derivation output template or equivalent.

## Monitoring and Control
- Do not assume backend behavior resolves missing UI decisions.
- Stop if interaction behavior is implemented before UCD items are confirmed.
- Keep transition edge cases and concurrent user actions explicit.

## Closure and Handoff
- Return the UCD table, grouped unresolved items, decisions, and path.
- Hand UI decisions requiring approval to the design owner.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: ui_constraint_derivation

## Purpose

Derive requirement confirmation gates from UI structure before implementation
locks in implicit behavior.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [UI constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/130_ui_constraint_derivation_catalog.md#xid-31C5A06B7E22)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md#xid-FF9A33B945ED)

## Inputs

- screen specs, wireframes, UI behavior notes, and interaction flows

## Outputs

- UCD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- explicit UI design-time decisions
- written output path

## Startup

- Confirm the input contains UI elements or screen transitions.
- Load the framework and the UI catalog.
- Identify validation, action, list, transition, and real-time behavior surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_ui_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate inputs, buttons, lists, transitions, and asynchronous UI elements.
2. Apply the UI catalog and assign `UCD-` ids.
3. Group the results by screen or interaction element.
4. Separate requirement confirmations from design-time UI decisions.
5. Keep unconfirmed states explicit instead of normalizing them to happy-path behavior.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not assume backend behavior resolves missing UI decisions.
- Stop if the task tries to implement interaction behavior before UCD items are confirmed.
- Keep transition edge cases and concurrent user actions explicit.

## Closure

- Return the UCD table and grouped unresolved items.
- Highlight UI states that still need confirmation before implementation.
- Return the written output path.

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

- summary: derive requirement confirmation gates from UI structure, interaction states, and screen transitions

- use_when: screen specifications, wireframes, or UI behavior notes may leave states or transitions to implicit AI completion

- input: screen specs, wireframes, UI notes, interaction flows, and client-side validation descriptions

- output: UCD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and explicit design-time UI decisions

- constraints: derive from visible UI structure instead of expected happy-path behavior; keep transition and validation gaps explicit; do not silently align UI behavior with backend assumptions; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the input contains UI structure and load the shared framework plus the UI catalog
  - planning: identify inputs, actions, screen transitions, and asynchronous UI behaviors
  - execution: derive UCD items, group them by screen element, and keep unsupported behavior unresolved
  - monitoring_and_control: stop if UI edge states are being collapsed into vague happy-path handling
  - closure: return the derivation table, grouped confirmation items, and explicit UI design decisions

- tags: `design`, `ui`, `requirements-derivation`

- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=ui_constraint_derivation_catalog; bind=31C5A06B7E22

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md
