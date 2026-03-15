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

## Rules

- If `judgment_evidence` is only estimation, treat the result as `unknown`.
- Confidence `2` or below must not remain as normal completion.
- When `context_usage` is `large`, reload necessary domain knowledge before the next major step.
- Attach metrics either to the management table row or to a parallel execution log.

## Example Log

```text
work: code_review
target: PaymentService.cs
judgment_evidence: design document section 3 and local coding rules
confidence: 4
context_usage: medium
notes: encryption requirement mapping is clear; retry logic still needs confirmation
```
