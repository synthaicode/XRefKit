<!-- xid: 7A2F4C8D1201 -->
<a id="xid-7A2F4C8D1201"></a>

# Metrics Definition

This page defines the execution metrics attached to work outputs and management-table rows.

## Purpose

Metrics make judgment quality inspectable and support the next handoff or review.

## Required Metrics

| Metric | Meaning | Typical values |
|------|------|------|
| `judgment_evidence` | what the result is based on | design doc, coding rule, service catalog, stakeholder confirmation |
| `confidence` | self-evaluated confidence of the result | `5`, `4`, `3`, `2`, `1` |
| `context_usage` | rough context-window usage estimate | `small`, `medium`, `large` |
| `token_cost` | measured LLM token cost of the step | a number (subagent/run total), or `n/a` |

## Confidence Scale

| Level | Label | Meaning | Required handling |
|------|------|------|------|
| `5` | high | evidence is clear and verified | normal handoff |
| `4` | moderately_high | evidence exists with minor unverified parts | handoff with note |
| `3` | medium | evidence is partial or mixed with estimation | request follow-up review |
| `2` | moderately_low | estimation dominates and evidence is weak | treat as `unknown` |
| `1` | low | no reliable evidence | do not treat as completed output |

## Context Usage Scale

| Value | Meaning | Risk |
|------|------|------|
| `small` | little context consumed | low |
| `medium` | moderate context consumed | medium |
| `large` | most context consumed | high; refresh domain knowledge before continuing |

## Token-Cost Attribution

`token_cost` makes the LLM cost of a step inspectable, the way `confidence` makes
quality inspectable. Record the real token total when it is available, not a guess.

- When a step runs in a subagent, record the harness-reported subagent token total
  as `token_cost`. For a multi-subagent step, sum them.
- **Measure before adopting a heavier path.** Before standardizing a deterministic
  tool/pipeline over a cheaper LLM path (or vice versa), run both on the same task
  and compare `token_cost` and result quality — do not adopt on reasoning alone. A
  worked example and the resulting decision are in
  [ADR 0001](../../docs/adr/0001-where-step-grep-first.md#xid-F4B92B6AC13E): a
  deterministic pack measured tie-to-worse on tokens versus grep for greppable
  impact, so the cheaper path stayed standard.
- Use `token_cost` to validate `model_tier` choices: a step routed to a heavy tier
  whose `token_cost` and quality match a lighter tier should be re-tiered.

## Rules

- If `judgment_evidence` is only estimation, treat the result as `unknown`.
- Confidence `2` or below must not remain as normal completion.
- When `context_usage` is `large`, reload necessary domain knowledge before the next major step.
- Attach metrics either to the management table row or to a parallel execution log.
- Record `token_cost` whenever a real token total is available (subagent runs);
  mark `n/a` when it is not.

## Example Log

```text
work: code_review
target: PaymentService.cs
judgment_evidence: design document section 3 and local coding rules
confidence: 4
context_usage: medium
token_cost: 43118
notes: encryption requirement mapping is clear; retry logic still needs confirmation
```
