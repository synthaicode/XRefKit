<!-- xid: C8B7A1E940D2 -->
<a id="xid-C8B7A1E940D2"></a>

# Repository Layout MCP Catalog Design

Status: proposal. This page defines the MCP-side design that supports the
repository layout zone model in
[Repository layout zones design](080_repository_layout_zones_design.md#xid-5C1F8A2D7E43).

The repository layout design defines where content should live. This page
defines how XRefKit MCP discovers that content, reports it to clients, and keeps
distribution boundaries explicit after `packs/` and `ownership.yaml` are added.

## Problem

The current MCP catalog assumes fixed repository roots for the main content
families:

- `skills/**`
- `knowledge/**`
- `flows/**`
- `capabilities/**`

That assumption becomes incomplete once packs become first-class physical units.
The MCP server must discover content from both kernel roots and pack roots
without making local-only content distributable by accident.

The MCP side must also preserve the existing startup contract:

- `get_startup_context` remains the first governance-content load.
- XID resolution remains lazy through `get_document_by_xid`.
- Skill bodies remain separate from metadata-only routing.
- client-tool downloads remain gated by selected Skill need.

## Design Goals

- Make catalog discovery zone-aware.
- Treat `ownership.yaml` as the repository-published source of path ownership and
  distribution intent.
- Add pack roots as a superset of the existing roots before moving content.
- Keep XID identity stable across physical moves.
- Keep local packs visible to the local MCP server but excluded from base
  distribution and base-sync worklists.
- Preserve metadata-first routing and lazy body materialization.

## Non-Goals

- No change to the MCP protocol names solely because content moves.
- No startup-time loading of all pack content.
- No server-side execution of Skills.
- No automatic approval of local pack content into base-owned zones.
- No repository split between kernel and business content.

## Source Of Truth

MCP catalog construction should read a root-level `ownership.yaml` when present.
If the file is missing, MCP should use the current fixed-root behavior and report
that ownership metadata is unavailable.

The declaration should give the MCP server these facts:

- path patterns for each zone
- owner class: `base`, `pack`, `local`, `operational`, or `generated`
- catalog eligibility
- distribution eligibility
- whether the zone can shadow base content

The MCP server should expose the interpreted zone model as metadata in catalog
responses. The exact tool shape can evolve, but clients need enough information
to distinguish:

- base-owned content
- shared pack content
- local-only pack content
- records and generated content
- delivery/runtime artifacts

## Content Roots

MCP discovery should become multi-root:

```text
skills       = skills/**       + packs/*/skills/**       + packs/local/*/skills/**
knowledge    = knowledge/**    + packs/*/knowledge/**    + packs/local/*/knowledge/**
flows        = flows/**        + packs/*/flows/**        + packs/local/*/flows/**
capabilities = capabilities/** + packs/*/capabilities/** + packs/local/*/capabilities/**
```

The `packs/local/*` roots are catalog-visible for the local repository instance
that serves them. They are not base-distributable.

Generated, operational, and delivery zones are not content-catalog roots unless a
specific MCP tool is designed for that purpose.

## Catalog Entry Metadata

Every catalog entry from a zone-aware root should include:

- `path`
- `xid` when available
- `content_hash`
- `content_family`: `skill`, `knowledge`, `flow`, or `capability`
- `zone`
- `owner`
- `pack_id` when the entry comes from `packs/<pack>/`
- `local_only`
- `distribution`
- `forked_from` when the entry shadows or forks base content

`content_hash` remains the version identity for cache invalidation. A separate
model-facing `version` field is not needed when it would duplicate
`content_hash`.

## Shadowing And Forks

Pack content may intentionally shadow base content by stable identity:

- Skills shadow by `skill_id`.
- Markdown documents and knowledge fragments shadow by XID.
- Flows and capabilities shadow by their declared identifiers, and by XID when
  present.

When two entries share the same stable identity, MCP must not silently choose one
without reporting the relationship. The catalog should classify the result as:

- `base`: no shadow exists
- `fork`: local or pack entry declares `forked_from`
- `conflict`: more than one entry claims the same identity without an explicit
  provenance relation

Routing tools may prefer the local fork for the local repository instance, but
the response must expose the base entry and the selected entry so clients can
audit the decision.

## Startup Behavior

`get_startup_context` should not expand pack catalogs at startup.

It may include compact root-policy metadata such as:

- whether `ownership.yaml` was found
- the hash of the interpreted ownership model
- enabled content root families
- whether local packs exist
- any blocking catalog conflicts discovered during lightweight root scanning

Startup references remain XID-based. Pack links are resolved later through
`get_document_by_xid` or the relevant catalog tool only when the task needs them.

## Tool Surface

Existing tools remain valid:

- `list_skills`
- `rank_skills_for_purpose`
- `get_skill`
- `get_skill_requirements`
- `list_workflows`
- `search_knowledge_catalog`
- `get_knowledge_summary`
- `expand_knowledge`
- `build_knowledge_context`
- `get_document_by_xid`

The first MCP-side implementation should add zone awareness behind these tools
before introducing new public tools.

Optional follow-up tools may be added when client behavior needs them:

- `get_repository_zones`: return the interpreted `ownership.yaml`.
- `list_packs`: return pack ids, owners, locality, and root paths.
- `get_pack`: return `pack.md` metadata and catalog summary for one pack.
- `check_catalog_conflicts`: return shadowing and duplicate-identity findings.

## Client-Tool Distribution

Client-tool distribution must follow zone metadata:

- `tools/**/*.py` remains part of the core client-tool package.
- `skills/**/*.py` remains available through client-tool file or bundle
  distribution after a Skill is selected.
- `packs/*/skills/**/*.py` follows the same Skill-selected distribution rule.
- `packs/local/*/skills/**/*.py` is local-only and must not be included in base
  snapshot or public package outputs.

The MCP response for a selected Skill should tell the client which tool files are
required and whether each file is base-distributable or local-only.

## XID Resolution

`get_document_by_xid` must resolve XIDs across all catalog-eligible roots.

If exactly one document has the XID, return it normally.

If a local or pack fork shadows a base XID, return the selected local document and
include the base document metadata in a `shadowed` or `forked_from` block.

If multiple documents claim the same XID without an explicit fork relation, fail
closed with a conflict response. Do not choose based on path order.

## Catalog Version

`catalog_version` should include the interpreted zone model and all
catalog-eligible content roots. At minimum it should change when any of these
change:

- `ownership.yaml`
- root-level Skills, knowledge, flows, or capabilities
- shared pack catalog content
- local pack catalog content served by this repository instance
- pack metadata such as `pack.md` or `bindings.yaml`

Generated artifacts such as `site/` should not affect `catalog_version`.

## Validation

MCP-side validation should cover:

- `ownership.yaml` parses and every declared path stays inside the repository.
- every catalog-visible pack has a `pack.md`.
- duplicate identity claims are either explicit forks or conflicts.
- local-only zones are excluded from base-distribution outputs.
- generated and record zones do not appear in normal Skill, knowledge, flow, or
  capability catalogs.
- `get_document_by_xid` resolves moved content by XID after `python -m fm xref
  fix`.
- client-tool bundles include pack Skill scripts only after Skill selection.

## Migration Plan

| Phase | MCP change | Repository layout dependency |
| --- | --- | --- |
| 0 | Parse `ownership.yaml` and expose interpreted zone metadata internally | `ownership.yaml` exists |
| 1 | Expand catalog scanners to multi-root discovery | before any content moves |
| 2 | Add shadow/fork classification and conflict responses | before local forks or pack pilot |
| 3 | Include pack Skill scripts in selected-Skill client-tool distribution | before pack Skills need scripts |
| 4 | Add optional pack/zone inspection tools if client workflows require them | after catalog behavior stabilizes |

Each phase should keep existing MCP tools backward compatible.

## Open Decisions

1. Whether `get_repository_zones` is needed as a public tool or whether zone
   metadata inside existing catalog responses is sufficient.
2. Whether local pack shadowing should be enabled by default or require an
   explicit server flag.
3. The exact conflict response schema for duplicate XIDs and duplicate Skill
   identifiers.
4. Whether `packs/local/*` should be included in `catalog_version` for all local
   clients or only when local packs are enabled.
