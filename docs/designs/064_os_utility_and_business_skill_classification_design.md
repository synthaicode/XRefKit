<!-- xid: ECF29DC3E268 -->
<a id="xid-ECF29DC3E268"></a>

# OS Utility and Business Skill Classification Design

This page is a design document for classifying current `skills/` assets under
the current XRefKit repository model.
It is not a usage guide.

## Purpose

This page defines which current Skills should be treated primarily as:

- OS utility Skills
- business or domain pack Skills

The goal is not to rename every Skill immediately.
The goal is to stop mixing core operating utilities and business execution
procedures as if they were one flat catalog.

Related:

- [Business Pack model](../core/models/071_business_pack_model.md#xid-40511A8A06CD)
- [Overview](../000_overview.md#xid-7C6C2B46A9D1)
- [Skills Index](../../skills/_index.md#xid-8D91F66DDBB7)

## Classification Rule

### OS Utility Skill

Treat a Skill as an OS utility Skill when its main purpose is one or more of
the following:

- protect runtime control
- preserve boundary and uncertainty handling
- improve or govern reusable operating assets
- move, promote, audit, or migrate repository-native agent assets
- keep execution memory, judgment, or closure structure usable across domains

An OS utility Skill may be used while working on a business pack, but it does
not itself define the business work.

### Business Or Domain Pack Skill

Treat a Skill as a business or domain pack Skill when its main purpose is one
or more of the following:

- learn or scope business work
- execute a lifecycle phase such as investigation, planning, design, or implementation
- perform domain-specific analysis or review
- produce a business-facing or delivery-facing work result

These Skills depend on the OS core and may use OS utility Skills, but they are
not the OS core themselves.

## Current Classification

| Skill | Classification | Reason |
|------|------|------|
| `import_skill` | OS utility | imports external Skill content into the repository model |
| `doc_ship` | OS utility | promotes approved `work/` outputs into canonical assets |
| `retro` | OS utility | reviews operational memory and proposes promotion |
| `judgment_log` | OS utility | preserves non-trivial judgment as operating memory |
| `skill_flow_authoring` | OS utility | authors repo-native Skill / Flow assets |
| `legacy_flow_skill_migration` | OS utility | migrates older Flow / Skill assets into the current model |
| `business_learning_interview` | business or domain pack | learns a business task from partial human fragments |
| `business_intake_scoping` | business or domain pack | scopes one business responsibility unit |
| `investigation_flow` | business or domain pack | executes investigation-stage business work |
| `estimation_flow` | business or domain pack | executes estimation and supplier-check work |
| `requirements_flow` | business or domain pack | drafts requirements |
| `planning_flow` | business or domain pack | prepares planning outputs and policies |
| `design_flow` | business or domain pack | creates implementation-ready design outputs |
| `implementation_flow` | business or domain pack | performs implementation work |
| `manufacturing_self_check` | business or domain pack | checks implementation against design intent |
| `qa_gate_review` | business or domain pack | performs QA gate review |
| `release_planning_flow` | business or domain pack | prepares release and operational readiness outputs |
| `cab_review_flow` | business or domain pack | performs CAB-style review work |
| `marketing_slide_png` | business or domain pack | produces marketing-group visual outputs |
| `marketing-explainer-video` | business or domain pack | produces narrated explainer outputs |
| `xlsx_spec_traceability` | business or domain pack | performs spreadsheet-driven specification conversion work |
| `pptx_spec_traceability` | business or domain pack | performs deck-driven specification conversion work |
| `csharp_review` | business or domain pack | performs language-specific review work |
| `dotnet_change_analysis` | business or domain pack | performs .NET change analysis |

## Operating Meaning

This classification is about primary responsibility, not absolute isolation.

- OS utility Skills may be invoked while maintaining business packs.
- business or domain pack Skills still carry the OS contract and runtime envelope.
- one Skill is not promoted to OS utility merely because it uses `work/`,
  `xref`, or runtime records.

The key distinction is:

- OS utility Skills improve or protect the operating layer
- business or domain pack Skills perform or shape the business work itself

## Routing Implication

The flat `skills/` catalog may remain for now, but routing should increasingly
recognize two questions separately:

1. is the user asking to operate or improve the AI Agent OS?
2. is the user asking to execute or shape business work inside one pack?

When the first question dominates, prefer OS utility Skills.
When the second question dominates, prefer business or domain pack Skills.

## Current Gaps

- The repository now has a first physical split under `skills/os/` and
  `skills/packs/business-intake/`, but the rest of the catalog is still stored
  at the old top level.
- `skills/_index.md` still serves one compact catalog view even though physical
  grouping now exists.
- Some utility-like conversion Skills are still stored beside lifecycle Skills
  without an intermediate family label.

These are acceptable during the current documentary reorganization stage.
They should not be treated as the final extraction boundary.

## Next Step

Use this classification together with a concrete business pack dependency map.
The first extracted pack is the business-intake route:

- `business_learning_interview`
- `business_intake_scoping`

For that dependency map, see
[Business Intake Pack Dependency Design](../packs/business-intake/065_business_intake_pack_dependency_design.md#xid-D334C1964342).
