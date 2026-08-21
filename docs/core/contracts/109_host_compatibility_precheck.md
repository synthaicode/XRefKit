<!-- xid: 9D6F3A1C7B42 -->
<a id="xid-9D6F3A1C7B42"></a>

# Host Compatibility Pre-check

This contract provides the repeatable, host-agnostic pre-check for Issue #109.
It records observable compatibility facts; it does not control or infer hidden
host or system-prompt routing.

## Sequence

1. A host or human operator records the host version, extension version, and a
   reference to the human-run transcript.
2. The operator declares the baseline Skill/result and the observed
   Skill/result.
3. The operator records whether XRefKit bootstrap, managed-Skill discovery,
   and route-selection evidence were present.
4. `python -m xrefkit host precheck --input <json> --out <report.json>` emits a
   deterministic JSON report.

The transcript reference is provenance only. The pre-check does not read it or
treat it as proof of private model reasoning.

## Deterministic outcomes

| Condition | Assessment | Human-visible next action |
|---|---|---|
| All evidence exists, catalog is available, intent is clear, and observed Skill/result matches the baseline | `pass` | Continue with the managed route |
| Generic Skill was already selected, catalog is unavailable, or bootstrap/discovery/route evidence is incomplete | `blocked` | Use the explicit XRefKit entrypoint or restore evidence, then repeat |
| Intent is ambiguous or observed result differs from baseline | `needs_human_confirmation` | Ask the human to choose/confirm the intended route |

The report always lists host/system-prompt priority, private model reasoning, and
whether XRefKit overrode a host-selected Skill as `unobservable`. XRefKit cannot
override or guarantee host/system-prompt priority and must not claim that it did.

## Input shape

```json
{
  "host": "host and version",
  "extension": "extension and version",
  "transcript_reference": "human-run transcript reference",
  "baseline": {"skill": "skill_id", "result": "declared result"},
  "observed": {"skill": "skill_id", "result": "observed result"},
  "evidence": {"bootstrap": true, "discovery": true, "route_selection": true},
  "catalog": "available",
  "intent": "clear",
  "generic_preselection": false
}
```
