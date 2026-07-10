<!-- xid: 19BC00401A1A -->
<a id="xid-19BC00401A1A"></a>

# Early XRefKit Migration Design

This page is a design document for migrating an **early-state XRefKit** into the
current AI Agent OS model, with the migration carried out by the AI.
It is not a usage guide; for the human-facing migration guide see
[Legacy Flow Skill migration guide](../guides/062_legacy_flow_skill_migration_guide.md#xid-E3B7D5A18C62).

Related:

- [Overview](../000_overview.md#xid-7C6C2B46A9D1)
- [Business Pack model](../core/models/071_business_pack_model.md#xid-40511A8A06CD)
- [Context direction security guard](../core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11)
- [Uncertainty protocol](../core/contracts/016_uncertainty_protocol.md#xid-8A666C1FD121)
- [Judgment log usage](../guides/055_judgment_log_usage.md#xid-9D64B2F18E44)
- Skill: `legacy_flow_skill_migration` (`skills/os/legacy_flow_skill_migration/`)

## Problem Context

The target environment runs an **early XRefKit**:

- **XIDs exist** — references are already durable; this is the one piece of
  continuity to anchor on.
- **No packs** — there is no business-layer boundary. Work exists as flows, not
  as Business Packs.
- **Flows are self-styled (独自 flow)** — hand-made for that environment, not the
  current Flow / Capability / Skill model.

Three consequences follow:

- Self-styled flows are simultaneously a **defect (自己流)** and a **record of
  real operational knowledge**. Separating the two is the central judgment.
- Early flows almost certainly **mix runtime control with business steps**,
  because the OS-core / business-pack boundary did not yet exist.
- Flow interdependencies are **implicit**, because there is no pack manifest.

## Core Design Principle

**Never combine "migrate" and "improve" in one move.** Migration preserves
behavior; re-basing a flow onto an established standard is a separate, explicitly
approved step. The dominant failure mode of AI-driven migration is the AI
normalizing a flow toward a standard and silently discarding business-specific
behavior it judges as noise but which is load-bearing operational knowledge.

Two rules enforce this:

- **Propose-per-case, human-approved, never bulk auto-apply.** The AI proposes;
  a human approves each preserve / re-base / discard decision.
- **Reuse the established migration pattern, do not invent one.** Use a
  strangler-style incremental migration (old and new coexist, retire piecewise),
  not a big-bang rewrite. This applies the repository's reuse-before-build
  principle to the migration method itself.

## The Three-Way Classification

For each flow fragment, the AI produces a decision-ready ledger classifying it
into one of three kinds; a human approves the classification.

| Class | What it is | Migration outcome | Human decision |
|------|------|------|------|
| (a) Covered by an established standard | maps to a known standard (e.g. ITIL, OWASP) | re-base onto the standard; keep only the **business-specific delta** as Knowledge | approve "standard covers this" |
| (b) Operational knowledge with no standard | practice-established, business-specific procedure | **preserve**; promote into a Skill / Knowledge asset | approve "do not discard" |
| (c) Control entangled in the flow | runtime control mixed into business steps | **strip out**; now provided by the OS core | confirm guard finding |

The (a)/(b) split is where "Quality is decided by the human" applies. When the
human lacks the resolution to decide, the fragment stays as an `unknown` /
concern — it is **not** auto-decided. Conservative default: if an (a) match
cannot account for the business-specific delta, fall back to (b) and preserve.

## Migration Pipeline

| Phase | Actor | Action |
|------|------|------|
| 0. Inventory & anchor | AI (deterministic) | enumerate flows, XIDs, and references; make implicit dependencies explicit via structure analysis and `xref`. No changes to the live system. |
| 1. Classify | AI (proposes) | classify each fragment into (a)/(b)/(c); for (a), name the candidate standard; attach evidence and a concern for anything uncertain. |
| 2. Quality gate | Human (decides) | approve the preserve / re-base / discard calls; unresolved resolution stays as `unknown`. |
| 3. Re-home (trial) | AI | generate trial pack scaffolds via `legacy_flow_skill_migration`; preserve XIDs so old references still resolve; run the context-direction guard on every imported fragment; keep scaffolds in `work/` — the live system is unchanged. |
| 4. Verify & incremental cutover | AI verify + human closure | run `xrefkit skill verify`, quality gate, and `xrefkit xref check`; keep old and new coexisting by XID until the new pack passes its gate, then retire the old flow; promote trial → canonical via `retro` / `doc_ship`. |

## Role Split (QCD)

- **AI delivers Cost and Delivery**: inventory, classification, standard
  matching, scaffolding, verification — the breadth work.
- **The human decides Quality**: the preserve / re-base / discard judgment, and
  any point where target resolution is insufficient to define quality.
- The OS **carries and enforces** these decisions but does not make the Quality
  call itself.

## Risks And Mitigations

- **Misclassifying (b) as (a)** (folding operational knowledge into a standard):
  require an explicit business-delta justification for every (a); unexplained
  delta forces (b).
- **Silent normalization during re-home**: Phase 3 must emit a behavior diff
  against the old flow so the human reviews whether each difference is intended.
- **Old control leaking upward**: the context-direction guard runs on every
  imported fragment to catch early-flow control assumptions trying to drive the
  new OS control plane.
- **Reference breakage**: never mutate the live system in place; migrate by XID
  coexistence and incremental cutover.

## Non-Goals

- Not a big-bang rewrite of the early environment.
- Not an automatic, unattended migration; the human Quality gate is required.
- Not a re-litigation of quality criteria the early environment already settled,
  except where a fragment is explicitly re-based onto a standard.
