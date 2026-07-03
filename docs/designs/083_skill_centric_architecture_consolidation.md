<!-- xid: 9DF3B80F9CBE -->
<a id="xid-9DF3B80F9CBE"></a>

# Skill-Centric Architecture Consolidation

Status: proposal. This page records a target architecture reached by design
discussion. The repository's layered operating model — Flow → Capability →
Skill → Knowledge, plus the Group overlay — accumulated layers that no longer
carry their original weight, once determinism moved to the generic workflow
protocol and knowledge, guard, and selection became runtime-resolved. This page
states the target and why each removed layer collapses.

It builds on, and does not restate:

- [Client authoring and unified supply design](082_client_authoring_and_unified_supply_design.md#xid-B0572E20DFBA)
  — dynamic knowledge selection (Decision 3) and guard consolidation (Decision 4).
- [Deterministic flow control kernel design](073_deterministic_flow_control_kernel_design.md#xid-4C7E9A2B1D63)
  — the generic per-Skill protocol that carries determinism.
- [Flow capability skill knowledge model](../core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
  — the four-layer model this page supersedes on adoption.
- [Capability layering](../reference/031_capability_layering.md#xid-8D50A972BA9F)
  — the capability/tuning/responsibility definitions this page relocates.

## Starting Point

The model layered work as Flow → Capability → Skill → Knowledge, with a Group
overlay assigning ownership. Each layer had a rationale. Three shifts hollowed
several of them:

1. **Determinism moved to the generic workflow protocol** — the per-Skill run
   envelope (`fm skill run/phase/verify/close`, `workflow_protocol: required`),
   not to specific flow definitions. Determinism is a property of the protocol;
   a Skill's internal processing and the selection of what to run are
   non-deterministic judgment.
2. **Knowledge selection became runtime-dynamic** (082 Decision 3) — meta
   declares the need (slots), runtime resolves it against the base+local unified
   catalog.
3. **The guard became ambient / MCP-consolidated** (082 Decision 4) — delivered
   as consolidated startup-contract wording, not composed per Skill.

Once control, knowledge, and guard are supplied by the protocol and runtime, the
layers that existed to carry them become redundant restatements of what now
lives on the Skill, in the protocol, or in the catalog.

## Target Architecture

Two content layers, wrapped by one generic protocol, orchestrated by semantic
routing:

```text
intent + state
   │  semantic routing  (non-deterministic selection; matches Skill meta triad,
   │                     filters by declared preconditions)
   ▼
Skill run  ── wrapped by ──▶  Workflow protocol / kernel
   │                          (generic per-Skill deterministic control:
   │                           phases, verify, close; identical for all work)
   ├─ Skill   = method + meta identity (capability/tuning/responsibility)
   │            + declared needs (knowledge slots, preconditions)
   └─ Knowledge = evidence fragments, resolved dynamically from the slots
                  against the base+local unified catalog
```

- Determinism is per-Skill at the protocol gate.
- Selection (routing) and Skill-internal judgment are non-deterministic — gated
  by the protocol, not made deterministic themselves.

## Decisions

### D1. The triad is Skill meta identity, not runtime-assigned

`capability` / `tuning` / `responsibility` are the Skill's fixed meta identity,
not parameters assigned at execution time. The original intent — decompose into
the triad and assign it per run — was the error, because **tuning and
responsibility are structural, not thin parameters**:

- `responsibility` (implement vs review) determines the Skill's viewpoint
  structure. A review carries axes beyond the function viewpoint (security,
  synchronization, operational resilience, resource efficiency, error policy,
  traceability). A review Skill is not an implementation Skill run with a
  runtime flag; its structure is organized around those risk viewpoints.
- `tuning` (C#, SQL, C#+SQL) bleeds into method and viewpoints, not only
  knowledge. Roslyn-baseline and async/synchronization concerns are C#/.NET
  bound; implementation idioms differ by language.

Because the specialization is structural, it is inseparable from the Skill.
Different triad = different Skill. What is runtime is the task and its concrete
inputs; the triad identifies and selects the Skill.

The one part of specialization that is a pure knowledge axis is carried by
knowledge slots (082 Decision 3): meta declares the need keyed by the triad;
runtime resolves which fragments satisfy it. So "assign at execution" survives
only as **need declared in meta, satisfied at runtime** — for knowledge, not for
the triad.

### D2. The `capabilities/` definition files dissolve

The four-layer model treated capability as the layer that specializes a generic
Flow to concrete work — the binding between generic progression and a specific
task. That construct assumed the specialization was separable from the method.
D1 shows it is not: the specialization is structural and lives on the Skill.

So a `capabilities/` definition file has no distinct residue. Its sections
relocate:

| capability file section | new home |
| --- | --- |
| id / name / summary | Skill meta triad label (routing vocabulary) |
| work_type (judgment/execution) | Skill meta attribute |
| Preconditions / Trigger | **Skill meta** (see D4 — Flow no longer exists to hold them) |
| Inputs / Outputs | Skill meta I/O contract |
| Required Domain Knowledge | knowledge slots (D3 of 082) |
| Constraints | Skill guardrails + operating contract |
| Assignment: Group | removed (D6) |

Capability survives as (1) the Skill meta triad element and (2) the routing
vocabulary. A thin **capability/tuning/responsibility vocabulary registry**
(one controlled list) may replace the definition files to keep routing terms
consistent and preserve the audit-facing inventory of abilities.

### D3. `role_responsibilities` is removed from Skill meta

Every Skill is the executor. The checker is the deterministic protocol
(`fm skill verify`, context-independent by construction), never a Skill-authored
role. With the executor/checker distinction absent on the Skill side, recording
it conveys nothing.

The value previously stored in `role_responsibilities.executor` (for example
"quality check") was never a role — it was the triad's `responsibility`. It
moves to the responsibility element. Independent review does not disappear: it
is itself an executor run of a review responsibility in a separate context, plus
the deterministic verify gate — realized by mechanism, not by a meta label.

### D4. The Flow definition layer is removed

`flows/*.yaml` and `docs/workflows/` are removed. A flow definition is a
pre-baked template of business progression. Once determinism sits in the generic
protocol, a flow definition:

- **does not control** — the per-Skill protocol gate does; and
- **cannot predict** — future business structure is not knowable, so a fixed
  template over-fits the current domain.

A template that neither controls nor predicts is dead weight. The generic
workflow protocol / kernel stays; it is what actually carries deterministic
control, and it is business-independent.

Cross-Skill sequencing that flows encoded ("requirements before design") becomes
**precondition / dataflow-driven**: a Skill declares its preconditions (moved
here from the capability files, since Flow no longer exists), routing proposes
candidates, only Skills whose preconditions are satisfied by current state are
runnable, and each run is gated by the protocol. Order emerges from precondition
satisfaction, not from a template.

### D5. Semantic routing is the orchestration

Semantic routing remains and becomes the primary — and only — orchestration,
replacing flow-defined sequencing. It matches intent + current state against
Skill meta (the triad and `applies_when`), and preconditions filter what is
runnable now. Supporting tools (`list_skills`, `rank_skills_for_purpose`, the
semantic routing references) stay and become central.

Routing is a non-deterministic selection step between deterministically-gated
Skill runs. This is consistent with the determinism boundary: determinism is at
the protocol, not at selection. The trade accepted: structurally-enforced domain
sequencing is lost; routing judgment and precondition declarations carry it,
with per-step protocol gates catching bad selection at the output.

### D6. The Group overlay is removed

Groups (Planning/Design/Manufacturing/Quality/Operations/OR/Coordinator and the
team models) were an organizational metaphor over the functional decomposition.
Their three additions — ownership/authority boundary, handoff topology, and
self-check ownership — are already carried by capability (now Skill identity),
the protocol roles (executor / deterministic checker), and Flow control (now the
protocol). The overlay is redundant.
See [Group definitions](../reference/040_group_definitions.md#xid-8B31F02A4009).
The team operating models and usage guides were already removed; the remaining
group references (`040`, `041`, `021`, and the group-keyed quality feedback in
`042`–`044`) are the remaining rework/removal surface.

## Layer Map (supersedes 052 on adoption)

| Old | Status | New |
| --- | --- | --- |
| Group overlay | removed | — (D6) |
| Flow (definitions) | removed | generic workflow protocol / kernel (control) + semantic routing (orchestration) |
| Capability (files) | dissolved | Skill meta triad + routing vocabulary registry (D1, D2) |
| Skill | kept, enriched | method + meta triad + knowledge slots + preconditions; no role field, no per-Skill guard |
| Knowledge | kept | dynamic slots against base+local unified catalog |

Effective content layers: **Skill + Knowledge**, wrapped by the **generic
protocol**, orchestrated by **semantic routing**.

## Determinism Boundary (restated)

- Deterministic: the workflow protocol per-Skill gate (`verify`, `close`).
- Non-deterministic: routing (selection), Skill-internal judgment, knowledge
  selection.

Non-deterministic steps are gated by deterministic protocol boundaries; they are
not themselves made deterministic. Removing Flow, Capability files, Group, and
the role field does not touch this boundary — those layers were not where
determinism lived.

## Non-Goals

- No implementation in this page. Every deletion and relocation below is a
  deferred follow-up, and most touch non-document governance (skills, flows, MCP
  catalog, kernel code).
- No change to startup / MCP supply (082), the consolidated startup contract
  pack, or XID discipline.
- No change to the repository layout zone model (080/081): packs and local
  content are orthogonal to this layer consolidation.

## Migration (deferred; mostly non-document)

| Step | Change | Surface |
| --- | --- | --- |
| 1 | Adopt this direction; supersede 052 and rewrite 031 to the triad-as-meta + routing model | docs |
| 2 | Remove `role_responsibilities` from meta; drop the requirement in 058 / `fm skill check` | skills, contract, code |
| 3 | Move capability Preconditions/Trigger/IO/Constraints onto Skill meta; replace `capabilities/` with a vocabulary registry | skills, capabilities/, code |
| 4 | Delete `flows/*.yaml` and `docs/workflows/`; move sequencing to Skill preconditions; repoint/retire MCP `list_workflows` / `_build_workflows` and the kernel's flow-execution parts | flows, docs, MCP, kernel |
| 5 | Remove the Group overlay (`040`/`041`/`021`, group-keyed `042`–`044`) and group owners in any remaining flow/skill references | docs, skills |
| 6 | Naming cleanup: "workflow protocol" / "flow control kernel" retain "flow" but now mean generic per-Skill control; reconcile the naming after flow-definition removal | docs, code |

Each step keeps `python -m fm xref check` clean and resolves references before
deleting targets, as done for the team-doc removal.

## Relationship to the Earlier `docs/` Cleanup

The `docs/` organization already in progress is the leading edge of this
direction: the team operating models/guides (a Group artifact) were removed, and
`docs/workflows/032`–`047` were deferred pending the Flow decision. D4 resolves
that deferral — those pages are removed with the Flow layer.
