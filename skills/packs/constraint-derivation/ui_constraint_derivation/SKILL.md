<!-- xid: C325D7E9F123 -->
<a id="xid-C325D7E9F123"></a>

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
