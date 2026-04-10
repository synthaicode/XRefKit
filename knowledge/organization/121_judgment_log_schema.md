<!-- xid: 7B4C2D91E621 -->
<a id="xid-7B4C2D91E621"></a>

# Judgment Log Schema

This page defines the canonical structure for AI-authored judgment logs stored in `work/judgments/`.

## Purpose

- make non-trivial judgments inspectable
- separate evidence from inference
- support later review, retry, and skill improvement

## Storage Rule

- Store judgment logs in `work/judgments/`.
- Use date-prefixed filenames:
  - `YYYY-MM-DD_judgment_<topic>.md`
- Keep session facts in `work/sessions/` and judgment records in `work/judgments/`.

## When To Write

Write a judgment log when any of the following occurs:

- a non-trivial scope, impact, or architecture judgment is made
- confidence is `3` or below
- multiple candidate interpretations are compared
- a stop-or-continue control decision is made
- a later review or retry is likely to need the reasoning path

## Required Fields

| Field | Meaning |
|------|------|
| `work` | work type or task name |
| `target` | file, module, feature, or decision target |
| `decision` | selected judgment or conclusion |
| `decision_status` | `proposed`, `accepted`, `rejected`, `unknown`, or `deferred` |
| `judgment_evidence` | concrete evidence used |
| `evidence_type` | `deterministic`, `context_extracted`, `inferred`, or mixed |
| `confidence` | `5` to `1` using the metrics scale |
| `context_usage` | `small`, `medium`, or `large` |
| `alternatives` | rejected or deferred alternatives |
| `open_questions` | missing evidence or unresolved questions |
| `next_check` | recommended next verification step |

## Evidence Type Rule

| Value | Meaning |
|------|------|
| `deterministic` | directly verified from code, config, tool output, or exact source text |
| `context_extracted` | summarized from broader local context with stable traceability |
| `inferred` | estimated from partial evidence or pattern recognition |

## Required Handling

- If `evidence_type` is only `inferred`, treat the result as `unknown` unless explicitly accepted as provisional.
- If `confidence` is `2` or below, do not present the result as normal completion.
- Preserve exact evidence paths when available.
- Separate observed facts from inferred conclusions.

## Format

```text
work: dotnet_change_analysis
target: Order approval flow
decision: approval branching is controlled by Application service and custom attribute gate
decision_status: proposed
judgment_evidence: src/App.Application/Orders/ApprovalService.cs; src/App.Framework/ApprovalGateAttribute.cs
evidence_type: deterministic + context_extracted
confidence: 4
context_usage: medium
alternatives:
  - controller-side branching
  - external-config-side branching
open_questions:
  - whether legacy batch reuses the same gate
next_check:
  - inspect batch entry path and related tests
notes:
  - attribute consumption path confirmed; batch reuse still unverified
```
