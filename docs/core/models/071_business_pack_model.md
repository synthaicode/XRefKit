<!-- xid: 40511A8A06CD -->
<a id="xid-40511A8A06CD"></a>

# Business Pack Model

This page is the canonical concept page for the Business Pack unit.
It defines what a Business Pack is, what it bundles, and where its boundary
with the AI Agent OS core lies.
It is a concept/model page, not a usage guide and not a pack-specific design.

Related:

- [AI agent OS reorganization design](../../designs/063_ai_agent_os_reorganization_design.md#xid-22CAE81A6D3E)
- [OS utility and business skill classification design](../../designs/064_os_utility_and_business_skill_classification_design.md#xid-ECF29DC3E268)
- [Business intake pack dependency design](../../packs/business-intake/065_business_intake_pack_dependency_design.md#xid-D334C1964342)
- [Business Pack Explained (diagram)](../../../human-docs/diagrams/02_business_pack_explained.md)

## Definition

A Business Pack is **not merely a collection of Skills**. It is a unit that
bundles **Skills, Knowledge, and explicit handoff points** so that one "job"
can be handed to the AI as a whole.

In that bundle:

- the work itself is carried by Skills,
- and the judgment and knowledge that connect those pieces of work are carried
  by Knowledge and explicit handoff.

Progression across the work — the order and boundaries that a Flow layer used
to define — is now carried by each Skill's generic workflow protocol and by
semantic routing, not by a pack-owned flow definition.

So a Business Pack contains both the work and the connecting judgment and
knowledge required to perform a job.

## What It Bundles

| Element | Role in the pack |
|------|------|
| Skill | a concrete unit of work the AI executes |
| Knowledge | the judgment basis loaded as business rules and viewpoints |
| Handoff | the point where one result is passed to the next Skill or to a human |

Progression (order, boundary, handoff sequence) is not a pack-owned element:
it comes from each Skill's workflow protocol and from semantic routing.

## Layer Correspondence

- A **job** (business) maps to one Business Pack.
- A piece of **work** maps to one Skill.
- The **judgment and knowledge** that connect the work map to Knowledge and
  explicit Handoff; the **order** comes from the workflow protocol and semantic
  routing.

Skills are the working parts; Knowledge and Handoff are what make a set of
Skills cohere into a single job rather than scattered actions.

## Purpose

- Let a human hand over a whole job at the job level instead of selecting and
  directing one Skill per piece of work (no micro-management).
- Move AI-verifiable quality checks to the AI side, so a human holds only the
  judgment points that genuinely need a human.
- Keep job-specific quality viewpoints inside the pack while shared Quality
  Gates stay in the OS core.

## Boundary With The OS Core

- The pack owns: job-specific Skills, judgment Knowledge, handoff points,
  and pack-specific quality viewpoints.
- The OS core owns: runtime control, guard, routing, closure, and audit.
- The pack depends on the OS core but must not redefine it. See
  [OS utility and business skill classification design](../../designs/064_os_utility_and_business_skill_classification_design.md#xid-ECF29DC3E268).

## How A Pack Is Defined

The canonical, machine-checkable definition of a pack is its manifest at
`skills/packs/<pack>/pack.md`. The manifest declares:

- `owns_*`: the assets this pack owns exclusively (its work Skills and
  Knowledge),
- `uses_*`: shared references that may live anywhere, including the OS core,
- `depends_on.os_contract_version`: the OS-core contract the pack depends on.

Validate manifests with `python -m xrefkit pack lint`. The linter checks that owned
assets resolve, that ownership is exclusive across packs, that an owned Skill
does not live in the OS core, and that the declared OS-core contract version
still matches the live contract.

The first pack defined this way is the business-intake pack; see
[Business intake pack entry](../../packs/business-intake/066_business_intake_pack_entry.md#xid-732E41DCA2E8).

## Non-Goals

- It is not a technology-stack template.
- It is not a plain folder classification.
- It does not endorse one giant pack that absorbs everything.
