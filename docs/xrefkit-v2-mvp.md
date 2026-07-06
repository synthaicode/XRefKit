# XRefKit v2 MVP

This document describes the implemented XRefKit v2 MVP surface.

The MVP is intentionally narrow. It proves the vertical path from a text-only
Skill Package to a Project Local Skill, resolver output, CLI display, package
discovery, and JSONL run-log validation.

## Purpose

XRefKit v2 is a shared context supply and governance base for AI work.

It is not only RAG, not only a prompt collection, and not only an MCP tool
gateway. The MVP focuses on:

- loading repository-independent Skill Packages
- mounting Project Local assets
- resolving a Local Domain Skill that extends a Pack Skill
- including reusable text fragments by XID without changing inheritance
- generating an `EffectiveSkillBundle`
- keeping source trace and content hashes visible
- separating referenced, loaded, and used XIDs

## Responsibility Boundaries

### Core

Core is executable Python code.

Current MVP Core responsibilities:

- Pydantic v2 models
- file loaders
- Python entry point discovery
- package, skill, knowledge, and XID registries
- single-inheritance resolver
- `EffectiveSkillBundle` builder for entry bundles
- CLI display for tree and resolved JSON
- JSONL run-log reader/writer and aggregate validation
- minimal MCP-tool-shaped facade without SDK wiring

Core must not contain project-specific domain knowledge or technical judgment
criteria such as C# rules, SQL Server rules, or site-specific templates.

### Skill Package

A Skill Package is a reusable text asset package.

The MVP assumes text-only packages:

- Skill definitions
- Skill entry text
- required fragments
- reusable include fragments
- on-demand branches
- knowledge
- review axes
- schemas
- `package_manifest.yaml`

Python packaging is used for distribution and discovery only. The MVP does not
execute package code as a tool.

### Project Local

Project Local contains project-specific assets:

- Local Domain Skills
- project knowledge
- output templates
- project schemas
- project review axes
- `local_manifest.yaml`

Project Local can extend Pack Skills, inject project knowledge, and bind output
templates. It cannot weaken Core contracts or Pack Skill contracts.

### Shared MCP

Shared MCP is the intended team-facing runtime surface.

The current MVP does not yet wire an actual MCP SDK server. It provides a thin
MCP-tool-shaped facade that calls the resolver. This is deliberately not a tool
gateway for arbitrary package execution.

## Python Distribution Model

The implemented sample package is:

- distribution name: `xrefkit-skills-xddp-design`
- import package: `xrefkit_skills_xddp_design`
- XRefKit package id: `xrefkit.skills.xddp.design`
- entry point group: `xrefkit.skill_packages`
- entry point: `xddp_design = xrefkit_skills_xddp_design:package_root`

`package_root()` returns the package asset root containing
`package_manifest.yaml`.

Installed packages are only discovered. Discovery does not enable them for
resolver use. A package must be explicitly enabled by package id before it is
registered for resolution.

## xrefkit.skills.xddp.design Structure

The sample package lives at:

```text
packages/xrefkit-skills-xddp-design/
├─ pyproject.toml
├─ README.md
└─ src/
   └─ xrefkit_skills_xddp_design/
      ├─ __init__.py
      ├─ package_manifest.yaml
      ├─ skills/
      │  ├─ change_design.skill.yaml
      │  ├─ common/
      │  │  └─ traceability_instruction.md
      │  └─ change_design/
      │     ├─ entry.md
      │     ├─ fragments/
      │     │  ├─ traceability_required.md
      │     │  └─ unknowns_required.md
      │     └─ branches/
      │        ├─ db_schema_change.md
      │        └─ external_interface_change.md
      ├─ knowledge/
      │  ├─ traceability_principles.md
      │  └─ unknown_handling_principles.md
      ├─ review_axes/
      │  ├─ traceability_completeness.yaml
      │  └─ unknown_visibility.yaml
      └─ schemas/
         └─ change_design.schema.json
```

The package provides:

- package id: `xrefkit.skills.xddp.design`
- skill id: `xddp.design.change_design`
- required outputs:
  - `traceability`
  - `unknowns`
  - `assumptions`
  - `used_xids`
  - `change_design`

The Skill entry and required fragments are `required_inline`.
Branches are `on_demand`.

Reusable instruction fragments that may be loaded by `includes` must be
published through `package_manifest.yaml` `provides.fragments`.

Example:

```yaml
provides:
  fragments:
    - id: xddp.traceability_instruction
      xid: xid-include-xddp-traceability-instruction
      path: skills/common/traceability_instruction.md
```

This is intentionally different from skill-internal required fragments such as
`skills/change_design/fragments/traceability_required.md`. Required fragments
belong to the Skill contract and are loaded through the Skill definition.
Reusable include fragments are package-level assets published for explicit
`includes` loading.

## Local Skill Extends Example

Sample Project Local:

```text
samples/xrefkit-v2/order-system/xrefkit.local/
├─ local_manifest.yaml
├─ skills/
│  └─ order_change_design.skill.yaml
├─ knowledge/
│  └─ current_spec.md
└─ templates/
   └─ change_design_report.md
```

The Local Domain Skill extends the Pack Skill:

```yaml
skill_id: project.order_change_design
xid: xid-project-skill-order-change-design
type: domain_skill_wrapper

xrefkit:
  extends:
    - ref: xrefkit.skills.xddp.design::xddp.design.change_design
      xid: xid-skill-xddp-design-change-design
      version: ">=0.1.0 <1.0.0"
      mode: contract_inheritance

  includes:
    - xid: xid-include-xddp-traceability-instruction

  injects:
    knowledge:
      - xid-project-order-current-spec

  output:
    template_xid: xid-template-project-order-change-design-report

  required_outputs:
    - applied_skills
```

`extends` expresses contract inheritance.
The XID identifies the referenced Skill asset; it does not represent
inheritance itself.

`includes` loads reusable text fragments by XID. It is mechanical context
assembly, not contract inheritance and not domain knowledge injection. In the
MVP, include order follows YAML list order, and duplicate include XIDs within
one bundle build are skipped with an `info` conflict entry.

Included fragments become `loaded_xids` with load reason `include_fragment` and
must appear in fragment-level `source_trace`. They do not become `used_xids`
unless the runtime later records that the loaded fragment was actually used as
judgment basis.

### Includeable Assets

`includes` can target only reusable instruction fragments that are published by
a package manifest under `provides.fragments`.

The XID registry stores file-backed assets with:

- `asset_type`
- `includeable`

MVP `asset_type` values are:

- `skill`
- `fragment`
- `knowledge`
- `review_axis`
- `schema`
- `template`

In the MVP, `includeable=true` is set only for assets declared in
`provides.fragments`. Skill-internal entry, required fragments, and branches are
file-backed assets for source trace and content hashing, but they are not
include targets.

The following assets must not be loaded through `includes`:

- knowledge: use `injects`
- template: use `output`
- schema: use `output`
- review axis: use `review_axes`

If a Local Domain Skill specifies an include XID that is not an includeable
fragment, resolution fails with an error that identifies the XID and the actual
asset type. This is a resolution error, not an error conflict entry.

Duplicate include XIDs in one resolution are skipped as `info` conflicts with
code `include_skipped_duplicate`. The first occurrence remains loaded.

## CLI Examples

Package discovery:

```powershell
python -m xrefkit package discover
python -m xrefkit package discover --json
```

Package list with explicit enabled package:

```powershell
python -m xrefkit package list --enabled-package xrefkit.skills.xddp.design
python -m xrefkit package list --json --enabled-package xrefkit.skills.xddp.design
```

Show effective Skill as a tree:

```powershell
python -m xrefkit show effective-skill project.order_change_design `
  --mode tree `
  --package-manifest packages/xrefkit-skills-xddp-design/src/xrefkit_skills_xddp_design/package_manifest.yaml `
  --local-manifest samples/xrefkit-v2/order-system/xrefkit.local/local_manifest.yaml
```

Show resolved `EffectiveSkillBundle` JSON:

```powershell
python -m xrefkit show effective-skill project.order_change_design `
  --mode resolved-json `
  --package-manifest packages/xrefkit-skills-xddp-design/src/xrefkit_skills_xddp_design/package_manifest.yaml `
  --local-manifest samples/xrefkit-v2/order-system/xrefkit.local/local_manifest.yaml
```

`resolved-json` is not full materialization. The word `full` is reserved for
true full materialize.

## EffectiveSkillBundle

`EffectiveSkillBundle` is the resolver output for the current Skill resolution.

In the MVP it contains:

- effective Skill id
- resolution mode
- base contracts
- loaded text references with content hashes and load reasons
- included reusable fragments loaded by XID
- referenced knowledge, templates, schemas, review axes, and branches
- required outputs after merge
- fragment-level source trace
- conflict and warning slots

The bundle does not contain `used_xids`. Used XIDs are runtime evidence records
and belong in the Run Log.

## Run Log JSONL

Run Log JSONL is the canonical event-log format.

Each line is one event. Examples of event types:

- `run.start`
- `context.resolved`
- `xids.referenced`
- `xids.loaded`
- `xids.used`
- `unknowns.reported`
- `assumptions.reported`
- `branch.loaded`
- `conflict.detected`
- `run.complete`

`RunLogAggregate` validates run-level consistency, including:

- all events share the same `run_id`
- `run.start` exists
- `run.complete` appears at most once
- event timestamps are monotonic
- `used_xids` is a subset of `loaded_xids`

YAML or Markdown run-log views are human exports, not the canonical format.

## referenced_xids / loaded_xids / used_xids

`referenced_xids`:

- XIDs presented as candidates or references.
- Body text may not be loaded.
- Useful for navigation and possible follow-up loading.

`loaded_xids`:

- XIDs whose body text was loaded into resolver or execution context.
- Each loaded XID carries a content hash and load reason.
- Loading does not mean the source was used as judgment basis.
- Included fragments are loaded XIDs with load reason `include_fragment`.

`used_xids`:

- XIDs actually used as evidence or judgment basis.
- Must be loaded first.
- `used_xids` belongs to Run Log events, not `EffectiveSkillBundle`.

## Not Implemented In MVP

The following are intentionally not implemented:

- true full materialize
- actual MCP SDK server wiring
- executable Skill Package
- SSO/OAuth
- automatic package install
- automatic package download
- multiple inheritance
- advanced branch condition DSL
- full workflow engine

True full materialize is reserved for a future mode and must include:

- all branch bodies
- referenced knowledge bodies
- output template and schema bodies
- review axis bodies
- source trace and content hash for every materialized asset
- `human_full_only` assets

## Wheel Build Verification

The `xrefkit-skills-xddp-design` package was verified as buildable with:

```powershell
python -m pip wheel --no-deps --wheel-dir .tmp/xrefkit-skills-xddp-design-dist packages/xrefkit-skills-xddp-design
```

Verified wheel contents:

- `xrefkit_skills_xddp_design/__init__.py`
- `xrefkit_skills_xddp_design/package_manifest.yaml`
- `xrefkit_skills_xddp_design/skills/change_design.skill.yaml`
- `xrefkit_skills_xddp_design/skills/change_design/**/*.md`
- `xrefkit_skills_xddp_design/knowledge/*.md`
- `xrefkit_skills_xddp_design/review_axes/*.yaml`
- `xrefkit_skills_xddp_design/schemas/*.json`
- `.dist-info/entry_points.txt`

Verified entry point:

```text
[xrefkit.skill_packages]
xddp_design = xrefkit_skills_xddp_design:package_root
```

The wheel was also installed into an isolated virtual environment with
`--no-deps`; `package_root()` returned the installed package asset root and
`package_manifest.yaml` was present.
