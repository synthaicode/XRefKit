<!-- xid: 163AD9936979 -->
<a id="xid-163AD9936979"></a>

# Structure Graph as TM Coverage Backstop

This page defines how a deterministic .NET structure graph (extracted with
Roslyn) is used as a coverage backstop for the **Where** step of XDDP — that is,
for spec-out and traceability-matrix (TM) construction.

The structure graph does **not** replace XDDP. The change-requirement
specification, the change design, and every final inclusion verdict remain with
a human or LLM. The graph's only responsibility is to traverse impact candidates
mechanically per change requirement and to expose TM omissions, overlaps, and
over-coupling.

For the XDDP frame this supports, see [XDDP basics](../organization/170_xddp_basics.md#xid-7A2F4C8D1701)
and [XDDP supporting methods](../organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711).
For the analysis viewpoints it feeds, see [Dotnet change analysis viewpoints](120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201).

## Why a Graph and Not a Mark

In derivative development the future change requirement cannot be fully
anticipated. Any scheme that pre-marks code or documents for a future "cut"
breaks down, because the set of locations a change cuts across is decided by the
change requirement and differs every time. A fixed mark encodes one
decomposition; change work needs a requirement-specific one.

XDDP answers this by **not** persisting the cut: when a change request arrives it
performs spec-out, identifies the impacted locations, and builds the TM for that
request. The TM is difference information, generated per change and disposable.

The structure graph follows the same principle:

- It stores only **decomposition-free relation facts** (calls, type references,
  inheritance, implementation, usage, containment, configuration and data
  references, generated artifacts).
- It stores **no cut, no grouping, no "center."**
- When a change requirement is given, a **seed** is set and the TM candidate is
  produced by traversal. The cut is computed, never stored.

## XDDP Three-Artifact Correspondence

| Local term | XDDP term | Owner |
|---|---|---|
| seed + intent | change-requirement specification / USDM / Why·What | human / judgment |
| traverse a relation substrate that loses nothing | spec-out + TM / Where | structure graph |
| write the change method on the cut | change design / How | human / LLM judgment |

The graph owns candidate generation and coverage checking for **Where** only. It
never substitutes the Why / What / How judgments.

## Why the Graph Maps Cleanly onto TM Checks

The TM confirmation items in XDDP correspond to relation queries the graph is
purpose-built for. These are exactly the completeness checks humans perform
worst and a graph performs perfectly, so the graph backstops the single point
where derivative-development misses originate (later discovery of misses,
interference, and side effects).

| TM check | Graph operation |
|---|---|
| Is the identified function/file set sufficient? | reachability coverage check |
| Are there other impacted locations? | seed traversal (caller/callee, shared nodes) |
| Does another change touch the same place? | multi-seed convergence detection |
| Is coupling too high / maintainability too low? | fan-in / fan-out / centrality metrics |

## Design Principles

### 1. The graph stores no cut

Store only relation facts that are independent of any change requirement. Do not
store "for this change, look here." Candidate node and edge kinds in initial
scope:

- Nodes: `solution`, `project`, `file`, `namespace`, `type`, `method`,
  `property`, `field`, `interface`, `external symbol`, `config key`, `db object`
- Edges: `contains`, `declares`, `calls`, `reads`, `writes`, `implements`,
  `inherits`, `references`, `uses-config`, `uses-db`, `generated-from`

### 2. The TM is generated per change requirement

When the change-requirement specification or seed is given, traverse the graph to
produce TM candidates. The TM is a reviewable artifact and is kept **separate**
from the relation substrate; the substrate is permanent, the TM is per-change and
disposable.

### 3. Graph output is candidate, not verdict

Traversal output is an *impacted boundary candidate*, never a confirmed change
target. Final inclusion or exclusion is curated by a human or LLM against the
change-requirement specification, design intent, constraints, prior judgments,
and non-mechanical ripple.

### 4. Seed derivation is an explicit, reviewable step

The seed is **not** a safe given. Mapping the USDM change requirement to concrete
graph seeds (which type / method / config key / db object) is itself the most
error-prone link: if the seed is wrong or incomplete, the traversal coverage
guarantee is void (garbage in). Treat USDM-to-seed mapping as an explicit
reviewable step with recorded rationale, not as an assumed input. A missed seed
is a coverage failure even when traversal is perfect.

### 5. Damp over-reach, do not only chase coverage

The twin failure of missing impact is collecting too much. Traversal through
high fan-in shared nodes (e.g. a logger, a base `Entity`, a shared utility)
floods the TM with irrelevant boundaries and buries the real ones, which is the
classic reason traceability tooling is abandoned. Use fan-in / centrality not
only as a *coupling check* but to **prune or dampen** traversal: stop at
high-centrality utility nodes, or mark them `transit` (a pass-through, not an
impacted target) rather than expanding through them. Traversal direction and
depth are selected per change type (impact / bug / design style), not fixed.

### 6. Define the handoff for non-mechanical channels

Dynamic-resolution channels (reflection, DI container resolution,
convention-based routing, configuration-driven switching, build-configuration
variants) do not appear as static edges, yet they are exactly where brownfield
impact hides — and they overlap with viewpoints the analysis skill already
covers (see the DI, convention-based discovery, configuration boundary, and
build-configuration viewpoints in [Dotnet change analysis viewpoints](120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)).
Define the seam explicitly:

- The **graph** owns static edges only.
- **LLM spec-out** owns the enumerated dynamic channels.
- Dynamic edges discovered during spec-out are **fed back as additional seeds**
  and re-traversed, so the TM converges instead of leaving a silent gap.

Note that many dynamic channels leave a **static footprint in custom attributes**
(`[ApiController]`, `[Route]`, `[FromKeyedServices]`, `[Table]`/`[Column]`,
serialization and mapping markers). That footprint is deterministically
extractable and is captured by the attribute inventory (principle 8), so it is
**not** left to spec-out even though the channel's runtime effect is. Spec-out
keeps only the genuinely non-static residue (reflection over runtime strings,
convention-by-name, configuration-driven switching with no attribute).

### 7. Reuse the existing Roslyn front-end; do not build a second harness

Reuse the verified analyzer-build invocation in `tools/collect_analyzer_sarif.py`
rather than standing up a parallel Roslyn pipeline. Key every node by its Roslyn
documentation comment id (`ISymbol.GetDocumentationCommentId()`, e.g.
`M:Ns.Type.Method(System.Guid)`) so node identity is deterministic, stable across
body-only edits, and aligned with the SARIF / locator id family used by the
existing error-policy tooling. See
[C# error-policy detection determinism tiers](131_csharp_error_policy_locator_tiers.md#xid-D1F4A7C3E209)
and [Roslyn analyzer quality-check applicability](150_roslyn_analyzer_quality_check_applicability.md#xid-A1B243BF7D5D).

### 8. Custom attributes are a deterministic static footprint — extract them

Custom-attribute applications are statically and exactly available from Roslyn
(`ISymbol.GetAttributes()`, with constructor and named argument values constant
folded by the compiler — `nameof(...)`, `const` references, and enums resolve to
their values). They are therefore **decomposition-free relation facts** in the
sense of principle 1 and must not be relegated to the LLM "principle" / spec-out
channel just because the channel they configure (DI, routing, serialization,
mapping) behaves dynamically at runtime.

Because attributes are not relation edges between two source nodes but a labelled
fact *about* one node (often with values), they are emitted as a **separate
deterministic inventory** rather than as graph edges — a sibling output to the
relation graph, consumed on demand:

- `target` — DocID of the annotated type / method / property / field (parameter
  and return-value attributes carry no DocID and are keyed by the containing
  method, with the parameter named in the display).
- `attribute` — DocID of the attribute type; `attributeName` — its short name.
- `ctorArgs` / `namedArgs` — constant-folded argument values.
- `file` / `line` — application site.

The inventory's value to the Where step is as a **static seed source**: "every
type carrying `[Topic]`", "every parameter with `[FromKeyedServices("x")]`",
"every `[Obsolete]` member in the cut" are deterministic queries a human performs
poorly and the inventory answers exactly. Framework-injected assembly attributes
(generated `obj/` `AssemblyInfo`) are kept in the inventory for completeness but
filtered by default at the reporting layer.

Tooling: `tools/structure_graph --attributes <attrs.json>` (same Roslyn
front-end, per principle 7) emits the inventory; `tools/attribute_inventory_report.py`
lists and filters it on demand.

## Connection to dotnet_change_analysis

> **Superseded by measurement (2026-06-21).** A controlled A/B
> ([ADR 0001](../../docs/adr/0001-where-step-grep-first.md),
> summary in [121](121_structure_analysis_determinism_tiers.md#xid-5301B897BA41))
> found that backing the Where impacted-boundary list with graph traversal gives no
> token or accuracy gain over an LLM using `grep` for **text-greppable** impact, at
> small and large scale. The Where step is therefore **grep-first by default**; the
> graph traversal is kept only for transitive impact with no textual footprint and
> for the grep-weak semantic inventories (attribute values, DI lifetimes, etc.). The
> paragraph below describes the original (now non-default) entry point.

The originally proposed entry point was to back the **Where** output of
[dotnet_change_analysis](../../skills/dotnet_change_analysis/SKILL.md#xid-D94E3B3A7C11)
— its impacted boundary list — with graph traversal candidate generation instead
of LLM-inferred structure. The LLM is not the primary candidate generator; it
explains candidates, records exclusion reasons, proposes additional traversal
seeds (including dynamic edges per principle 6), and connects the curated cut to
the change design.

### Output into the Where section

- impacted boundary list
- traversal root / seed (with the USDM-to-seed rationale, per principle 4)
- traversal direction and depth
- included nodes
- excluded nodes and reason
- high fan-in / fan-out / `transit` nodes (per principle 5)
- overlapping impact with other seeds
- uncertain / non-graph impacts handed to spec-out (per principle 6)
- human-review-required points

## The Four TM Checks

### 1. Sufficiency check

Confirm the identified change set is sufficient.

- Are reachable related nodes from the seed present in the TM?
- Was traversal cut off anywhere unfinished?
- Was only one side of an interface / base class / caller / callee picked up?

### 2. Missing-impact check

Confirm no other impacted location exists.

- reverse traversal toward callers
- forward traversal toward callees
- shared type / shared DTO / shared config / shared db object discovery
- public API / external boundary discovery

### 3. Overlap check

Confirm no other change seed touches the same place.

- do multiple seeds reach the same node?
- do they converge on the same file / type / method / config key / db object?
- are there concurrent-change collision candidates?

### 4. Coupling check

Confirm the change targets are not over-coupled.

- high fan-in nodes
- high fan-out nodes
- high-centrality nodes
- nodes referenced from many projects
- shared nodes whose change ripples widely

## Validation: Back-Test Against History

To be trusted as a backstop the graph must demonstrate it does not miss. Validate
empirically against git history: take a real past change (PR), derive the seed
from its intent, and check whether the traversal candidate set covers the files
actually changed in that PR. This yields recall (coverage) and precision
(over-reach) measures, is buildable directly from repository history, and fits
the repository's existing eval discipline. A low recall indicates a missing
edge kind or a seed-derivation gap; a low precision indicates over-reach that
principle 5 must damp.

## Limits

The graph captures only mechanically extractable relations. The following are not
sufficiently handled by the structure graph alone and remain spec-out territory:

- shared state
- runtime configuration switching
- build parameters
- environment variables
- timing dependency
- implicit protocol
- reflection
- DI container dynamic resolution
- convention-based routing
- external-system-side specification
- operational-procedure dependency
- prior judgments and exception rules

Note the boundary on `uses-config` / `uses-db` edges: static literal config keys
and EF `DbSet` references are extractable; dynamically built keys and dynamic SQL
are not, and belong to spec-out.

Therefore the structure graph **assists** spec-out; it does not make spec-out
unnecessary. See [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).

## Adoption Decision

The value adopted here is **not** any specific `@graph-*` annotation notation or
a Product Graph implementation. In-source semantic annotation is rejected for
this repository: structural relations are mechanically derivable (so marking them
is redundant), code-to-knowledge links are already covered by rule maps, skill
`knowledge_refs`, and on-demand LLM judgment, and brownfield code cannot carry
new annotations at all.

The value adopted is using a deterministic structure graph as the **TM coverage
backstop for the XDDP Where step**. Because it aligns with the existing XDDP
knowledge, the `dotnet_change_analysis` impacted boundary list, and the
`requirements_flow → design_flow` chain, the net-new scope is limited to:

- Roslyn structure-graph generation (reusing the existing front-end, DocID-keyed)
- a deterministic custom-attribute inventory as a static seed source (principle 8)
- explicit USDM-to-seed derivation
- seed traversal with over-reach damping
- the four TM checks
- impacted-boundary-candidate output
- reviewable-artifact framing for human / LLM curation
- back-test validation against history

## Conclusion

The structure graph does not replace XDDP. It is a mechanical backstop that
strengthens the coverage of impact identification across the XDDP Where step,
from spec-out to TM construction. The graph holds permanent relation facts and
the TM is generated per change requirement. This separation lets brownfield work
compute a per-requirement cut safely even though future change requirements
cannot be anticipated in advance.
