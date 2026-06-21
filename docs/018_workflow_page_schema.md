<!-- xid: 6D2E4A9C0B71 -->
<a id="xid-6D2E4A9C0B71"></a>

# Workflow Page Schema

This page defines two related schemas:

1. the **documentation shape** used by workflow pages in `docs/` (human view);
2. the **flow definition schema** for the machine-readable flow files under
   `flows/` (execution view).

The documentation page is the readable view; the flow definition is authoritative
for execution and is what `flow doctor` validates. They must not contradict each
other. The flow definition schema realizes the deterministic control model in
[Deterministic flow control kernel design](073_deterministic_flow_control_kernel_design.md#xid-4C7E9A2B1D63).

It exists to reduce interpretation drift across workflow pages.
Individual workflows should focus on their domain-specific differences and may rely on this page for the shared section pattern.

## Common Sections

Most workflow pages use the following sections:

- `Purpose`
- `Group Interaction`
- `Flow Diagram`
- `Business Activities and Supporting Capabilities`
- `Sequence`
- optional `Inputs`
- optional `Outputs`
- optional `Control Rules`
- optional `Required Knowledge`
- `Related Skills`

Not every workflow must use every optional section, but omissions should be intentional.

## Section Meanings

- `Purpose`:
  - what outcome this workflow is responsible for
- `Group Interaction`:
  - owner group, upstream inputs, downstream handoff, and escalation path
- `Flow Diagram`:
  - high-level progression and handoff structure
- `Business Activities and Supporting Capabilities`:
  - the business activities and the capability definitions that support them
- `Sequence`:
  - the readable operational order for humans and agents
- `Inputs` / `Outputs`:
  - explicit handoff artifacts where traceability matters
- `Control Rules`:
  - workflow-specific boundary or quality rules that should not be buried only in capabilities
- `Required Knowledge`:
  - knowledge pages that are especially important for executing the workflow
- `Related Skills`:
  - likely skill entry points for execution

## Flow Definition Schema (deterministic control)

The machine-readable flow file is a **deterministic state machine**. Rationale,
the three execution modes, and the capability-localization invariant are in
[Deterministic flow control kernel design](073_deterministic_flow_control_kernel_design.md#xid-4C7E9A2B1D63);
this section fixes the concrete field shape that `flow doctor` checks.

### Top-Level Fields

- `flow_id`, `name`, `doc_xid` — identity (unchanged)
- `phase`, `owner`, `runs_after`, `runs_before` — orchestration metadata
  (unchanged)
- `inputs`, `outputs`, `handoff` — handoff artifacts (unchanged)
- `entry` — the name of the first step
- `steps` — a map of step name → step definition (replaces `sequence`)
- `invariants` — flow-level guards that are **not** transitions (the part of the
  old `control_rules` that expresses a boundary, e.g. `draft_only`,
  `evaluation_not_decision`)
- `global_handback` — cross-cutting human returns that may fire from any step
  (uncertainty); declared once, not per step

Reserved transition targets: `COMPLETE`, `ABORT` (machine terminals).

### Step Fields

Each step is one 作業 and declares:

- `facets` — the facet manifest assembled for this step (deterministic assembly)
- `permission` — the capability envelope, e.g. `{ edit: false, tools: [...],
  paths: [...] }` (enforced by the harness, not by trust)
- `capability` — **optional, and the only place non-determinism is allowed.**
  Present only at a context-consolidation point (② — a decision or a generation).
  A step with no `capability` is deterministic (① routing or ③ tool/verification).
  When present, the value must be a declared capability id from `capabilities/`;
  unresolved or fabricated ids fail `flow doctor`.
- `acceptance` — the acceptance criterion for this 作業 (see *Acceptance* below)
- `result_map` — for ③ steps only: the mapping from closure outcomes
  (`complete` / `needs_fix` / `escalate` / `uncertain` / `blocked`) to exit
  labels, so the engine derives the label from the result vector without a model
- `on` — the exit map: `{ label: target }` over the step's declared exit enum.
  Every `on` must include `_invalid_or_absent` so any output, including malformed
  output, lands on a defined edge.

### Human Edges

An `on` target may be a human edge instead of a step or terminal. A human edge
**suspends and resumes**; it always carries `resume`:

```yaml
on:
  feedback_tradeoff_or_scope_conflict:
    handback:            # cannot resolve — hand to a human, resume on the answer
      to: coordinator    # a human role, never a step
      reason: tradeoff_or_scope_conflict
      ask: "adjudicate trade-off / scope conflict"
      resume:
        resolved_in_scope: implementation
        ruled_out_of_scope: record_out_of_scope
        rejected: ABORT
  complete:
    gate:                # synchronous approval gate before advancing
      to: quality_group_review
      ask: "external review approval"
      resume:
        approved: COMPLETE
        needs_fix: implementation
```

A human return **without** `resume` is `ABORT`, never `handback` / `gate`.

### Acceptance Gate

Per 073, every 作業 is *execution → acceptance gate → transition*. The criterion
is defined at planning (a context consolidation = capability) and **evaluated at a
gate** that produces the transition label. Every step has a gate; the transition
label is always produced by the gate, never by bare execution.

A gate is named by its evaluator:

- **tool gate** — `result_map` / `acceptance: [{tool: …}]`: deterministic ③
  (compiler, analyzer, test, coverage)
- **review gate** — `acceptance: [{review: …}]`: judgment-bearing acceptance
  routed to an independent reviewer (② capability)
- **human gate** — a `gate:` / `handback:` human edge: a human-owned commitment

The gate is owned by a role distinct from the executor (executor ≠
quality_reviewer — no self-certification). `_invalid_or_absent` is the minimal
gate (the always-present reject edge). The YAML keyword `gate:` is the *human*
gate specifically; "acceptance gate" is the umbrella.

**Evaluation vs generation.** For an *evaluation* step the evaluation axis *is*
the gate: the `on` branches are the verdicts produced by the evaluation
capability (e.g. `meets` / `not_met`), with no separate acceptance — the verdict
is the product, so there is no self-certification. For a *generation* step the
gate is a separate review/tool acceptance of the produced artifact, owned by a
different role.

**Canonical verdicts.** A gate emits one verdict, normalized to the Stage-Gate
vocabulary (see 073):

- **Go** — accepted → proceed to the next step (or `COMPLETE`)
- **Kill** — rejected, unrecoverable → `ABORT`
- **Hold** — pause for a human → a `handback` / `gate` human edge
- **Recycle** — rework → loop back to a prior step

`_invalid_or_absent` is the meta-fallback (no valid verdict), not a verdict.
Non-verdict content-decision branches keep their own labels.

Acceptance items map to `check`-kind artifacts in the run log; see
[Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61).
Prefer `tool:` so the gate collapses to ③.

### Minimal Example

```yaml
flow_id: FLOW-EXAMPLE
name: example_workflow
doc_xid: <XID>
entry: draft

invariants:
  - draft_only

global_handback:
  uncertainty:
    to: coordinator
    ask: "resolve blocking unknown"
    resume: draft

steps:
  draft:
    facets: [planner_persona, draft_policy, domain_knowledge]
    permission: { edit: true, paths: ["docs/**"] }
    capability: CAP-DRAFT          # ② consolidation — the only non-deterministic point
    acceptance:
      - { tool: "python tools/check_draft.py" }
    on:
      complete: verify
      _invalid_or_absent:
        handback: { to: coordinator, ask: "draft blocked", resume: { resolved: draft, rejected: ABORT } }

  verify:                          # ③ deterministic — no capability
    facets: [verify_policy]
    permission: { edit: false }
    result_map: { complete: COMPLETE, needs_fix: draft }
    on:
      complete: COMPLETE
      needs_fix: draft
      _invalid_or_absent: ABORT
```

### Migration From `sequence` / `control_rules`

- `sequence` → `entry` + `steps` with explicit `on` edges
- `control_rules`, split per item:
  - a boundary/guard → `invariants`
  - an implied transition (e.g. "needs-fix is fixed by implementation") → an `on`
    edge / human edge
  - an embedded decision → a `capability` at a ② step
- escalation prose → `handback` with `resume`
- the migration is per-flow and human-reviewed (strangler, not big-bang); see
  [Early XRefKit migration design](072_early_xrefkit_migration_design.md#xid-19BC00401A1A)

### Validation

A conforming flow passes the **flow doctor Check Items** (graph closure,
determinism closure, human-edge contract, capability localization, per-step
declaration) enumerated in
[Deterministic flow control kernel design](073_deterministic_flow_control_kernel_design.md#xid-4C7E9A2B1D63).
In particular, `capability:` is not a free-form label: it must resolve to the
real capability catalog, and unresolved references are hard validation failures.

## Authoring Rule

Do not repeat repository-wide base control or XRefKit routing rules in every workflow page unless the workflow needs a narrower local rule.

Prefer:

- shared repository rules in:
  - [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
  - [Base control and xref routing layers](017_base_and_xref_layering.md#xid-5A1C8E4D2F90)
  - [Workflow](010_workflow.md#xid-7D1E1C0279F1)
- workflow-specific rules in each workflow page

## Related

- [Workflow](010_workflow.md#xid-7D1E1C0279F1)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Deterministic flow control kernel design](073_deterministic_flow_control_kernel_design.md#xid-4C7E9A2B1D63)
- [Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61)
