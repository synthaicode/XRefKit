---
schema_version: 1
skill_id: ui_constraint_derivation
xid: 6B1F8D3A5E20
aliases: [C325D7E9F122, C325D7E9F123]
summary: derive requirement confirmation gates from UI structure, interaction states, and screen transitions
applies_when:
  - screen specifications, wireframes, or UI behavior notes may leave states or transitions implicit
exclusions:
  - do not silently align UI behavior with backend assumptions
inputs: [screen specs, wireframes, UI notes, interaction flows, and client-side validation descriptions]
outputs: [UCD derivation table, grouped confirmation list, explicit UI decisions, written output path]
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
knowledge_needs:
  - id: constraint_derivation_framework
    query: constraint derivation framework
    required_when: Required for deriving and classifying UI signals
    seed_xids: [81A6C4E2B190]
  - id: ui_constraint_derivation_catalog
    query: UI constraint derivation catalog
    required_when: Required for selecting UI signal categories
    seed_xids: [31C5A06B7E22]
control_refs: [111D282CA0EA]
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
