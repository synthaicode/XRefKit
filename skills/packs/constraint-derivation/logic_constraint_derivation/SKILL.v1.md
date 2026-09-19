---
schema_version: 1
skill_id: logic_constraint_derivation
xid: 3D7A9E2B4C60
aliases: [D436E8FA0123, D436E8FA0124]
summary: derive requirement confirmation gates from branching, calculations, state transitions, and approval logic
applies_when:
  - business-logic specifications may leave boundary, exception, or transition behavior implicit
exclusions:
  - do not infer unspecified else-paths or business rules from examples
inputs: [logic specs, flowcharts, calculations, and state-transition definitions]
outputs: [LCD derivation table, grouped confirmation list, state-transition matrix, written output path]
criteria:
  - id: logic_evidence
    statement: Every LCD item is grounded in an observed branch, calculation, transition, approval, or control rule.
    verification: Check each item against the supplied logic evidence.
  - id: boundary_coverage
    statement: Unresolved branches, invalid values, and calculation or transition boundaries remain explicit.
    verification: Review the transition matrix and unresolved items.
  - id: output_closure
    statement: The derivation file exists at the declared output path with grouped confirmations and gaps.
    verification: Check the output path before handoff.
knowledge_needs:
  - id: constraint_derivation_framework
    query: constraint derivation framework
    required_when: Required for deriving and classifying logic signals
    seed_xids: [81A6C4E2B190]
  - id: logic_constraint_derivation_catalog
    query: logic constraint derivation catalog
    required_when: Required for selecting logic signal categories
    seed_xids: [4E5B8923C912]
control_refs: [111D282CA0EA]
---
<!-- xid: 3D7A9E2B4C60 -->
<a id="xid-3D7A9E2B4C60"></a>

# Skill: logic_constraint_derivation

## Purpose
Derive requirement confirmation gates from business-logic structure before exception paths are filled in implicitly.

## Inputs
- logic specs, flowcharts, calculations, and state-transition definitions

## Outputs
- LCD-prefixed derivation basis table
- grouped requirement confirmation list
- state-transition matrix when required
- written output path

## Startup
- Confirm the input contains branch, calculation, or transition structure.
- Load framework and logic catalog Knowledge.
- Use `work/constraint_derivation/YYYY-MM-DD_logic_constraint_derivation_<topic>.md` unless an output path is supplied.

## Execution
1. Enumerate branches, calculations, transitions, approvals, and control rules.
2. Apply the logic catalog and assign `LCD-` ids.
3. Expand transition matrices where current-state and action axes are exposed.
4. Group results by logic unit and keep unresolved boundaries explicit.
5. Write the result using the primary derivation output template or an equivalent structure.

## Monitoring and Control
- Do not accept a single happy-path example as full logic coverage.
- Stop if invalid transitions or boundary calculations are skipped.
- Preserve confirmed rules separately from unconfirmed cases.

## Closure and Handoff
- Return the LCD table, grouped unresolved items, blocking matrices, and path.
- Hand unresolved business meaning to the responsible human or design owner.
