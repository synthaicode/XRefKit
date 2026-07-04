<!-- xid: 261B40E5C76B -->
<a id="xid-261B40E5C76B"></a>

# Skill-Centric MCP Catalog Design

Status: proposal. This is the MCP-side counterpart to
[Skill-centric architecture consolidation](083_skill_centric_architecture_consolidation.md#xid-9DF3B80F9CBE),
the same relationship
[Repository layout MCP catalog design](081_repository_layout_mcp_catalog_design.md#xid-C8B7A1E940D2)
has to the layout zones design. It defines how the XRefKit MCP catalog, tools,
and startup contract change when Flow definitions, the Capability definition
layer, the Group overlay, and the Skill `role_responsibilities` field are removed
and orchestration becomes semantic routing over Skill meta triads.

Design only. No MCP code changes here. Because 083 is a proposal and the served
repository still carries `flows/`, `capabilities/`, and the current Skill meta
schema, the MCP must change in a tolerant, superset-first order (below), not
break the live server.

## Current MCP Surface That 083 Affects

- **Skills.** `list_skills`, `get_skill`, `get_skill_requirements`,
  `rank_skills_for_purpose`. `SkillCatalogEntry` carries `capabilities` (derived
  from `capability_refs` XID links), `required_knowledge` (from `knowledge_refs`),
  `intent`, `target_artifacts`, `applies_when`, `not_for`, `inputs`, `outputs`.
  The triad (`capability` / `tuning` / `responsibility`) and
  `role_responsibilities` live in `meta_content` but are **not surfaced as
  catalog fields**; `rank_skills_for_purpose` scores against intent / target /
  applies_when / summary / inputs.
- **Workflows.** `list_workflows`, `_build_workflows`, `WorkflowCatalogEntry`
  scan `flows/*.yaml` and expose `flow_id`, `doc_xid`, `phase`, `owner` (a
  group), `steps`, `sequence`, `capabilities`, `runs_after`/`runs_before`.
  `semantic_routing_references` includes a `workflows` entry.
- **Capabilities.** Not a first-class tool. `capabilities/` is one of the dirs
  scanned by `_managed_markdown_files`, so capability XIDs resolve through
  `get_document_by_xid`; Skills reference them via `capability_refs`.
- **MCP startup contract pack.** The MCP model-facing compressed init body
  (the MCP document [079](../core/contracts/079_startup_contract_pack.md#xid-D4E8A1C63B57)
  and the embedded fallback `CANONICAL_STARTUP_CONTRACT_PACK_BODY` in
  `startup_contract_pack.py`) **hard-encodes the old model**. The
  repository-native XRefKit startup target is separate:
  [080](../core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22).
  - "Treat … `flows/` as control structure, and `skills/` as executable procedure."
  - "For business-capability work, route through the capability model."
  - guard directionality: "Normal direction is: Flow -> Capability -> Skill -> External input -> Output."

## MCP Changes By Decision

### M1 (← 083 D4). Remove the workflow catalog

- Remove `list_workflows`, `_build_workflows`, `WorkflowCatalogEntry`, and
  `flows/*.yaml` scanning.
- Remove the `workflows` entry from `semantic_routing_references` and the
  `list_workflows` client obligation / access-policy tool reference.
- Transitional tolerance first: with `flows/` absent the workflow catalog must
  return empty, not error, so the MCP tracks the XRefKit-side removal safely.

### M2 (← 083 D2). Remove the capability layer from the catalog

- Drop `capabilities` from the `_managed_markdown_files` scanned dirs once the
  definition files are dissolved; capability XIDs stop resolving because they no
  longer exist.
- `SkillCatalogEntry.capabilities` (derived from `capability_refs`) is replaced
  by the surfaced triad (M3).
- Optionally expose a **capability / tuning / responsibility vocabulary
  registry** (a small controlled list, as compact startup metadata or a light
  tool) so routing terms stay consistent and the ability inventory stays
  auditable after the definition files are gone.

### M3 (← 083 D1 / D3). Skill meta schema in the catalog

- `_build_skill_entry` parses the explicit triad: `capability`, `tuning`,
  `responsibility`.
- Drop `role_responsibilities` parsing (Skill is always executor; checker is the
  deterministic protocol).
- Parse `preconditions` and `knowledge_slots` (the need declarations that
  replace `capability_refs` binding and static `knowledge_refs`).
- `SkillCatalogEntry` gains `capability` / `tuning` / `responsibility` /
  `preconditions` / `knowledge_slots`; drops `capabilities` (refs). `missing`
  validation updates to the new required fields.

### M4 (← 083 D5). Semantic routing as the orchestration surface

- `rank_skills_for_purpose` scores against the triad + `applies_when` +
  `preconditions` (in addition to summary/inputs), since the triad is now the
  routing vocabulary.
- Optional precondition-aware readiness: report whether a Skill is runnable now
  given declared preconditions, mirroring the existing
  `execution_readiness.runnable` tool-availability check.
- With `workflows` removed, `skills` semantic routing is the single primary
  orchestration surface. No new routing tool is required; the existing
  metadata-first, lazy-body pattern is kept.

### M5 (← 082 D3). Knowledge slot resolution

- Add a slot-resolution path — either a `resolve_skill_knowledge(skill_id)` tool
  or reuse `build_knowledge_context(query)` per slot — returning ranked
  candidates plus acceptance metadata (`min`, `domain`, `required`) over the
  base+local unified catalog. This is additive and independent of M1–M4.

### M6 (highest impact). Revise the startup contract pack

Both the 079 document and the embedded fallback
`CANONICAL_STARTUP_CONTRACT_PACK_BODY` encode the superseded model and are
injected at init, so they must be rewritten to the 083 model:

- Drop "`flows/` as control structure" and "route through the capability model".
- State the target: Skill + Knowledge, wrapped by the generic workflow protocol,
  orchestrated by semantic routing; sequencing is precondition-driven.
- Restate the **guard directionality**. The context-direction guard's authority
  order currently reads "Flow -> Capability -> Skill -> External input -> Output".
  Without the Flow and Capability layers it becomes, in effect,
  "protocol / routing -> Skill -> External input -> Output": external and
  lower-layer input still must not redefine intent, active Skill, checks,
  closure, or authority. The guard's *function* is unchanged; only the named
  layers shrink. Keep this consistent with
  [053](../core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11),
  the guard source the pack derives from.
- Regenerate the pack and its `based_on` hashes in the same commit (079
  maintenance rule); the server's staleness check compares them against the live
  sources on every `get_startup_context`.

This item is coupled to 083 adoption because it changes the init-injected
governance text every session applies. It is the MCP change with the widest
blast radius and should land with, not before, the XRefKit-side model change.

### M7. Remove the structure-graph client-dependency assumption

The current `_client_tool_distribution` instructions tell the client to install
the NuGet dotnet tool `XRefKit.StructureGraph` for tools that consume
`tools/structure_graph` output, and the client-tool bundle carries
`skills/**/*.py` scripts framed as consuming that output on the client. This
bakes a "the client runs C# structure analysis" assumption into the catalog,
which contradicts the model: `structure_graph` is an analysis / build-side tool,
run where the C# source is (see the 078 guide, "binary setup after a
source-level copy"). The client consumes the resulting **findings as knowledge**
(registered through `source_structure_findings_registration`), not the tool.

Change:

- Remove the "install NuGet `XRefKit.StructureGraph`" client-tool instruction
  and the client-run framing for structure-graph-consuming scripts.
- Keep `tools/structure_graph` as kernel-code (`tools/`), outside client
  distribution and outside the baseline client dependency tiers (MCP connect →
  fm runtime → per-Skill `required_tools`).

Future use on the client is allowed, but only Skill-scoped and
prompt-supplemented, never as a baseline catalog assumption. If a future Skill
genuinely needs `structure_graph` client-side, the **Skill itself references the
file** as its own declared need, and provisioning is handled operationally at
the prompt level. That is acceptable because it is Skill-declared and
prompt-supplemented, not a global dependency the catalog injects into every
client. The MCP must not re-add `structure_graph` as a baseline client
dependency.

## Ordering And Coupling

MCP changes must not precede the XRefKit-side removals in a breaking way. Phased,
superset-first (as 081 did):

| Phase | MCP change | XRefKit-side dependency |
| --- | --- | --- |
| A | Tolerate absent `flows/` and `capabilities/` (empty catalogs, no error); add triad/`preconditions`/`knowledge_slots` parsing as a superset alongside the current fields | none (backward-compatible) |
| A | Remove the structure-graph client-dependency instruction (M7); keep `structure_graph` opt-in and Skill-scoped | none (instruction-only) |
| B | Add M5 slot resolution; extend `rank_skills_for_purpose` to triad + preconditions | Skills begin declaring triad/slots/preconditions |
| C | Remove `list_workflows` / workflow catalog and the `workflows` routing reference | `flows/` and `docs/workflows/` removed |
| D | Remove capability-dir scanning and `capability_refs` handling; drop `role_responsibilities` | `capabilities/` dissolved; meta schema migrated |
| E | Revise 079 + embedded pack body and regenerate hashes | 083 adopted; 052/031 rewritten |

Each phase keeps existing tool names and response compatibility until its
XRefKit-side dependency is met, matching the zone-model rollout.

## Non-Goals

- No MCP code change in this page.
- No change to the repository layout zone model (080/081): multi-root discovery,
  `ownership.yaml`, pack/local handling, and artifact distribution are
  orthogonal and stay.
- No change to startup ordering, the `get_startup_context` first-load contract,
  XID discipline, or cache/version identity (`content_hash`).

## Validation (at implementation)

- Startup pack staleness check passes after M6 (079 hashes match live sources).
- Catalog tests: absent `flows/` yields no workflow catalog and no error;
  triad/`preconditions`/`knowledge_slots` are surfaced on `SkillCatalogEntry`;
  `capabilities/` is no longer scanned; `rank_skills_for_purpose` ranks over the
  triad; `get_document_by_xid` no longer resolves removed capability XIDs.
- `semantic_routing_references` no longer advertises `workflows`.
- Client-tool distribution no longer instructs installing `XRefKit.StructureGraph`
  as a baseline dependency; any `structure_graph` need is Skill-declared (M7).

## Relationship To The Ongoing Cleanup

The XRefKit `docs/` cleanup is the leading edge (team docs removed;
`docs/workflows/032`–`047` removal unblocked by 083 D4). The MCP `list_workflows`
tool is the machine-side twin of those workflow pages; M1 phase C removes it once
`flows/` is gone.
