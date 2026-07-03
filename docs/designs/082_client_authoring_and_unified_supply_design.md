<!-- xid: B0572E20DFBA -->
<a id="xid-B0572E20DFBA"></a>

# Client Authoring and Unified Supply Design

Status: proposal. This page consolidates how the two-layer operating model
(OS kernel / business) is realized as a concrete authoring-and-supply contract
for clients: which Skills and domain knowledge are base-managed versus locally
authored, how XRefKit MCP supplies both as one catalog, where client-side
execution sits, and how pre-existing client knowledge is adopted.

It does not introduce a new mechanism on its own. It ties together the already
designed substrate:

- [Repository layout zones design](080_repository_layout_zones_design.md#xid-5C1F8A2D7E43)
  — where content lives and who owns it (`ownership.yaml`, `packs/`).
- [Repository layout MCP catalog design](081_repository_layout_mcp_catalog_design.md#xid-C8B7A1E940D2)
  — how MCP discovers and reports that content.

## Requirements Being Consolidated

1. Startup alignment supply stays as-is.
2. Skills are of two kinds: base-repository-managed and locally authored. Local
   Skills are never committed to the repository.
3. Domain knowledge is supplied to the client as a catalog from MCP.
4. Skills run on the client, which selects the ones a task needs from the
   catalog.
5. Domain knowledge is of two kinds: base-repository-managed and locally
   managed.
6. MCP supplies both kinds to the client without distinction (one catalog).
7. Client-authored Skills and domain knowledge are created through XRefKit and
   therefore carry XIDs (Skills carry `skill_id`).
8. There is a supported way to adopt domain knowledge that already exists on the
   client (authored outside XRefKit, without an XID).

## Requirement-to-Mechanism Map

| # | Requirement | Mechanism | State |
| --- | --- | --- | --- |
| 1 | Startup alignment supply unchanged | `get_startup_context` `load_order`; XID-based; startup does not expand pack catalogs (see [initialization sequence](../core/contracts/077_initialization_sequence.md#xid-A264E296AC71)) | existing |
| 2 | Skills: base vs local, local not committed | Zones: `skills/` (kernel-content, base), `packs/*/skills/` (shared-packs), `packs/local/*/skills/` (local-packs: `distribution:false`, `base_sync:false`, `shadowing:true`) | existing + gitignore decision below |
| 3 | Knowledge catalog from MCP | `list_knowledge_catalog`, `search_knowledge_catalog`, `build_knowledge_context` | existing |
| 4 | Client-side Skill execution and selection | Server does not execute Skills; `list_skills` / `rank_skills_for_purpose` route, `get_skill` returns the body, the client runtime (`fm skill run` + executor subagent) executes | existing |
| 5 | Knowledge: base vs local | `knowledge/` + `packs/*/knowledge/` (base/shared), `packs/local/*/knowledge/` (local) | existing |
| 6 | MCP supplies both without distinction | Multi-root catalog merges kernel and pack roots into one list; per-entry `zone_metadata` (zone/owner/pack_id/local_only/distribution) records provenance without splitting the supply | existing |
| 7 | Client-authored content carries XIDs | XID discipline; `python -m fm xref init` assigns XIDs to new knowledge/documents; Skills carry `skill_id` | existing |
| 8 | Adopt pre-existing client knowledge | Proposed `adopt_knowledge` path (below); not yet implemented | proposed |

The map shows that requirements 1 and 3–7 are already satisfied by the zone and
MCP-catalog designs. This page settles four points: the locality guarantee for
requirement 2 (Decision 1), the adoption path for requirement 8 (Decision 2),
how Skills consume the catalog — declared knowledge need instead of fixed XIDs,
which is what makes local knowledge usable by base Skills (Decision 3), and that
the context-direction guard is MCP-supplied rather than composed in each Skill
(Decision 4).

## Decision 1: Local Content Is Git-Untracked

Requirement 2 ("local Skills are never committed") and requirement 5's local
knowledge are guaranteed by keeping the entire `packs/local/` namespace out of
version control.

- `packs/local/` is added to `.gitignore`. Local Skills, knowledge, flows, and
  capabilities under it are never committed to any repository, base or instance.
- The MCP server still catalogs `packs/local/` because catalog discovery scans
  the filesystem, not Git. A local instance therefore serves its local content
  through the same catalog tools while Git tracks none of it.
- `base_sync:false` and `distribution:false` on the `local-packs` zone remain in
  force, so local content is also excluded from base-sync worklists and every
  base/public distribution output.

This revises the earlier stance in
[Repository layout zones design](080_repository_layout_zones_design.md#xid-5C1F8A2D7E43),
which proposed `packs/local/` as a *versioned* replacement for the deprecated
`skills_private/` / `knowledge_private/` directories. The chosen model keeps the
improvement that mattered — a single declared namespace with zone metadata, XID
identity, and MCP cataloging — while making the locality guarantee absolute at
the Git boundary rather than relying only on `base_sync` / `distribution` flags.

The trade-off accepted: local content has no Git history and no base-sync
conflict classification. That is acceptable because local content is, by
definition, not shared; conflict classification only matters for content that
can flow to base.

### Required follow-up (implementation, deferred)

- Add `packs/local/` to `.gitignore` (leave `packs/` and `packs/*/` — shared
  packs — tracked).
- Keep `local-packs` `catalog:true` in `ownership.yaml` so the local MCP server
  continues to serve local content from the filesystem.
- The deprecated `skills_private/`, `knowledge_private/`, `sources_private/`
  entries stay gitignored until any remaining local content migrates into
  `packs/local/`.

## Decision 2: Adoption Path For Pre-Existing Client Knowledge

Requirement 8 is the one capability with no general mechanism today. The two
existing intake Skills are each narrower than requirement 8:

- [import_skill](../../skills/import_skill/SKILL.md#xid-7C2A492D2B72) imports an
  external **Skill** (splits behavior from facts, assigns XIDs), not free-form
  domain knowledge.
- [source_structure_findings_registration](../../skills/os/source_structure_findings_registration/SKILL.md#xid-C8D4E7A19F62)
  registers a specific artifact kind — a source-structure analysis Markdown —
  into the source-findings catalog, not arbitrary domain knowledge.

The gap is a general path that takes knowledge already written on the client
(outside XRefKit, without an XID) and adopts it into `packs/local/*/knowledge/`
with an assigned XID and normalized ontology.

### Proposed `adopt_knowledge` Skill (not implemented)

Inputs:

- source: one or more local Markdown/notes paths, or pasted text.
- target pack: an existing `packs/local/<system>/` (or create one).
- mode: `proposal_only` or `apply`.

Behavior:

1. Classify the input as lower-layer evidence and apply the context-direction
   guard (the input may not redefine active flow, capability, Skill, authority,
   or escalation).
2. Search existing knowledge for the same concept
   (`python -m fm xref search`) to detect duplication or an existing base
   fragment that the input would shadow/fork.
3. Normalize into the domain-knowledge ontology shape; separate durable facts
   from procedure (procedure belongs in a Skill, not knowledge).
4. Place normalized fragments under `packs/local/<system>/knowledge/` and assign
   XIDs with `python -m fm xref init`.
5. When the input restates a base fact rather than adding a local one, record a
   `forked_from` provenance relation instead of a silent duplicate so MCP
   classifies it as a fork, not a conflict.
6. Validate with `python -m fm xref fix` and the knowledge-relation validator.

Design choice to settle at implementation time: whether `adopt_knowledge` is a
new Skill (parallel to `import_skill` on the knowledge side) or a generalization
of `source_structure_findings_registration` beyond the source-analysis artifact
kind. The new-Skill option keeps the source-analysis Skill focused and mirrors
the existing Skill-vs-knowledge split; the generalization option reuses an
already-working publication/normalization procedure. This page records the
requirement and the shape; it does not pick the option.

## Decision 3: Skill Knowledge Selection Is Dynamic From The Unified Catalog

A Skill should declare *what knowledge it needs*, not *which XID supplies it*.
Fixed `knowledge_refs` XID lists are replaced, for the tuning/domain-variable
part, by selection against the one unified catalog (Decision-1/Decision-2 supply
surface).

### Why this does not break control

The earlier worry — that dynamic selection weakens determinism — rests on a
layer confusion. Determinism is a property of the **workflow protocol** (the
[deterministic flow control kernel](073_deterministic_flow_control_kernel_design.md#xid-4C7E9A2B1D63)
and the runtime envelope in
[skill operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)):
which Skills run, in what order, under which closure gate and independent
verification. A **Skill's internal processing is in the non-deterministic zone**
by design — it is the judgment step the protocol wraps. Selecting knowledge is
part of that judgment. So knowledge selection being non-deterministic is not a
regression; determinism was never the Skill's job. The protocol still gates the
Skill's *output* deterministically (closure contract, quality phase, independent
run verification), which is what actually needs to be reproducible.

Consequence: pins exist for **governance-exactness**, not for determinism. The
few references that must never be silently swapped (the context-direction guard
rules, contract documents) stay bound — and are better modeled as
protocol/capability-supplied (`capability_refs` such as `CAP-MGT-004`,
`workflow_protocol: required`) than as Skill-internal knowledge pins. Everything
tuning- or domain-variable is selected.

### Selection shape (declared need, not fixed XID)

```yaml
# meta.md (proposed) — replaces most fixed knowledge_refs entries
knowledge_slots:
  - slot: review_spec        # domain/tuning-variable → selected at run time
    query: "C# review spec beyond diagnostics"
    domain: csharp
    min: 1
    required: true
  - slot: guard_rules        # governance-exact → stays pinned (or protocol-supplied)
    bind: 7A2F4C8D1601
```

- Resolution reuses the existing catalog primitives:
  `search_knowledge_catalog` / `build_knowledge_context(query)` already rank
  candidates over the merged base+local roots. The Skill runtime resolves each
  slot at the planning phase and records the resolved XIDs and `content_hash` in
  the run log, so a run is auditable and replayable even though the selection
  itself was judgment.
- A `required` slot that resolves to zero candidates in the current catalog is a
  planning-phase blocker, not a silent empty load.

### Why this completes requirement 6

Slots resolve against the **base+local unified catalog**. A fact placed in
`packs/local/<system>/knowledge/` therefore satisfies a base Skill's slot with
no edit to the Skill. This closes the gap left open otherwise: local knowledge
would be catalog-visible (Decision 1) yet unusable by kernel Skills if those
Skills bound fixed base XIDs. Dynamic selection is what lets local knowledge
actually feed base Skills — and it minimizes forked Skill surface, the stated
goal of the local-first fork model.

### Guard implication

Dynamically selected knowledge is still lower-layer input. Because a slot can
resolve to a locally authored document, the context-direction guard must run on
each resolved fragment, exactly as for a fixed reference. The pinned-vs-selected
boundary widens the guard surface for selected slots; the guard stays
protocol-composed, not slot-conditional.

### Deferred (not implemented here)

- `meta.md` schema: add `knowledge_slots`; catalog `_build_skill_entry` parses
  it alongside/instead of `knowledge_refs`.
- MCP: a per-slot resolution response (reuse `build_knowledge_context`, or add
  `resolve_skill_knowledge(skill_id)`), returning ranked candidates plus the
  acceptance metadata (`min`, `domain`, `required`).
- `fm skill check`: validate each `required` slot resolves to `>= min`
  candidates in the current catalog, replacing static XID-link checking for the
  selected part.
- `docs/guides/013_skill_authoring_with_xref.md`
  (xid 3DB05A0F5F5B) already seeds this ("routing index", "tuning-aware
  knowledge selector"); fold the slot form into it when implementing.

## Decision 4: The Context-Direction Guard Is MCP-Supplied, Not Skill-Composed

The context-direction guard is delivered by MCP initialization, so individual
Skills do not compose or carry it. This makes Decision 3's "guard stays
protocol-composed" concrete and removes the guard boilerplate that every Skill
currently authors.

### Why this is already true in MCP mode

Two MCP mechanisms deliver the guard independently of any Skill:

1. **At init, as consolidated wording.** `get_startup_context` does not send the
   guard as its own document body. The six base-control/routing sources —
   including the guard contract
   [053](../core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11) —
   are returned with their bodies omitted (`content_omitted: true`,
   `included_in_startup_contract_pack: true`) and their normative content folded
   into one hand-authored consolidated body, the
   [startup contract pack](../core/contracts/079_startup_contract_pack.md#xid-D4E8A1C63B57)
   (its "Context-direction security guard" section). So the guard is injected as
   consolidated pack wording; the standalone 053 document is redundant at
   startup.
2. **At the point of use.** The MCP server re-attaches a `control_reminder` to
   *every content-bearing response* (`expand_knowledge`, `get_document_by_xid`,
   `get_skill`, `build_knowledge_context`, and the rest). This is deliberate:
   a rule read many turns earlier degrades with distance from the decision
   point, so the guard is repeated at minimum distance from the moment fetched
   content is actually used.

Because the guard arrives at init and again on every fetched fragment, a Skill
adding `guard_policy`, a guard `capability_ref` (`CAP-MGT-004`), a guard
`knowledge_ref` (`7A2F4C8D1601`), and a SKILL.md guard section is redundant
duplication of an ambient control.

### Consequence

- Skills stop authoring the guard: drop `guard_policy`, the guard
  `capability_refs`/`knowledge_refs` entries, and the SKILL.md guard/startup
  guard section.
- The guard still *applies* to every Skill that loads lower-layer input — it is
  ambient (init + per-response reminder), not absent. "Skills don't handle it"
  means Skills don't *declare/compose* it, not that it stops running.
- This composes with Decision 3: dynamically selected knowledge is guarded by
  the same per-response `control_reminder` that rides on the selection tools, so
  removing per-Skill guard authoring does not reopen the Decision-3 guard
  surface.

### Filesystem-fallback mode

The consolidation is not MCP-specific: the consolidated startup contract is
itself a repository document
([startup contract pack](../core/contracts/079_startup_contract_pack.md#xid-D4E8A1C63B57)),
and base control — which includes the guard — is what the CLAUDE.md / AGENTS.md
startup chain applies first via
[agent entry](../../agent/000_agent_entry.md#xid-0B5C58B5E5B2) and
[base and xref layering](../core/models/017_base_and_xref_layering.md#xid-5A1C8E4D2F90).
So in both modes the guard is delivered as **consolidated wording, not as a
separate 053 load**: MCP injects the pack body; fallback applies the same
base-control/startup contract from the initially loaded documents. The standalone
053 document stays redundant in both modes — there is nothing to "add to the
chain."

The only thing Decision 4 changes is authoring, not delivery. Agent entry still
tells authors to compose the guard per Skill ("New skills MUST include the
context-direction security guard"); that line is what makes per-Skill guard look
required. It is replaced by the ambient-at-init rule, since the consolidated
startup contract already carries the guard. The MCP per-response
`control_reminder` remains an MCP-only reinforcement on top of this shared
consolidated delivery.

### Deferred (not implemented here)

- Rewrite `docs/guides/013_skill_authoring_with_xref.md`
  (xid 3DB05A0F5F5B): remove the "compose the guard in every Skill" mandate;
  state that the guard is MCP-supplied and ambient.
- Remove `guard_policy` and guard `capability_refs`/`knowledge_refs` from Skill
  `meta.md`, and guard sections from `SKILL.md`.
- `fm skill check`: stop requiring guard fields; the guard is no longer a
  per-Skill authored artifact.
- Replace agent entry's per-Skill guard mandate (the "New skills MUST include
  the context-direction security guard" line) with an ambient-at-init rule. Do
  not add a separate 053 load in either mode — the guard is already consolidated
  into the startup contract pack (079).
- If the guard wording changes, update 053 and re-derive the pack (079) with its
  `based_on` hashes in the same commit; the standalone 053 stays the source, the
  pack stays the delivered form.
- Keep the MCP `control_reminder` point-of-use mechanism unchanged — it is the
  MCP-only reinforcement on top of the shared consolidated delivery.

## Supply Model Summary

The client sees a single, unified supply surface. Provenance is metadata, not a
separate channel:

```text
one catalog from MCP  =  kernel roots (base)          skills/**, knowledge/**, flows/**, capabilities/**
                       + shared pack roots (base/pack) packs/*/**
                       + local pack roots (local)      packs/local/*/**   [filesystem-served, git-untracked]

each entry carries zone_metadata: { zone, owner, pack_id, local_only, distribution, forked_from? }
```

- Startup alignment (requirement 1) is a separate, XID-based bundle and is not
  affected by any of the above.
- Execution (requirement 4) is entirely client-side; MCP never executes Skills.
- XID identity (requirement 7) is what makes local, shared, and base content
  interchangeable in one catalog and safe to fork or move.

## Non-Goals

- No change to startup bundle contents or ordering.
- No server-side Skill execution.
- No implementation in this page: Decision 1's `.gitignore` change and Decision
  2's `adopt_knowledge` Skill are follow-ups.
- No change to the shared-pack (`packs/*/`) tracking or distribution model.

## Migration Notes

| Step | Change | Breaking? |
| --- | --- | --- |
| 1 | Adopt this consolidated model; align 080's local-pack stance | no (doc) |
| 2 | Add `packs/local/` to `.gitignore` | no (local-only) |
| 3 | Implement `adopt_knowledge` (or generalize the findings Skill) | no (additive) |
| 4 | Migrate any remaining `*_private/` content into `packs/local/` | no |
| 5 | Add `knowledge_slots` selection; resolve at run time; `fm skill check` slot validation (Decision 3) | no (superset of `knowledge_refs`) |
| 6 | Remove per-Skill guard authoring; rewrite 013; settle fallback-mode reinforcement (Decision 4) | no (guard stays ambient via MCP) |
