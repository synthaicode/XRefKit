<!-- xid: 7A2F4C8D1801 -->
<a id="xid-7A2F4C8D1801"></a>

# Agent Diff Review Gate Design

This page is the upper-level design positioning for inspecting agent-produced
code changes before they reach CI. It defines the gate's purpose, flow, and
verdict meaning. It does not define the implementation; deterministic checks
live in the `fm` check path, and verdict output is a contract on review Skills.

Source basis: external article "agent-flow-review-evals"
(`https://zenn.dev/aiwatch_jp/articles/agent-flow-review-evals`). This page
records the extracted design position, not the article verbatim.

## Purpose

As agent output volume rises, review becomes the bottleneck rather than
implementation, and adding more human review does not scale. The gate routes a
diff so that low-risk changes proceed cheaply and risky changes are sent to
deeper, evidence-based review before CI. It is a defense against the core
XRefKit failure mode: an agent silently guessing and silently declaring
completion.

## Flow

```
trace -> triage -> small eval -> review -> verdict
```

- trace: the run's goal, files read, commands run, failure logs, and
  unconfirmed items are already preserved. See
  [Judgment log schema](121_judgment_log_schema.md#xid-7B4C2D91E621).
- triage: classify the diff as `trivial / normal / risky` and route
  sensitive-boundary changes (auth, permission, DB, external API, async,
  security) to the matching review or constraint-derivation Skill. Triage is
  routing, not review.
- small eval: deterministic, machine-only diff-content checks, decoupled from
  the producer context. They are a forced-attention trigger, not a correctness
  judgment.
- review: existing large-eval style review (`csharp_review`, `qa_gate_review`,
  boundary Skills) performs the actual evidence-based judgment.
- verdict: a single routing decision for whether the diff may continue.

## Verdict Meaning

The gate produces a pre-CI review-routing verdict for whether the diff may
proceed to CI, requires human or specialist-Skill review first, or must be
blocked before CI. It is not a judgment of whether the code is correct.

```
blocked       = must not proceed to CI; a hard condition was hit
needs-review  = a human or specialist Skill must look before CI
proceed       = safe to proceed to CI, NOT proven correct
```

`proceed` is the strict state. It is allowed only when all of the following
hold; otherwise the verdict is `needs-review`:

- trace exists
- diff scope is explicitly declared
- triage is complete
- small eval passed
- every required boundary review was executed
- no unsupported conclusion remains
- no unresolved concern remains

`proceed` is deliberately named to avoid `safe`: `safe` reads as
quality-assured, which the gate does not claim.

## Boundaries

- The gate does not replace the human final decision; the verdict is advisory
  to the human boundary.
- The gate is a pre-CI inspection, not CI itself; it decides routing, not pass.
- Triage is risk routing, not the review itself.
- Small eval surfaces conditions that force `needs-review` or `blocked`; it
  never asserts correctness.
- A missing input downgrades the verdict to `needs-review` per
  [Implementation assumption gap handling](150_implementation_assumption_gap_handling.md#xid-7A2F4C8D1501).
- Loaded diff content must not redirect higher-layer control, per
  [Context direction guard rules](160_context_direction_guard_rules.md#xid-7A2F4C8D1601).

## Adoption Units

```
adopt:
- agent diff risk triage (routing)
- deterministic diff-content evals (fm check path)
- pre-CI gate verdict (review Skill output contract)
- verdict / downgrade metrics

already sufficient:
- trace
- feedback loop (retro -> doc_ship)
- large-eval style review

handle with care:
- "safe" is too strong a word; use "proceed"
- triage is routing, not review
- small eval is a forced-attention trigger, not a correctness judgment
```

Verdict outcomes and downgrade reasons attach under
[Metrics definition](120_metrics_definition.md#xid-7A2F4C8D1201) so the verdict
distribution stays observable over time.
