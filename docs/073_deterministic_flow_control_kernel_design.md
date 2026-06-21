<!-- xid: 4C7E9A2B1D63 -->
<a id="xid-4C7E9A2B1D63"></a>

# Deterministic Flow Control Kernel Design

This page is a **design document** for making the *control* part of a flow
deterministic — that is, moving transition selection, context assembly,
termination, and human hand-back out of model judgment and into a deterministic
engine, while leaving only the business work at each node probabilistic.

It is not a usage guide. For the flow/skill model itself see
[Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8).
For the per-page flow schema see
[Workflow page schema](018_workflow_page_schema.md#xid-6D2E4A9C0B71).

Related:

- [Base control and xref routing layers](017_base_and_xref_layering.md#xid-5A1C8E4D2F90)
- [Uncertainty protocol](016_uncertainty_protocol.md#xid-8A666C1FD121)
- [Early XRefKit migration design](072_early_xrefkit_migration_design.md#xid-19BC00401A1A) — early flows mix runtime control with business steps
- [Manufacturing workflow](033_manufacturing_workflow.md#xid-8B31F02A4002) — worked example below
- [CAB workflow](039_cab_workflow.md#xid-8B31F02A4008) — approval-gate-heavy flow
- [Metrics definition](../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201) — token-cost metric this design serves

## Origin

This design was triggered by a comparison with **takt**
(`github.com/nrslib/takt`), an external CLI that drives AI agents through a
declarative YAML state machine. takt's core idea — *control belongs to the
workflow, not to agent memory* — is the same thesis as XRefKit's
"control is the source of efficiency." takt is **not** adopted wholesale; only
the **form** (machine-readable transitions) is taken, and the placement is fixed
to the flow layer to preserve the OS-core / business boundary
(see [Base control and xref routing layers](017_base_and_xref_layering.md#xid-5A1C8E4D2F90)).

What is explicitly **not** imported from takt:

- **Worktree-by-default isolation** — execution isolation is the harness's
  responsibility, not the flow model's. Mixing it in muddies the layer.
- **Repertoire (community package distribution)** — premature for XRefKit.

## Problem Context

Today a flow expresses its transitions in **two split places**, neither of which
is machine-readable:

- `sequence:` — a **straight line**. It cannot express a branch or a loop.
- `control_rules:` — the branches and loops are **written as natural-language
  rules** and left for a human or model to interpret at runtime.

Concretely, in the manufacturing flow the feedback loop
("quality feedback without trade-off is fixed by implementation") and the
escalation ("trade-off or scope conflict is escalated to coordinator") live as
prose in `control_rules`, while `sequence` pretends the process is linear. The
"what happens next" information is therefore **duplicated and un-verifiable**.

## Core Principle

**Two layers, with non-determinism confined to one named place.**

- **Layer 1 — flow** arranges the *導線* (routing) among pieces of work: which
  step follows which, and where control terminates or returns to a human. This
  layer is **fully deterministic**.
- **Layer 2 — 業務 (the work)** is a **bundle of 作業 (work units)**. Each 作業
  resolves through exactly one of three execution modes (below).

> Determinism is not all-or-nothing. Every part of control — the graph,
> transitions, facet assembly, termination, resume — is deterministic. The only
> non-deterministic element is the **consolidation of context**, and it lives in
> exactly one place: a **capability**. Nothing outside a declared capability may
> be non-deterministic.

## A 作業's Three Execution Modes

A 作業 resolves through one of three modes. A transition label is produced in all
three, but only one mode carries judgment:

| Mode | Deterministic? | Capability? | How the label is produced |
|---|---|---|---|
| ① escalate to a human | yes (routing) | no | human's answer → `resume:` lookup |
| ② capability — consolidate context | **the sole non-deterministic locus** | **yes — the capability *is* the consolidation** | decision responsibility → label into the exit enum; generation responsibility → artifact, then label from ③ verification |
| ③ execute with Tools | yes (execution) | no | derived from the result vector (closure state) — see below |

Resolution order inside a 作業 — maximize ② and ③ coverage and keep ① as the
explicit "not covered" exit:

1. a capability must consolidate context — a decision or a generation → ② apply
2. it is pure deterministic doing → ③ Tools / Skill
3. neither, or unknown / trade-off / out-of-scope → ① escalate

① is not failure; it is the defined path when ② and ③ do not cover the case. It
is the runtime face of the
[Uncertainty protocol](016_uncertainty_protocol.md#xid-8A666C1FD121) and of
`concern` (unknown / risk).

## Capability Is Context Consolidation, Not Execution

A capability is one thing: the non-deterministic act of **consolidating
context**. It is **not** a unit of execution, and it has **no sub-types**. Whether
a 作業 makes a *decision* or *generates* an artifact, the capability is the same —
only the **responsibility** differs:

- **decision responsibility** — consolidation yields a label (into the exit enum)
- **generation responsibility** — consolidation yields an artifact; the
  transition label then comes from deterministic verification, never from the
  artifact itself

So generation is not a fourth mode and not a second kind of capability. A
generation 作業 decomposes into: the capability (consolidate context — the only
non-deterministic part) + the Tools it uses (deterministic) + verification
(deterministic). For code this is: write until it compiles (the consolidation) →
the compiler (deterministic) → label from the compile/test result. The
non-determinism is the consolidation alone; the tools the capability uses and the
verification that follows are all ③.

This yields an auditable invariant:

> Any non-determinism that is **not** a declared capability (context
> consolidation) is a defect.

`flow doctor` / the engine can enforce it:

- routing (①), terminals, `resume`, and facet assembly must be deterministic —
  no capability there;
- Tool execution and verification (③) must be deterministic — no capability, even
  when invoked **inside** a consolidation step;
- a context-consolidation point is the only place a capability is declared;
- a declared capability must resolve to a real catalog id under `capabilities/`;
  fabricated ids are not placeholders, because they create an unaudited
  non-deterministic surface;
- a generation 作業's transition label must come from deterministic verification
  (③), not from the generated artifact;
- a hidden branch or an undeclared consolidation is flagged.

The residual non-deterministic surface of the whole system therefore equals the
**amount of context consolidation** — i.e. capability invocations. Raising
certainty reduces to one engineering move: shrink what each capability must
consolidate and push everything around it (tools, verification) into
deterministic ③. This also sharpens **Capability Routing**
([Capability routing](../agent/010_capability_routing.md#xid-1F93A7C24010)): it
routes to a *consolidation responsibility*, resolved before execution; once
resolved, the surrounding tools and verification run deterministically.

## Every 作業 Is Execution Plus Acceptance

Every 作業 has two parts: an **execution** and an **acceptance criterion**. The
acceptance criterion is defined when the work list is created — at **planning** —
and defining it is itself a context consolidation: deciding what "done / good"
means for this 作業 is a **capability**, hence non-deterministic.

This front-loads the non-determinism. There are exactly **two planning-time
consolidations** per 作業, both capabilities:

1. form the work list (which 作業 exist)
2. define each 作業's acceptance criterion

Once the criteria are predefined, checking an output against them falls to
**deterministic ③**: the check re-derives a fixed predicate, it does not decide
afresh. A check becomes a *further* capability only when a criterion cannot be
made tool-checkable and acceptance requires judgment; the certainty move is to
define criteria so the check collapses to ③.

This is already the mechanism in
[Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61): work
items carry the execution, `check`-kind artifacts carry the acceptance criteria
declared at planning, `fm skill verify` re-derives the predefined conditions
deterministically, and only judgment-bearing acceptance is routed to an
independent quality reviewer. The same shape holds across the flow chain:
`planning_workflow` defines the policies (criteria) non-deterministically, and
the downstream flows execute and verify against them
(`design_realizes_planning_policies`, requirement-traceability checks, and so on).

The determinism thesis closes on this: concentrate non-determinism in the two
planning consolidations, and every per-作業 execution and check downstream can be
deterministic.

## The Acceptance Gate

The acceptance criterion is not passive: it is **evaluated at a gate**, and the
gate decides the transition. This completes the structure — **every 作業 is
execution → acceptance gate → transition** — and yields a universal invariant:

> The transition label is **always** produced by the 作業's acceptance gate,
> never by bare execution. Every 作業 has a gate.

### Three Gate Kinds

A gate is named by its evaluator:

| Gate | Evaluator | Deterministic? | Schema form |
|---|---|---|---|
| **tool gate** | a deterministic tool (compiler, analyzer, test, coverage) | yes — ③ | `result_map` / `acceptance: [{tool: …}]` |
| **review gate** | an independent reviewer | no — ② capability | `acceptance: [{review: …}]` |
| **human gate** | a human (a human-owned commitment) | no — ① | `gate:` / `handback:` human edge |

"Every 作業 has a gate" does **not** mean every 作業 stops for a human. The gate
kind follows the criterion: tool-checkable → tool gate; judgment → review gate;
a human-owned commitment → human gate. Non-determinism stays localized — only the
review gate is a capability.

### Canonical Verdicts (Go / Kill / Hold / Recycle)

A gate emits one canonical verdict. The vocabulary is borrowed from the
Stage-Gate process so we do not reinvent it:

| Verdict | Meaning | Transition target |
|---|---|---|
| **Go** | accepted — proceed | the next 作業 (or `COMPLETE` if terminal) |
| **Kill** | rejected, unrecoverable | `ABORT` |
| **Hold** | cannot decide now — pause for a human | a human edge (`handback` / `gate`) |
| **Recycle** | not yet acceptable — rework | loop back to a prior 作業 |

`_invalid_or_absent` is **not** a verdict; it is the meta-fallback for *no valid
verdict* (malformed/absent output), routed to Kill or Hold.

A tool gate (③) derives the verdict from closure outcomes (`complete`→Go,
`needs_fix`→Recycle, `escalate`/`uncertain`→Hold, `blocked`→Hold/Kill). A review
gate (②) or a human gate (①) emits the verdict directly. Content-decision
branches that are *not* acceptance verdicts (e.g. "feedback needed vs not") keep
their own labels — the canonical verdicts are for the acceptance gate.

### Terminology

The YAML keyword `gate:` is the **human** realization specifically; **acceptance
gate** is the umbrella concept whose three kinds are above. A `result_map` is a
tool gate; an `acceptance: [{review: …}]` is a review gate.

### The Gate Is Role-Separated From Execution

The gate is owned by a role **distinct from the executor**
([Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61):
`executor` ≠ `quality_reviewer`). Execution (executor role) produces the
artifact; the gate (reviewer role, tool, or human) produces the
accepted/rejected label. So "every 作業 has a gate" is also a control
requirement — it universalizes producer/checker separation and forbids
self-certification.

### Evaluation Work: the Axis Is the Gate

The role-separation rule above is about **generation**. Evaluation is different.

For an **evaluation 作業** (CAB's suitability / readiness / value-fit reviews,
scope determination), the work *is* judging against an axis. The **evaluation
axis is the gate**: the verdict against the axis is the transition label, and
execution and gate coincide. There is no separate meta-acceptance and no
self-certification problem — the verdict *is* the product, nothing else is being
approved. Such a step is a ② capability whose `on` branches are the verdicts
(e.g. `meets` / `not_met` / `conditional`).

For a **generation 作業** (analysis, drafting, design), execution produces an
artifact and the gate is a *separate* acceptance (review or tool) of that
artifact, owned by a role distinct from the executor.

So: evaluation → the evaluator produces the verdict (axis = gate); generation →
a separate gate, by a different role, accepts the artifact. This is the same
decision / generation responsibility split applied to the gate.

### `_invalid_or_absent` Is the Minimal Gate

Every 作業's always-present fail edge `_invalid_or_absent` is the **minimal
gate** — the reject path that must exist even for a trivial gate. `flow doctor`
already enforces it (D2), so the minimum form of "every 作業 has a gate" is
machine-checked today; the full form additionally wires the accept/reject
outcomes through the gate.

### Why Not Preconditions (Entry Gates)

Design by Contract pairs every routine's postcondition with a precondition (an
entry gate). A symmetric per-作業 precondition was **considered and rejected**: in
a flow it would only re-state the upstream 作業's exit gate. By DbC's own
composition rule a supplier's postcondition discharges the client's precondition,
and a flow graph has *known* predecessors, so the entry condition is determined by
the upstream exit gates. (DbC needs the precondition because a routine has open,
unknown callers; a closed flow graph does not.) A separate entry gate would only
duplicate the upstream exit gate and become a sync liability.

The two residuals are handled without a precondition construct:

- a flow's **entry 作業** takes its entry condition from the *upstream flow's* exit
  gate (the inter-flow handoff via `runs_after` / `handoff`), not a per-作業
  precondition;
- a **fan-in 作業** (multiple inputs) checks cross-input consistency inside its own
  gate (inconsistent → Recycle / Hold), since the state machine is single-path
  with no join node.

The consequence is a requirement on exit gates, not a new construct: an exit
gate's acceptance criteria must fully guarantee what every downstream 作業
requires. Preconditions are unnecessary precisely because the exit gate carries
that responsibility.

## The Node ↔ Engine Contract

A 作業 reports a **result**; it does not freely choose its successor. The engine
derives the transition from that result, per mode:

- **① human edge** — the human's answer maps through `resume:` (deterministic).
- **③ Tool/Skill execution** — the label is derived deterministically from the
  run's **result vector** (closure state, phase states, concern inventory).
  `fm skill verify` / `fm skill close` fix that state deterministically and the
  engine reads it; the node never emits the label freely. See
  [Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61).
  No new result format is introduced — the existing run-log result vector *is*
  the report.
- **② capability judgment** — the only place the label reflects a genuine
  decision, bounded to the declared exit enum.

In every mode the node carries `evidence` (the `evidence`-kind artifact plus the
run-log reference). The node never names its successor; routing, termination, and
resume belong to the engine.

## Transition Representation

Replace the split `sequence` + `control_rules` with per-step transitions:

```yaml
steps:
  implementation:
    edit: true
    on:
      complete: unit_test_execution

  return_quality_feedback_response:
    on:
      feedback_no_tradeoff: implementation          # feedback loop
      none: quality_source_recheck_or_redisposition
      # human hand-back: see below
```

Machine terminals: `COMPLETE`, `ABORT`. `control_rules` keeps only the
invariants that are *not* transitions (e.g. `stays_inside_approved_boundary`).

## Human Hand-Back Is a Third Transition Type

Returning control to a human is **not** a terminal. Unlike `COMPLETE`/`ABORT`,
the human's answer comes **back into the flow**, so the flow is still alive. It
is a *suspend + branch-on-human-answer + resume*, and its target is a **human
role**, not a step.

```yaml
  return_quality_feedback_response:
    on:
      feedback_tradeoff_or_scope_conflict:
        handback:
          to: coordinator                 # human role, not a step
          reason: tradeoff_or_scope_conflict
          ask: "adjudicate trade-off / scope conflict"
          resume:                         # routing keyed on the human's answer
            resolved_in_scope: implementation
            ruled_out_of_scope: record_out_of_scope
            rejected: ABORT

  handoff_to_quality_review:
    on:
      complete:
        gate:                             # synchronous approval gate
          to: quality_group_review
          ask: "external review approval"
          resume:
            approved: COMPLETE
            needs_fix: implementation     # rejection loops back
```

Distinctions that must be kept:

- `next: <step>` — engine advances automatically (machine edge).
- `handback.to: <role>` / `gate.to: <role>` — engine **suspends** and waits for a
  human (human edge). Always carries `resume:`.
- A human return **without** `resume:` is just `ABORT` (flow ends; disposed
  outside). That is a different thing — do not write it as `handback`.

This formalizes the existing `escalation:` block (today prose) and the
`handoff:` block into transitions.

## Condition for *True* Determinism

The control closes deterministically **only if** invalid or absent labels have a
defined edge. Without this it is "almost deterministic" — a model that emits an
out-of-enum label breaks the wiring.

```yaml
on:
  approved: COMPLETE
  needs_fix: implementation
  _invalid_or_absent: handback   # mandatory deterministic fallback
```

Every step's `on:` must guarantee that **any** model output — including
malformed output — lands on a terminal, a human edge, or an existing step. Then
control is provably closed.

## Cross-Cutting Uncertainty Hand-Back

"If you cannot answer, stop and ask" (see
[Uncertainty protocol](016_uncertainty_protocol.md#xid-8A666C1FD121)) is **not**
a per-step transition. It can fire at any node, so listing it in every `on:`
explodes the graph. It is declared once as a flow-level hand-back:

```yaml
global_handback:
  uncertainty:
    to: coordinator
    ask: "resolve blocking unknown"
    resume: <re-enter the suspending step>
```

## Layer Boundary

Transitions stay in the **flow** layer. They must **not** move into skill phases
(`fm skill phase`):

- **flow** = the business state machine — *whose* failure loops back to *where*.
- **skill phase** = execution / check / handoff *inside one work-unit*.

takt collapses persona + permission + transition into one `steps` entry. XRefKit
imports only the transition *form*; placement stays in the flow to preserve the
two-layer separation. Early flows that mix runtime control with business steps
are exactly the defect called out in
[Early XRefKit migration design](072_early_xrefkit_migration_design.md#xid-19BC00401A1A).

## Token-Cost Implication

The deterministic representation **by itself does not lower tokens** — the YAML
grows slightly with `resume:` branches. Savings appear only when the
representation enables the engine to:

1. **Drive next-step selection** without spending model context on "what's
   next" — and load **only the current step's facets**. This is the continuous
   per-turn context reduction (takt's faceted-prompting benefit).
2. **Cut rework variance** — natural-language `control_rules` invite wrong
   branches → redo → whole-conversation re-send. A machine edge removes the
   interpretation. This trims the expensive failure tail and matters most on
   light-tier executors; heavy tiers branch correctly even on prose, so the
   margin is smaller there.
3. **Make resume cheap** — `resume: <step>` re-enters at the named step instead
   of rebuilding context after a human answer.

The headline property is not "cheaper" but **predictable**: transition count and
per-turn context are decided deterministically by the engine, so cost variance is
localized to capability (judgment) invocations — the system's only
non-deterministic surface. See
[Metrics definition](../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201).

## flow doctor Check Items

`flow doctor` is the static, declaration-time enforcer: every contract clause
needs a deterministic enforcer, and this is the one that runs before any flow
executes. All checks are pure functions of the flow definition — no run, no
model.

**Graph closure**

- C1 — every `on:` label target resolves to an existing step, a terminal
  (`COMPLETE` / `ABORT`), or a human edge
- C2 — no unreachable step (every step reachable from the entry)
- C3 — every cycle has at least one exit to a terminal or a human edge (no
  inescapable loop)
- C4 — the entry step exists

**Determinism closure**

- D1 — every step declares its exit enum (the closed label set)
- D2 — every step's `on:` includes `_invalid_or_absent` (or inherits the engine
  default), so any output — including malformed output — lands on a defined edge

**Human-edge contract**

- H1 — every `handback` / `gate` carries `to:` (a human role), `ask:`, and
  `resume:`
- H2 — every `resume:` answer-key target resolves to an existing step or terminal
- H3 — a human return without `resume:` is written as `ABORT`, never as
  `handback` / `gate`
- H4 — `global_handback` (uncertainty) is declared once at flow level with a
  valid resume target

**Capability localization** (the core invariant of this design)

- K1 — a capability is declared only at a context-consolidation point (②)
- K2 — routing (①), terminals, `resume`, and facet assembly carry no capability
- K3 — Tool execution and verification (③) carry no capability and must be
  deterministic, **including tools/verification invoked inside a consolidation
  step**
- K4 — a branch whose label is produced neither by ① nor by ③ nor by a declared
  capability is flagged as a hidden (undeclared) consolidation
- K5 — a declared capability sitting on a deterministic step (not a consolidation
  point) is flagged as misplaced
- K6 — a generation 作業's transition label is produced by deterministic
  verification (③), not by the generated artifact
- G3 — every `capability:` value resolves to a declared capability id in
  `capabilities/`; unresolved or fabricated ids are hard failures, not warnings

**Per-step declaration**

- P1 — each step declares its facet manifest, so assembly is a pure function
- P2 — each step declares its permission envelope (edit / tools / paths)
- P3 — each ③ step declares the mapping from its exit enum to closure outcomes
  (complete / needs_fix / escalate / uncertain / blocked), so the engine derives
  the label from the result vector without the model

**Acceptance gate**

- G1 — a declared tool gate (`acceptance: [{tool: …}]`) produces its verdict via
  `result_map`; a tool gate with no `result_map` is unwired (warning)
- G2 — a canonical verdict label routes to a consistent target: `Go` → step or
  `COMPLETE`, `Kill` → `ABORT`, `Hold` → a human edge, `Recycle` → a step

A flow that passes all of the above has a **provably closed, capability-audited
control graph**: every reachable path ends at a terminal or a human edge, every
output lands on a defined edge, and every non-deterministic point is a declared
capability.

## Open Questions / Next Steps

- **Engine prototype** — a minimal `fm` driver that reads `on:` / `handback` /
  `gate` / `global_handback`, loads per-step facets, and enforces the
  `_invalid_or_absent` fallback.
- **`flow doctor`** — implement the static checks enumerated in
  **flow doctor Check Items** above (graph closure, determinism closure,
  human-edge contract, capability localization, per-step declaration).
- **Schema update** — fold the above into
  [Workflow page schema](018_workflow_page_schema.md#xid-6D2E4A9C0B71) once one
  flow is migrated end-to-end as a reference.
- **Pilot flow** — migrate one flow first to confirm the control graph provably
  closes (every edge lands on terminal / human / existing step). A light-tier
  flow (investigation or requirements) best demonstrates the token effect; CAB
  best exercises the `gate` type.
