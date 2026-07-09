<!-- xid: 5C1F8A2D7E43 -->
<a id="xid-5C1F8A2D7E43"></a>

# Repository Layout Zones Design (Ownership-Explicit, Pack-Centric)

Status: proposal. This page designs how the repository should hold its
content going forward, given the base-vs-local operating model: long-lived
local copies, provenance-carrying Skill forks, local packs, and the
base-sync handoff workflow.

## Problem

The two-layer operating model (OS kernel / business) is not reflected in
the repository layout, and ownership of each directory is implicit. Five
forces make this a problem now:

1. **Base/local divergence.** Local copies modify content in place because
   nothing in the layout says which paths are base-owned. The
   `handoff/base_sync` tooling manages the resulting drift, but the layout
   itself keeps generating it.
2. **Distribution boundaries are entangled with layout.** XRefKit MCP
   discovers content by fixed roots (`skills/**`, `knowledge/**`,
   `flows/**`); client-tool distribution ships `tools/**/*.py` and
   `skills/**/*.py`. Layout changes silently change what is distributed.
3. **Business content is scattered.** Pack documents live under
   `docs/packs/`, their Skills and flows in the shared roots, and project
   workspaces at top level (`projects/`). The Business Pack model (see
   [Business Pack model](../core/models/071_business_pack_model.md#xid-40511A8A06CD))
   has no physical home.
4. **Derived content is tracked next to governance.** `site/` (161
   generated files) and `readme.mp4` (7.9 MB) live in the working tree;
   the MP4 alone forced the creation of the `codex/*without-mp4*` snapshot
   branches and their sync automation.
5. **Invisible escape hatches.** `skills_private/` and
   `knowledge_private/` are gitignored, so locally important content is
   invisible to the governance model and to the MCP catalog — the
   local-pack model supersedes them by giving local content a single
   declared namespace (zone metadata, XID identity, MCP cataloging) even
   while it stays git-untracked. See
   [Client authoring and unified supply design](082_client_authoring_and_unified_supply_design.md).

## Non-Goals

- No repository split. Monorepo publishing was decided (see the
  structure_graph NuGet decision) and stays.
- No big-bang rename of kernel roots. `fm/`, `tools/`, `docs/`, `agent/`,
  `skills/`, `knowledge/`, `flows/`, `capabilities/` keep their names and
  places; too many contracts (MCP globs, pip packages, NuGet workflows,
  startup pointers) depend on them.
- No change to the XID discipline. XIDs remain the stable identity that
  makes any physical move safe.

## Design

### 1. Declared zones (`ownership.yaml` at the repository root)

A machine-readable declaration of who owns which paths and how they are
distributed:

| Zone | Paths | Owner | Distributed via |
| --- | --- | --- | --- |
| kernel-code | `fm/`, `tools/`, `tests/` | base | pip packages, `/dist`, NuGet |
| kernel-content | `agent/`, `docs/`, `flows/`, `skills/`, `knowledge/`, `capabilities/` | base | MCP catalog, snapshot copy |
| shared-packs | `packs/<pack>/` | base or pack owner | MCP multi-root |
| local-packs | `packs/local/<system>/` | local instance | never; local-only |
| records | `work/`, `observations/` | operational | not distributed |
| derived | `site/`, `human-docs/` | generated / translation | excluded from catalogs |
| delivery | `handoff/` | base | snapshot copy |

Consumers of the declaration:

- CI lint: on instance repositories, commits touching base-owned zones
  fail unless the file carries a `forked_from` declaration.
- `handoff/base_sync` worklist: zone-aware classification (a change inside
  `packs/local/` is never a sync item).
- fm / MCP: content-root discovery (below).

### 2. Top-level `packs/` as the physical pack unit

The pack contract gets a home:

```text
packs/<pack-name>/
  pack.md          # XID, purpose, owner, target system
  flows/
  capabilities/
  skills/          # new Skills and provenance-carrying forks
  knowledge/       # domain facts; generated facts carry provenance
  bindings.yaml    # slot bindings for kernel Skills
  observations/    # verification evidence
```

- Pilot migration: `business-intake` (its documents currently under
  `docs/packs/business-intake/`, plus its Skills/flows in the shared
  roots) becomes `packs/business-intake/`.
- `packs/local/` is the reserved namespace for instance repositories; the
  base repository documents the contract but keeps the directory empty.
- `projects/` is dissolved case by case: a project that is ongoing work
  with flows/Skills becomes a pack; one that is only records moves under
  `work/projects/`.

### 3. Multi-root content discovery (fm and XRefKit MCP)

Catalogs stop assuming single roots:

```text
skills   = skills/**        ∪ packs/*/skills/**
knowledge = knowledge/**    ∪ packs/*/knowledge/**
flows    = flows/**         ∪ packs/*/flows/**
capabilities = capabilities/** ∪ packs/*/capabilities/**
```

This one feature serves both futures: shared packs in the base repository
and overlay roots for instance repositories (local packs shadowing base
content by XID / skill_id with `forked_from` provenance).

### 4. Derived content leaves the working set

- `readme.mp4` becomes a GitHub Release asset linked from README. This
  removes the reason the `*without-mp4*` snapshot branches exist. The
  snapshot branch is kept during a transition window because existing
  local copies were taken from it.
- `site/` becomes a build artifact: generated by the pages workflow from
  its sources, not tracked in the main branch.

### 5. Deprecations and hygiene

- `skills_private/`, `knowledge_private/`, `sources_private/` are
  deprecated in favor of `packs/local/` — a single git-untracked namespace
  that is catalog-visible to the local MCP server and governed by
  `ownership.yaml` (zone metadata, XID identity). Locality guarantee and
  the `.gitignore` decision are settled in
  [Client authoring and unified supply design](082_client_authoring_and_unified_supply_design.md).
- `skills/_index.md` becomes generated (`fm` subcommand, multi-root
  aware), removing the last hand-maintained catalog.
- Stray working files at the repository root (for example
  `morning-briefing-*.md`) belong under `work/`.

## Why Now Is the Safe Moment

- XID links survive physical moves; `python -m xrefkit xref fix` re-resolves
  paths.
- Downstream copies classify moves as `moved_in_base` (not conflicts)
  through `handoff/base_sync` — verified against the real docs/
  reorganization (25 moves tracked cleanly). Reorganizing before more
  local copies fork minimizes total drift cost.
- MCP startup references and the startup contract pack are XID-based and
  unaffected by paths.

## Impact on Existing Machinery

| Machinery | Impact | Mitigation |
| --- | --- | --- |
| MCP catalog globs | must learn `packs/*` roots | phase 1 before any content moves |
| Client-tool distribution (`skills/**/*.py`) | must include pack roots | same phase 1 change |
| pip/NuGet packaging, `/dist` | none — kernel-code paths unchanged | — |
| base-sync manifest/worklist | path-agnostic (XID-keyed); moves classify as `moved_in_base` | regenerate manifest after each phase |
| `skills/_index.md` routing | generated by `python -m xrefkit skill index --write` | phase 1 follow-up |
| Startup pointers (CLAUDE.md, 011, 077) | none — XID-based | — |

## Migration Plan

| Phase | Content | Breaking? |
| --- | --- | --- |
| 0 | `ownership.yaml` + this design + CI lint | no |
| 1 | multi-root discovery in fm and XRefKit MCP | no (superset) |
| 2 | `packs/business-intake/` pilot; `projects/` disposition | moves (XID-safe) |
| 3 | `readme.mp4` → Release asset; `site/` → build artifact; snapshot-branch transition note | operational |
| 4 | deprecate `*_private/` after local-pack migration | no |

Each phase ends with `python -m xrefkit xref fix` clean, MCP tests green, and a
regenerated base-sync manifest.

## Decision Points

1. `projects/` の各プロジェクトを pack 化するか records 化するか(個別判断)。
2. `site/` を追跡から外す時期(公開パイプラインの変更を伴う)。
3. `readme.mp4` の Release 移行と snapshot ブランチ廃止のタイミング(既存ローカルが
   ZIP 取得経路として使用中のため、移行期間が必要)。
4. Phase 2 のパイロット範囲(business-intake のみか、projects/ の一部も含めるか)。
