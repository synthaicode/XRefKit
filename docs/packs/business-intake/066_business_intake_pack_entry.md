<!-- xid: 732E41DCA2E8 -->
<a id="xid-732E41DCA2E8"></a>

# Business Intake Pack Entry

This page is the compact entry for the `business-intake` pack during the AI
Agent OS reorganization.
It identifies what the pack owns and what it depends on from the OS core.
It is not the runtime contract itself.

Related:

- [Business intake pack dependency design](065_business_intake_pack_dependency_design.md#xid-D334C1964342)
- [Business intake workflow](067_business_intake_workflow.md#xid-7F2C8DA14E66)
- [Business learning interview guide](061_business_learning_interview_guide.md#xid-D2A41E8C7B51)
- [Business intake scoping guide](060_business_intake_scoping_guide.md#xid-C91F7D2A6B40)

## Pack Purpose

The `business-intake` pack learns incomplete business fragments and shapes them
into one scope-ready business unit before later execution design.

## Startup Decision Table

Use this table before selecting either business-intake Skill. The pack may start
from a single visible business seed; it must not require a complete business map
before helping.

| Visible input state | Start with | Reason |
| --- | --- | --- |
| No business seed is visible | Ask for one seed first | The pack needs at least a goal, task name, role, artifact, bottleneck, approval point, repeated error, or partial handoff. |
| One or more seeds are visible, but the goal, judgment, ownership, or handoff is still unclear | `business_learning_interview` | The request is still in learning mode; produce an interview cycle and the smallest next question. |
| A goal and candidate business unit are visible, but previous/current/next boundaries are incomplete | `business_learning_interview`, then reassess scoping readiness | Ownership and interpretation must not be promoted to scope-ready while both are provisional. |
| A target task or candidate business unit is visible and at least part of the previous side, current responsibility, and next side can be named | `business_intake_scoping` | The request can be shaped into a responsibility-level scope, even if the result remains partial. |
| The user provides only screen clicks, private habits, or local implementation steps | `business_intake_scoping` only to recover a business-level boundary; otherwise ask for the business goal | Work-step detail is not a valid starting level unless the business and responsibility levels are already explicit. |
| The scope-ready fields are visible: start trigger, inputs, judgment point, outputs, send-back or stop condition, and next owner or next side | `business_intake_scoping` | The pack can produce a scoped intake note and handoff candidate for investigation, requirements, or planning. |

`business_learning_interview` may recommend handoff to
`business_intake_scoping`, but only when the scoping readiness fields are visible.
`business_intake_scoping` may still return `partial`; partial scoping is valid
when the missing boundary and next confirmation point are explicit.

## Canonical Manifest

The machine-checkable definition of this pack is its manifest:

- `skills/packs/business-intake/pack.md`

The manifest declares what the pack OWNS (exclusive) versus what it USES (shared
references that may live anywhere, including the OS core), and pins the OS-core
contract version it depends on. Validate it with `python -m fm pack lint`. This
page remains the human-facing entry; the manifest is the source of truth for
membership and boundary.

## Pack-Owned Assets

### Skills

- `skills/packs/business-intake/business_learning_interview/`
- `skills/packs/business-intake/business_intake_scoping/`

### Knowledge

- `knowledge/packs/business-intake/120_business_learning_interview_rules.md`
- `knowledge/packs/business-intake/110_business_intake_scoping_rules.md`

### Guides

- [Business intake workflow](067_business_intake_workflow.md#xid-7F2C8DA14E66)
- [Business learning interview guide](061_business_learning_interview_guide.md#xid-D2A41E8C7B51)
- [Business intake scoping guide](060_business_intake_scoping_guide.md#xid-C91F7D2A6B40)

### Flows

- `flows/packs/business-intake/business_intake_workflow.yaml`

## Shared OS-Core Dependencies

The pack depends on shared OS-core capabilities and must not redefine them.

### Shared Capabilities


### Shared Knowledge

- [Context direction guard rules](../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

### Shared Runtime Surface

- `fm skill run`
- `fm skill workitem`
- `fm skill artifact`
- `fm skill concern`
- `fm skill phase`
- `fm skill close`
- `fm xref search`
- `fm xref show`

## Stage-3 Status

The `business-intake` pack is the first pack that now has an explicit family
path for:

- Skills
- pack-owned Knowledge
- machine-readable Flow
- human-facing pack entry and dependency design

## Boundary Rule

- Keep pack-owned learning and scoping logic inside the pack.
- Keep runtime envelope, closure, guard, and audit controls in the OS core.
- When adding later `business-intake` assets, place them in the pack family
  unless they are clearly reusable across business packs.
