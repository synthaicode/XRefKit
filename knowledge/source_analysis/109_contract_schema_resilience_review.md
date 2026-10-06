<!-- xid: 5F21C8A41109 -->
<a id="xid-5F21C8A41109"></a>

# Contract And Schema Resilience Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.

## Contract And Schema Resilience Review

Check whether external and serialized contracts fail safely when the producer,
consumer, model, or message format changes.

Check at least the following:

- unknown fields, missing fields, type changes, enum expansion, nullability
  changes, version changes, and polymorphic variants have an intentional
  handling policy
- strict parsing failures are caught at the boundary and become controlled
  rejection, quarantine, retry, unknown, or escalation outcomes
- lenient parsing does not silently drop fields that are required for
  authorization, routing, billing, audit, idempotency, or compliance
- schema/version metadata is preserved where later processing needs it
- contract adapters distinguish producer evolution from malformed or
  untrusted input
- deserialization and mapping boundaries preserve source evidence for
  diagnostics and replay when policy permits

Findings must identify the boundary, expected contract behavior, observed
fallback or failure behavior, and the downstream decision affected by it.

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
