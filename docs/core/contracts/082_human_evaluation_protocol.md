<!-- xid: 7C4E2A91D8F0 -->
<a id="xid-7C4E2A91D8F0"></a>

# Human Evaluation At Run Boundaries

This contract extends the workflow protocol with an optional record that a
human may provide together with a subsequent request. It connects a completed
run to the next action without turning handoff into an approval wait.

## Boundary Rule

- A run always returns control to the human at handoff.
- The next request may omit evaluation and start ordinary low-risk continuation
  without blocking.
- When provided, evaluation is recorded against the preceding run only after
  its `Closure Gate` is `done` or `escalated`.
- The human-confirmed `classification` is authoritative. An AI may present a
  `proposed-classification`, but the proposal is not a decision or authority.
- This record contains externally stated evaluation facts and evidence links;
  it does not store or reproduce private model chain-of-thought.

## Run-Level Fields

`xrefkit skill evaluate` records `decision` (`accepted`,
`accepted_with_conditions`, `correction`, `rejected_or_returned_to_human`, or
`needs_clarification`), the human-confirmed `classification` (`continuation`,
`correction`, `scope_change`, `new_work`, or `needs_clarification`), and
`next_handling` (`continue_next_step`, `repair_previous_run`, or
`human_takeover`). It also records purpose fit, verified artifact/check basis,
remaining uncertainty/risk, carry-forward context, linked targets, and an
`evaluated_at` timestamp.

## Scoped Findings

One run may cover multiple work items, systems, or evidence sets. Add optional
findings with `TARGET|DECISION|NOTE` and scoped evidence links:

```powershell
xrefkit skill evaluate --log <run-log> `
  --decision accepted_with_conditions `
  --classification correction `
  --next-handling repair_previous_run `
  --purpose-fit "The overall purpose remains valid" `
  --verified "WI-001 and its check passed" `
  --uncertainty "WI-002 behavior remains unresolved" `
  --scope-finding "WI-001|accepted|Target system A is acceptable" `
  --scope-finding "WI-002|correction|Target system B needs the missing constraint" `
  --scope-link "WI-002|EVD-002"
```

`TARGET` may identify a work item, artifact, evidence context, or target
system. A scoped correction does not invalidate the entire preceding run.

## Time And Context Drift

The event records `preceding_run_id`, `evaluated_at`, and optional
`context_refs` for versioned/declarative evidence context. Comparability is
valid only when the decision basis, source/evidence context, criteria, and
relevant Skill/protocol/configuration are comparable. If those inputs are not
versioned or snapshotted, record `--comparability gap` with one or more
`--comparability-gap` reasons; do not infer that an A-good/B-bad difference is
object-specific. This does not promise model-internal reproducibility.

## Verification Boundary

The evaluation is an observation event, not a replacement for `skill verify`,
`skill close`, artifact quality review, or human accountability. It is not a
required closure field, so missing evaluation never blocks handoff or ordinary
continuation. The CLI validates schema, predecessor closure status, allowed
values, timestamp/context syntax, and scoped finding syntax; it does not judge
whether the human's basis is substantively correct.

## Related

- [Skill Operating Contract](058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Workflow Protocol Sequence For Humans](../../guides/087_workflow_protocol_sequence_for_humans.md#xid-E8B4D2F19A63)
- [Instruction-Backed Workflow Protocol](../../guides/088_instruction_workflow_protocol.md#xid-9F4C2A7D1B60)
