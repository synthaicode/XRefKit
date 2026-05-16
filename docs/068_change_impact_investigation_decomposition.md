<!-- xid: 14733B9B4F61 -->
<a id="xid-14733B9B4F61"></a>

# Change Impact Investigation Decomposition

This page clarifies how `change impact investigation` should be decomposed in
XRefKit when the work is broadly reusable but still depends strongly on domain
knowledge.

This page is a design note.
It does not replace the investigation workflow, capability definitions, or
usage guides.

Related:

- [Investigation workflow](032_investigation_workflow.md#xid-8B31F02A4001)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Change analysis skill usage](054_change_analysis_skill_usage.md#xid-C5A8F13D7E21)
- [CAP-INV-002 Change Impact Enumeration](../capabilities/investigation/110_cap_inv_002_source_dependency_analysis.md#xid-E994FCDA8CD1)

## Core Point

`change impact investigation` is reusable enough to define as a shared
capability, but it does not execute well without domain-tuned knowledge.

That means the reusable structure is not one flat artifact.
It is a layered composition:

- pack:
  - where this investigation sits in the business progression and handoff
- capability:
  - the reusable impact-enumeration ability
- skill:
  - the executable investigation procedure for one technical context
- knowledge:
  - the domain-specific viewpoints, rules, and evidence categories that make
    the investigation meaningful

## Software Development Decomposition Table

| Layer | What it owns | Reuse level | Example in software development | What changes by domain |
|------|------|------|------|------|
| `Pack` | why this investigation is being done, where it hands off, what later work consumes it | medium | `investigation pack` before requirements / planning / design | handoff target, owner group, required artifacts, escalation meaning |
| `Capability` | reusable ability to enumerate impacts and preserve unknowns | high | [CAP-INV-002 Change Impact Enumeration](../capabilities/investigation/110_cap_inv_002_source_dependency_analysis.md#xid-E994FCDA8CD1) | almost none; the core ability stays stable |
| `Skill` | how to run the investigation against a concrete technical surface | medium | `dotnet_change_analysis`, `external_definition_change_analysis` | repository scan strategy, viewpoint buckets, target artifact kinds |
| `Knowledge` | what counts as relevant evidence, dependency, boundary, or activation condition | low to medium | `.NET` structure viewpoints, XML/config-driven activation viewpoints, domain rules | strongly domain-dependent |

## What Is Actually Reusable

The following parts of change impact investigation are highly reusable:

| Reusable part | Why it is reusable |
|------|------|
| identify the change trigger | every change investigation starts from a requested difference |
| enumerate directly affected targets | every system has direct impact points |
| enumerate indirect dependencies | every system has second-order effects |
| keep evidence and inference separate | investigation quality depends on traceability |
| preserve `unknown` instead of guessing | missing evidence is a stable investigation concern |
| produce test viewpoints | downstream validation always needs impact-based checks |

These belong mainly in capability and shared investigation method.

## What Must Be Domain-Tuned

The following parts depend heavily on the technical or business domain:

| Domain-tuned part | Why it changes |
|------|------|
| what counts as a dependency | code call graph, DB relation, XML mapping, event route, batch chain, and approval flow are different kinds of dependency |
| what counts as activation | runtime registration, DI, annotation, XML enablement, scheduler settings, and feature flags differ |
| what counts as a boundary | module, service, job, screen, table, document, and approval step boundaries differ |
| what counts as important evidence | source code, definitions, schema, logs, config, operations docs, and business rules differ |
| what test viewpoints matter most | UI behavior, batch timing, transaction effect, retry behavior, report output, or downstream integration may dominate depending on the system |

These belong mainly in domain knowledge and skill-specific execution details.

## Example 1: .NET Line-Of-Business Application

| Layer | Concrete example |
|------|------|
| `Pack` | investigation work before requirements or design for a requested feature or bug change |
| `Capability` | enumerate controller, application service, repository, DB, logging, batch, and test impacts |
| `Skill` | [dotnet_change_analysis](../skills/dotnet_change_analysis/SKILL.md#xid-D94E3B3A7C11) |
| `Knowledge` | [Common source analysis criteria](../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001), [Custom framework common criteria](../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002), [Dotnet change analysis viewpoints](../knowledge/source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201) |

What changes here:

- dependency often means code references, DI registration, DB access, API calls,
  logging hooks, and test targets
- activation often means route registration, service wiring, attribute use, or
  startup configuration

## Example 2: External-Definition-Driven Enterprise Application

| Layer | Concrete example |
|------|------|
| `Pack` | investigation work before deciding how to modify XML or configuration-controlled business behavior |
| `Capability` | enumerate definition file, activation rule, consuming code, transition, validation, scheduler, and downstream impact |
| `Skill` | [external_definition_change_analysis](../skills/external_definition_change_analysis/SKILL.md#xid-8C1F3DA2B6E4) |
| `Knowledge` | [Common source analysis criteria](../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001), [Custom framework common criteria](../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002), [External-definition change analysis viewpoints](../knowledge/source_analysis/130_external_definition_change_analysis_viewpoints.md#xid-4D91A26BE301) |

What changes here:

- dependency often means definition-to-code mapping, load order, runtime
  activation condition, transition target, and operations configuration
- activation cannot be inferred from file presence alone; the consuming
  mechanism must be verified

## Practical Rule

When you want to generalize `change impact investigation`, generalize in this
order:

1. capability:
   - keep the reusable impact-enumeration skeleton stable
2. skill family:
   - split execution by technical control surface such as source-code-driven or
     external-definition-driven
3. knowledge:
   - load the domain-specific viewpoints that make the capability meaningful
4. pack:
   - decide where the investigation sits in the business progression and where
     it hands off next

Do not generalize by pretending the same investigation can run without domain
knowledge.

## Pack Versus Capability In This Case

For this kind of work:

- `capability` answers:
  - what reusable investigation ability is needed?
- `pack` answers:
  - why is this investigation being done here, and what does it hand off to?

That is why `change impact investigation` can be one shared capability while
still appearing in different packs:

- an `investigation pack`
- a `delivery pack`
- a domain-specific migration pack

The capability stays shared.
The pack meaning changes with progression, boundary, and handoff.

## Design Implication

If XRefKit later extracts an `investigation pack`, it should not duplicate
`CAP-INV-002`.

Instead:

- keep `CAP-INV-002` as the shared impact-enumeration capability
- keep multiple investigation Skills for different technical surfaces
- keep domain-tuned knowledge fragments for each analysis context
- let the pack define the business progression and next handoff
