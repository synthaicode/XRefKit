<!-- xid: 22CAE81A6D3E -->
<a id="xid-22CAE81A6D3E"></a>

# AI Agent OS Reorganization Design

This page is a design document for reorganizing XRefKit into an explicit AI
agent OS structure.
It is not a usage guide and not a business operating model.
For the boundary among operating models, usage guides, and design pages, see
[Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583).

## Purpose

This page defines how to reorganize the current execution foundation so the
repository is understood and maintained as an AI agent OS with a clear split
between:

- OS core
- business or domain packs
- human-facing design and governance documents

The goal is not to rename the repository and declare success.
The goal is to make the existing control structure explicit enough that future
agent-facing work, business-task onboarding, and reusable runtime control can
evolve without collapsing back into one mixed documentation space.

Related:

- [Overview](000_overview.md#xid-7C6C2B46A9D1)
- [Single-link startup architecture](012_single_link_startup_architecture.md#xid-AB27F6C19DF5)
- [Base control and xref routing layers](017_base_and_xref_layering.md#xid-5A1C8E4D2F90)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61)

## Problem Statement

The repository already behaves like more than a document set.
It carries:

- startup control
- semantic routing
- skill load gating
- execution and check separation
- unknown and risk visibility
- closure enforcement
- handoff structure

However, those mechanisms are still described mainly as repository features.
That makes several things harder than they should be:

- it is not explicit which parts are the reusable agent OS core
- business-specific Flow or Skill work can remain mixed with runtime control
- future extraction or packaging work lacks a stable boundary
- newcomers can still misread the repository as only `xref` plus prompt files

The design problem is therefore not how to invent an OS from scratch.
The design problem is how to expose the existing control plane as an OS core
while keeping business execution content as separately managed packs.

## Design Decision

Reorganize XRefKit around three explicit layers:

1. `OS core`
2. `business or domain packs`
3. `human-facing explanation and governance`

The OS core owns runtime control, loading rules, reference durability, and
execution records.
Business or domain packs own Flow, Capability, Skill, and Knowledge bundles for
concrete work domains.
Human-facing docs explain structure, intent, and migration, but they do not
replace machine-checked runtime control.

Here, OS means an operating layer for controlled AI Agent work, not a
low-level system OS or an LLM runtime.

## Scope

In scope:

- defining the target layer boundary
- mapping current repository areas to the target model
- identifying the minimum OS contract surface
- defining a staged migration path
- choosing the first practical migration target

Out of scope:

- immediate repository split into multiple git repositories
- immediate CLI renaming
- claiming that all existing Skills are already OS-grade
- changing business semantics only to fit a cleaner architecture diagram

## Target Architecture

The target architecture is:

1. startup adapter layer
2. OS core
3. business or domain packs
4. work records and audits
5. human-facing design and governance layer

The interaction is:

1. a tool-specific startup file loads one shared entry
2. the startup entry applies base control first
3. the OS core performs routing, load gating, and runtime-record creation
4. the selected business pack provides Flow, Capability, Skill, and Knowledge
5. execution results, checks, judgments, and handoff records are written to
   controlled work logs
6. human-facing docs explain and govern the structure without becoming the
   runtime itself

Those work logs are not only audit trails.
They are operational memory used to improve Skills, Knowledge, guard policies,
routing rules, and quality gates after execution.

## Core Boundary

### OS Core

The OS core is the part that should remain reusable across business domains.

It owns:

- startup contract shape
- context-direction guard
- uncertainty and `unknown` handling
- skill runtime envelope
- execution and check role separation
- closure gate
- handoff rule
- `xref` durability and lookup commands
- runtime log structure
- judgment-log linkage
- audit and quality-gate enforcement
- operational-memory feedback into Skill, Knowledge, guard, routing, and gate improvement

These controls are already visible in the current repository and should be
treated as the kernel of the agent OS rather than as incidental repo
conventions.

### Business Or Domain Pack

A business or domain pack is the part that defines what concrete work the agent
is doing. This is the business work (業務) the OS exists to execute — the
purpose of the OS, not a demonstration of it. The OS core is the reusable
substrate; business packs are why that substrate exists.

It owns:

- business progression in `Flow`
- reusable professional work-unit definitions in `Capability`
- executable procedure in `Skill`
- evidence, facts, and local rules in `Knowledge`
- domain-specific examples, scoping logic, and output expectations

The pack may depend on the OS core, but it should not redefine the core control
contract.

### Human-Facing Design And Governance

This layer explains and evaluates the system.
It owns:

- human-readable architecture pages
- operating-model pages
- usage guides
- migration guidance
- boundary explanations and rationale

It must not be treated as the mechanism that enforces runtime correctness.

## Current-To-Target Mapping

| Current area | Target role in AI agent OS model | Notes |
|------|------|------|
| `agent/` | OS core entry and startup contract | keep short and load-first |
| `fm/` | OS runtime and reference engine | core execution and enforcement surface |
| `docs/011`, `015`, `016`, `017`, `052`, `053`, `058`, `059` | OS core design and governance docs | already describe most core behavior |
| `skills/` | business or domain packs, plus a small number of OS-authoring utilities | separate core utilities from domain Skills explicitly |
| `capabilities/` | business or domain pack ability definitions | not evidence, not runtime engine |
| `knowledge/` | business or domain pack evidence and local rules | loaded on demand through OS routing |
| `flows/` | machine-readable business progression control | should remain business-pack side unless the flow is OS-internal |
| `work/` | OS runtime records and operational memory | keep auditable, improvement-oriented, and separate from canonical docs |
| vendor startup files | startup adapters | remain thin and link-based |

## Minimum OS Contract Surface

The minimum OS contract surface should be treated as the stable interface that
business packs rely on.

It includes at least:

- startup entry rule
- semantic routing rule
- `fm skill run` load gate
- work-item recording
- artifact recording
- concern recording for `unknown`, `risk`, and `judgment`
- phase transition recording with assigned roles
- closure gate enforcement
- handoff-source validation
- XID-based lookup and rewrite
- runtime-log audit

If one of these elements changes, that change is an OS contract change, not
only a local documentation edit.

## Directory Reorganization Direction

The first reorganization step should be conceptual and documentary, not a large
filesystem move.

The intended direction is:

- make OS-core documents easier to identify as one family
- distinguish OS utility Skills from business execution Skills
- keep business packs grouped by business responsibility rather than by tool
- preserve current links and runtime commands until the contract boundary is
  stable

This means the first iterations may keep the existing top-level directories
while tightening their role labels and entry pages.

## Migration Stages

### Stage 1: Name The Boundary

- publish the AI agent OS design boundary
- identify which current pages are OS-core pages
- identify which current Skills are OS utilities versus business Skills
- keep runtime behavior unchanged

### Stage 2: Stabilize The Core Contract

- treat startup, routing, runtime envelope, closure, and audit as one contract
- remove ambiguous wording that makes these controls sound optional
- document compatibility expectations for business packs

### Stage 3: Separate Business Packs Explicitly

- group business-oriented Flow, Capability, Skill, and Knowledge assets by
  responsibility boundary
- stop mixing OS-control explanation into business-pack documents unless the
  interaction point is explicit
- add missing pack-level entry pages where needed

### Stage 4: Extract Or Package Only If Justified

- evaluate whether the OS core should remain in one repository or be extracted
- only move files after the interface is stable enough that business packs do
  not break
- keep `xref` and skill-runtime compatibility explicit during any extraction

## First Practical Migration Target

The first migration target should be one concrete business execution path rather
than a repo-wide rename.

Recommended first target:

1. choose one business pack with clear learning, scoping, and execution
   boundaries
2. map its Flow, Capability, Skill, and Knowledge assets explicitly
3. list every place where that pack depends on OS-core control
4. remove or rewrite any mixed explanation that blurs the boundary

The business-intake route is a strong candidate because it already shows the
split between:

- semantic routing
- business learning
- scope shaping
- later execution handoff

## Design Rules

- Do not describe business packs as if they are the OS.
- Do not treat business packs as demonstrations of the OS; the OS exists to
  execute business work (業務) efficiently, so business is the purpose, not a
  sample.
- Define business (業務) from established domain knowledge (industry standards
  and established practice), not from self-styled invention; this prevents
  reinventing the wheel and avoids baking defects into the design.
- For the deterministic part of a task (作業), prefer reusing established OSS
  over building bespoke tools (reuse-before-build).
- Do not bury OS-core controls inside business-only explanations.
- Do not claim extraction readiness before compatibility boundaries are named.
- Do not treat `xref` as the whole OS; it is one core subsystem.
- Do not treat design pages as enforcement; machine-checked runtime controls
  remain authoritative.

## Risks And Open Gaps

- Some existing Skills that look architecturally central are not fully
  load-ready under the current runtime gate.
- The current repository structure still mixes control-plane and business-pack
  assets under common top-level families.
- The naming system does not yet expose an `os-core` family directly.
- Actual `fm/` module boundaries have not yet been re-sliced for extraction.

These gaps do not block the design page.
They do block any claim that the OS reorganization is already complete.

## Minimal Implementation Plan

Phase 1:

- add this design page
- update entry pages to point to the AI agent OS framing
- identify OS utility Skills and business Skills explicitly

Phase 2:

- add an OS-core index or boundary page family
- define compatibility rules for business packs
- choose the first business pack and document its dependency map

Phase 3:

- apply targeted directory and index cleanup
- tighten runtime validation where business-pack assumptions are still implicit
- evaluate extraction or packaging only after the contract is stable

## Why This Design Is Preferred

This design is preferred because it matches the repo's actual control model.

The repository is already enforcing more than storage and more than prompting.
It already has the beginnings of an OS contract:

- controlled startup
- routed loading
- load gating
- execution and checking separation
- visible uncertainty
- auditable closure
- explicit handoff

Making that contract explicit gives the repository a cleaner center of gravity.
It also lets business execution content evolve as managed packs instead of
forcing every future change to argue about the whole repository at once.
