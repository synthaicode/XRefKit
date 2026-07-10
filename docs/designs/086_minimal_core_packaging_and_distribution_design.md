<!-- xid: D0EEC9A16307 -->
<a id="xid-D0EEC9A16307"></a>

# Minimal Core Packaging and Distribution Design

Status: proposal. This page records the target model reached by design
discussion on 2026-07-05: what the XRefKit core is, how it is packaged and
distributed, and how Skill content is distributed separately from it.

It builds on, and does not restate:

- [Base control and xref routing layers](../core/models/017_base_and_xref_layering.md#xid-5A1C8E4D2F90)
  — the original extraction boundary this page finally executes.
- [Deterministic flow control kernel design](073_deterministic_flow_control_kernel_design.md#xid-4C7E9A2B1D63)
  — the workflow protocol this page treats as enforcement interface 1.
- [Repository layout zones design](080_repository_layout_zones_design.md#xid-5C1F8A2D7E43)
  and [Repository layout MCP catalog design](081_repository_layout_mcp_catalog_design.md#xid-C8B7A1E940D2)
  — the zone and multi-root catalog model this page turns into distribution
  units.
- [Client authoring and unified supply design](082_client_authoring_and_unified_supply_design.md#xid-B0572E20DFBA)
  — local content, adoption paths, dynamic knowledge selection.
- [Skill-centric architecture consolidation](083_skill_centric_architecture_consolidation.md#xid-9DF3B80F9CBE)
  — the Skill + Knowledge + protocol + routing layer model.
- [Skill domain knowledge runtime input design](085_skill_domain_knowledge_runtime_input_design.md#xid-BC6C6D89E4E1)
  — the runtime knowledge input shape consumed by Decision 2.
- [OS utility and business skill classification design](064_os_utility_and_business_skill_classification_design.md#xid-ECF29DC3E268)
  — the Skill classification reused for pack slicing.

## Basis

Three oppositions define what XRefKit is. They are a dependency chain, not
parallel slogans:

- **Prompt → Contract**: a rule is a contract only when violation is defined
  and the text is version-fixed (XID + content hash). Wording alone is a
  prompt.
- **Review → Enforcement**: a control is enforcement only when a
  non-conforming path physically cannot proceed. Inspection that can be
  skipped or rubber-stamped is review.
- **Memory → Durable Direction**: what persists is human-authored normative
  direction (what should be), not an accumulation of what the AI experienced
  (what happened).

Durable Direction gives Contract its content; Contract without Enforcement is
a solemn prompt. Direction-setting is a human responsibility as a matter of
category, not capability: methods that place the criterion inside the AI
(self-consistency, judge agents, self-evaluation) fail because the checker
shares the failure class of the checked. The working subject for producing
AI-readable text is the AI; the human checks and accepts. Acceptance, not
authorship, is where the human responsibility lives.

## Decision 1: The Core Enforces Two Things and Supplies One

The core imposes exactly two obligations on a Skill:

1. **Workflow protocol conformance** — a Skill run is valid only inside the
   run → verify → close envelope.
2. **XID uniqueness** — identifiers must not collide across the merged asset
   space (core + packs + local + external roots). The enforcement point is
   catalog merge time, because that is the first moment the full space
   exists.

And it supplies one thing:

3. **The unified knowledge catalog** — core roots, pack roots, local roots,
   and external domain-knowledge roots merged into one list, delivered over
   MCP. Supply, not enforcement.

Everything else — the meta triad, `knowledge_slots` shape, SKILL.md
structure, guard and contract wording — is convention or delivered content,
not an enforcement interface. Consequence: `fm skill check` splits into two
tiers:

- **enforcement tier** (blocks execution): protocol conformance, XID
  uniqueness and resolvability;
- **lint tier** (warnings): meta shape, triad vocabulary, slot syntax and
  other conventions.

Mixing the tiers either fattens the interface (killing pack-side freedom) or
hollows the contract. The core is a runtime/loader, not an SDK: the analogy
is the CLR enforcing IL verification and strong names while dictating no code
style.

## Decision 2: Skill Anatomy — Container Is Free, Judgment Is Required

```text
Skill = container            (Agent Skills SKILL.md format is acceptable)
      + knowledge-use judgment  (the defining property of an XRefKit Skill)
      + the two enforced interfaces (protocol, XID)
```

The knowledge-use judgment is: declare the knowledge need in meta (slots per
[085](085_skill_domain_knowledge_runtime_input_design.md#xid-BC6C6D89E4E1)),
receive the merged catalog at run time, select the fragments for the task
(non-deterministic, inside the Skill), and record the selected XIDs +
content hashes in the run log. The judgment is what lets base Skills consume
local knowledge with zero edits — the fork-surface-minimization mechanism.

Skills published on the public ecosystem do not ride on XRefKit: they are
mostly thin deterministic wrappers with no judgment, because judgment over
knowledge can only be written where a knowledge supply exists. The boundary
is the catalog, not the format. Intake of external Skills is re-authoring by
tri-decomposition, not conversion:

- deterministic procedure → **code** (tools / fm);
- judgment → **Skill**;
- facts → **knowledge**.

If nothing remains after decomposition but deterministic steps, the artifact
should have been a script, not a Skill. XRefKit participates in the public
Skill ecosystem only at the raw-material level.

The judgment a Skill carries is structured as **judgment axes** — the named
viewpoints the Skill judges by (for a review Skill: security,
synchronization, error policy, traceability, …; the viewpoint structure of
[083](083_skill_centric_architecture_consolidation.md#xid-9DF3B80F9CBE)
D1). The runtime division of labor: the human states the goal and policy;
the AI selects the way of proceeding from Skills (routing); the Skill's axes
frame the judgment; along those axes, domain knowledge is used toward the
goal. Judgment is never unframed — each layer's criterion is supplied from
one layer above. Operationally: a Skill whose axes cannot be named is a
script, and human acceptance of a Skill is acceptance of its axes.

## Decision 3: The Filesystem Is the Source of Truth

The catalog model is mount + scan: assets become supply by existing under a
declared root. No registration step, no upload. This is a keystone, not a
default:

- registration drift (index/content divergence) is structurally absent;
- the AI writes a file and discovery is complete — no forgettable
  registration call;
- MCP-less startup
  ([080 startup contract](../core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22))
  requires that the truth be readable without a server;
- git-untracked local packs can be served only because the scan reads the
  filesystem, not Git;
- an instance is files + manifest, so copying is migration.

The one discipline: indexes (search, embeddings) and state (approval,
maturity) are always derived caches or sidecar files. Nothing may be more
authoritative than the files.

## Decision 4: Python Packaging, uv Distribution

The three interfaces are language-neutral: assets are Markdown, run records
are JSON, delivery is MCP. The implementation language is a detail behind
the interfaces, so the existing Python implementation stays and is packaged
as one tool:

```text
xrefkit (pip package, distributed via uv tool)
  xrefkit init                 instance bootstrap (materialize startup
                               contract, generate manifest)
  xrefkit run / verify / close protocol
  xrefkit xid init|check       XID service
  xrefkit check skill|knowledge  enforcement + lint tiers
  xrefkit mcp serve            MCP server (same core, thin stdio mouth)
```

Distribution point: git tags on this repository. No feed infrastructure —
`uv tool install git+<repo>@core-v1.2.0`. The target machine needs only the
`uv` single binary; uv downloads a managed CPython on demand, so a local
Python installation is not a prerequisite.

The portable specification is not the code but the **fixture corpus**:
sample Skills, run-log JSON, expected check results, kept under `tests/`.
With fixtures, a future port (for example to a dotnet tool) is a mechanical
parity job. Reconsideration triggers for a dotnet port, recorded so they are
not re-litigated: a deployment target where Python/uv is prohibited, or
sustained hand-debugging where owner-language fluency dominates.

## Decision 5: Repository Layout — Core plus First Instance

The repository stays one repository playing three roles: core source, pack
source, and the first instance (dogfood).

```text
XRefKit/
├─ pyproject.toml           package definition; ships src/xrefkit only
├─ src/xrefkit/             everything distributed
│   ├─ cli.py
│   ├─ protocol/            skillrun / gate / goalstate / ctx (from fm/)
│   ├─ xid/                 xref (from fm/; dependency-free)
│   ├─ catalog/             scan, merge, XID collision check,
│   │                       startup-pack assembly
│   ├─ mcp/                 stdio server + control_reminder attachment
│   └─ contracts/           base-control set as package data,
│                           materialized by `xrefkit init`
├─ fm/                      remains: dashboard / ownership / packmeta
│                           (instance ops tools) + back-compat shim
├─ xrefkit.manifest         this instance's root declarations
├─ packs-src/               pack sources (Decision 6)
├─ skills/ knowledge/ …     unpacked instance content
├─ packs/local/             local overlay, gitignored
└─ tests/                   fixture corpus
```

The `src/` boundary is itself enforcement: the installed package physically
contains no instance content, so "core cannot reference packs" is guaranteed
by build, not by convention. Known surgery: `skillmeta`'s import of
`ownership` becomes injected configuration so the core does not know the
zone model.

The separate XRefKit.MCP repository becomes unnecessary. Its catalog
construction and startup-pack assembly move into `src/xrefkit/catalog/`
(they are core logic shared with the CLI); only the stdio transport and the
per-response `control_reminder` remain in `src/xrefkit/mcp/`. The old
repository is archived, not deleted.

## Decision 6: Pack Distribution — Two Artifact Kinds

Code and content are distributed differently:

| | core | Skill pack |
| --- | --- | --- |
| content | code (three interfaces) + contracts | Markdown + meta, XID-bearing |
| form | pip package (`uv tool install`) | file tree fetched by manifest |
| lands in | PATH command | `packs/<name>/` scan root |
| version | `core-vX.Y.Z` tag | `<pack-id>-vX.Y.Z` tag |

Packs are not pip packages: content must stay scannable, inspectable, and
overlayable as files (Decision 3). Each pack carries a `pack.toml` (id,
version, **requires_core**, zone metadata, content hash list). `xrefkit
sync` resolves the manifest: fetches declared packs, verifies
`requires_core`, and runs the XID collision check across all merged roots —
the Decision-1 enforcement point. Installed packs are treated as immutable;
local modification necessarily goes to `packs/local/` shadowing, which
completes the fork-as-overlay model.

Pack identity uses a dotted namespace under the core:

```text
installed:
  xrefkit                      core (uv tool)
  xrefkit.skill.csharp         work bundle: C# review / change analysis
  xrefkit.skill.sqlserver      work bundle: DB design / current-state analysis
  xrefkit.knowledge.common     knowledge-only pack (cross-cutting fragments)
```

`xrefkit.skill.<domain>` names a work bundle; `xrefkit.knowledge.<name>`
names a knowledge-only pack. Tags follow the id
(`xrefkit.skill.csharp-v0.4.0`). The naming gives the family view
(`xrefkit pack list` shows what work this instance can take on) while the
mechanism stays Decision-3 file trees, never site-packages.

**The granularity is a bundle of work, not micromanagement.** A pack is the
unit in which an instance accepts a kind of work — "can this environment
take on C# work?" is answered by one install. Per-Skill packages are
rejected: a lone Skill cannot accept a complete piece of work (preconditions
chain it to its companions), per-Skill versioning explodes the dependency
graph, and semantic routing needs a candidate set, not a single procedure.

Slicing criteria, in priority order:

1. **co-evolution** — what changes together ships together (domain knowledge
   with the Skills that mainly consume it);
2. **selective adoption** — cut where another instance could plausibly want
   the unit without the rest;
3. **tuning-axis alignment** — pack names should match the triad tuning
   vocabulary.

Do not slice by lifecycle phase: flow Skills chain through preconditions and
do not stand alone. The full-slicing map, held as a blueprint and not
executed up front: OS utility Skills ship with core
([064](064_os_utility_and_business_skill_classification_design.md#xid-ECF29DC3E268));
`xrefkit.skill.sdlc` (lifecycle flows + quality gates);
`xrefkit.skill.csharp`; `xrefkit.skill.sqlserver`;
`xrefkit.skill.office-docs`; a shared `xrefkit.knowledge.common` for
cross-cutting fragments (preferred over cross-pack references to keep the
dependency graph flat).

**Initial scope is deliberately minimal**: `core-v*` plus
`xrefkit.skill.csharp` only. Everything else stays as unpacked instance content. The trigger for
cutting a further pack is a second instance actually requesting it —
evidence before freezing, applied to distribution.

## Migration Order

1. Mechanical relocation into `src/xrefkit/` + `pyproject.toml` + `fm/`
   shim. No behavior change; verified by existing tests and
   `python -m fm xref check`.
2. `packs/local/` gitignore + migrate remaining `*_private/` content.
3. Tag and `uv tool install` into a separate directory — first portability
   proof.
4. Vertical-slice run on the packaged form: one Skill through
   [085](085_skill_domain_knowledge_runtime_input_design.md#xid-BC6C6D89E4E1)
   slot resolution, full run → verify → close, resolved XIDs + hashes in the
   run log. The human evaluation point is designed in: acceptance criteria
   for this run are written by the human before the run.
5. Freeze the run-log / meta / check outputs as the fixture corpus under
   `tests/`.
6. Carve `packs-src/csharp/` and validate `pack.toml` + sync checks on that
   one pack.
7. Integrate MCP (`xrefkit mcp serve`), switch client configs, archive
   XRefKit.MCP.

## Non-Goals

- No dotnet port now (triggers recorded in Decision 4).
- No pack slicing beyond `xrefkit.skill.csharp` (trigger recorded in
  Decision 6).
- No feed infrastructure (git tags suffice until a real second consumer).
- No change to the guard delivery model
  ([082](082_client_authoring_and_unified_supply_design.md#xid-B0572E20DFBA)
  Decision 4) or to XID discipline.
- `adopt_knowledge` implementation and the L3 approval-record / sidecar
  state design are separate follow-ups.

## Open Points

- Exact injected-configuration shape for decoupling `skillmeta` from
  `ownership`.
- Whether the XID collision check at merge lives in `catalog/` (shared) or
  is re-run by `mcp/` per refresh.
- `xrefkit.knowledge.common` boundary once a second pack exists.
