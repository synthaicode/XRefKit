<!-- xid: 7F2C8DA14E66 -->
<a id="xid-7F2C8DA14E66"></a>

# Business Intake Workflow

This workflow defines how incomplete business fragments are learned and scoped
before later execution-design or delivery workflows.

## Purpose

Turn partial business fragments into one boundary-visible, scope-ready business
unit without requiring the human to provide the full business map in advance.

## Group Interaction

| Item | Value |
|------|------|
| Owner group | Planning Group |
| Input from | human fragment, artifact fragment, known owner, known downstream side, repeated trouble point |
| Output to | later investigation, requirements, or planning workflows after the business unit becomes scope-ready |
| Main handoff artifacts | interview-cycle summary, current business hypothesis, scoped business unit, unresolved intake items, next confirmation point |
| Escalation path | unresolved business interpretation stays explicit; boundary or ownership ambiguity is preserved for later human confirmation |

## Flow Diagram

```mermaid
flowchart TD
    A[Human fragment or business seed] --> B[Business learning interview]
    B --> C{Scope-ready?}
    C -- No --> D[Ask next best question]
    D --> B
    C -- Yes --> E[Business intake scoping]
    E --> F[Scoped business unit]
    F --> G[Later workflow selection]
    F --> H[Preserve unresolved items]
```

## Business Activities and Supporting Capabilities

- Business learning from fragments:
  - currently executed directly by [business_learning_interview](../../../skills/packs/business-intake/business_learning_interview/SKILL.md#xid-4D8E1A7C5B92)
  - no dedicated business-intake capability page has been extracted yet
- Scope-ready responsibility shaping:
  - currently executed directly by [business_intake_scoping](../../../skills/packs/business-intake/business_intake_scoping/SKILL.md#xid-6F2A9C41E8B3)
  - no dedicated business-intake capability page has been extracted yet
- Shared OS-core runtime control:
  - supported by [CAP-MGT-005 Skill Runtime Envelope](../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5)
  - supported by [CAP-MGT-004 Context Direction Guard](../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11)

## Sequence

1. Start from one visible business seed such as a goal, artifact, owner, bottleneck, or downstream dependency.
2. Run business learning interview cycles until the goal, judgment, domain-knowledge area, input-information area, quality viewpoint, and handoff sides become visible enough.
3. If the result is not yet scope-ready, preserve unresolved points and continue with the next best question instead of demanding a full business map.
4. Once the unit becomes scope-ready, run business intake scoping on the current responsibility boundary.
5. Record previous side, current responsibility, next side, and first-pass scoping fields.
6. Hand off the scoped unit and unresolved items to the next applicable workflow.

## Inputs

- human fragment or business seed
- stated goal or expected result when available
- known upstream or downstream side when available
- artifact examples, rules, or approval points when available

## Outputs

- interview-cycle summary
- current business hypothesis
- scoped business unit
- unresolved intake items
- next confirmation point
- later-workflow handoff basis

## Control Rules

- Do not require the full business map before starting.
- When structure is incomplete, learning must run before scoping.
- Keep observed facts, AI hypotheses, and unresolved items separate.
- Do not treat local work steps as the primary scoping level.
- Previous side, current responsibility, and next side must remain explicit.
- If the unit is not scope-ready, preserve the gap instead of silently promoting it.

## Required Knowledge

- [Business learning interview rules](../../../knowledge/packs/business-intake/120_business_learning_interview_rules.md#xid-7B3E5D1A6103)
- [Business intake scoping rules](../../../knowledge/packs/business-intake/110_business_intake_scoping_rules.md#xid-7B3E5D1A6102)
- [Context direction guard rules](../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Related Skills

- [business_learning_interview](../../../skills/packs/business-intake/business_learning_interview/SKILL.md#xid-4D8E1A7C5B92)
- [business_intake_scoping](../../../skills/packs/business-intake/business_intake_scoping/SKILL.md#xid-6F2A9C41E8B3)
- [context_direction_guard](../../../skills/os/context_direction_guard/SKILL.md#xid-4D8C7F1A9E22)
