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

- [CAP-MGT-005 Skill Runtime Envelope](../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5)
- [CAP-MGT-004 Context Direction Guard](../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11)

### Shared Knowledge

- [Context direction guard rules](../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

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
