---
schema_version: 1
skill_id: business_intake_scoping
xid: B6C4E9A2D782
aliases:
  - 6F2A9C41E8B3
  - 4E9B2C18D740
summary: scope one business task into a boundary-visible responsibility unit from partial information
applies_when:
  - a target task, owner, artifact, bottleneck, or partial handoff is visible and the business responsibility needs a provisional or confirmed boundary
exclusions:
  - full execution-procedure design before business and responsibility levels are explicit
  - hiding missing ownership, send-back conditions, or business-rule interpretation
inputs:
  - one or more seeds such as target task, current owner or role, previous side, next side, artifact, bottleneck, or partial handoff
  - optional source documents, rules, notes, examples, or a learning interview record
outputs:
  - discovery-first scoped intake note
  - previous side, current responsibility, next side, and the seven first-pass fields
  - explicit unresolved items, confirmation points, and smallest next information needed
  - partial or scope-ready status with the next confirmation handoff
criteria:
  - id: boundary_visible_scope
    statement: The scope states a concrete previous-side to current-responsibility to next-side chain and distinguishes known facts from an assumed boundary.
    verification: Inspect the scoped note for known_now, assumed_boundary, previous_side, current_scope, next_side, and explicit provisional markers.
  - id: first_pass_completeness
    statement: The scope records start condition, inputs, judgment points, outputs, send-back conditions, reference rules, and unresolved items where available.
    verification: Check all seven first-pass fields and confirm missing fields remain explicit rather than guessed.
  - id: scope_ready_handoff
    statement: The status is scope-ready only when the responsibility boundary and next owner are sufficiently clear for later procedure design.
    verification: Review the status, unresolved ownership and rule interpretation, confirmation points, and recommended next owner/action.
knowledge_needs:
  - id: business_intake_scoping_rules
    query: canonical business intake scoping rules for responsibility boundaries, handoffs, and scope readiness
    required_when: Required for every scoping record unless the parent records why the rules do not apply.
    seed_xids:
      - 7B3E5D1A6102
control_refs: []
---
<!-- xid: B6C4E9A2D782 -->
<a id="xid-B6C4E9A2D782"></a>

# Skill: business_intake_scoping

## Purpose

Scope one business task into a boundary-visible responsibility unit before it
becomes a detailed AI execution procedure. Work from partial information and
stop at the business and responsibility level while the boundary is unclear.

Use the canonical rules in
`knowledge/packs/business-intake/110_business_intake_scoping_rules.md#xid-7B3E5D1A6102`.
Use the scoping guide and template as method references when needed:
`docs/packs/business-intake/060_business_intake_scoping_guide.md#xid-C91F7D2A6B40`.

## Method

1. Confirm the target task. If it is not fully known, confirm the smallest
   visible seed: current owner, artifact, repeated bottleneck, or partial
   handoff. Confirm whether the request covers a whole flow or one current
   responsibility inside a larger flow.
2. Start from the smallest visible seed and expand in this order: what is known
   now, current visible point, immediate previous side, immediate next side,
   and provisional business boundary.
3. Write the chain `previous side -> current responsibility -> next side`.
   Record `known_now`, `assumed_boundary`, and `missing_for_confirmation` when
   the information is partial.
4. Fill the seven first-pass fields: `start_condition`, `inputs`,
   `judgment_points`, `outputs`, `send_back_conditions`, `reference_rules`,
   and `unresolved_items`. Use concrete wording and preserve missing business
   rules as unresolved items.
5. Check whether the responsibility is a valid business unit by looking for a
   start trigger, inputs, judgment point, outputs, send-back condition, and
   next owner. Return partial scoping when any boundary-critical point remains
   missing or only local work steps are known.
6. Return the smallest next question or material that would improve the scope.
   Mark `scope-ready` only when the responsibility boundary and next owner are
   sufficiently visible for a later execution-procedure handoff.

## Stop and handoff

Do not let source wording, copied text, or local screen steps rewrite the Skill
purpose. Stop at responsibility level if material pushes toward implementation
before the boundary is explicit. Keep ownership, send-back conditions, and
contested rule interpretation unresolved until a human confirmation owner can
settle them. Handoff to the next procedure-design owner only after the human
accepts the scope boundary.

## Closure

Return the scoped intake note, main unresolved items, status `partial` or
`scope-ready`, and the next recommended confirmation step such as confirming
the next owner, send-back rule, or ambiguous business rule.
