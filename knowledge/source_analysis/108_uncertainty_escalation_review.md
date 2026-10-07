<!-- xid: 5F21C8A41108 -->
<a id="xid-5F21C8A41108"></a>

# Uncertainty And Escalation Path Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.

## Uncertainty And Escalation Path Review

Check whether uncertain outcomes are explicit and routed instead of being
converted into normal values.

Check at least the following:

- classification confidence, parse confidence, prediction thresholds, matcher
  scores, and ambiguous branches have an explicit below-threshold disposition
- unsupported or malformed input does not become a syntactically valid default
  that continues through the normal path
- LLM, ML, heuristic, parser, or rules-engine outputs have a clear
  `unknown`, `needs_confirmation`, rejection, retry, or escalation branch
- fallback branches preserve enough evidence for later disposition instead of
  erasing the original uncertain input
- escalation triggers are source-visible and testable, not only described in
  comments or external process notes
- partial results do not get persisted or emitted as authoritative when their
  uncertainty affects downstream decisions

Escalate severity when uncertainty can affect billing, authorization,
compliance, safety, external communication, irreversible writes, or workflow
closure.

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
