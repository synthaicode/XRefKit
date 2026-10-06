<!-- xid: 5F21C8A41101 -->
<a id="xid-5F21C8A41101"></a>

# Resource Efficiency Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.
Also apply the shared [Overload and resource-control source basis](113_overload_resource_source_basis.md#xid-5F21C8A41111) for this axis;
its source-backed lenses are required even without a confirmed incident.

## Resource Efficiency Review

Resource efficiency covers waste, cost, and local performance. Do not stop at
this category when the same pattern creates an operational failure path.

Check at least the following:

- disposable or closeable resource lifetimes are bounded and ownership is clear
- avoidable allocations and buffering in hot paths
- inefficient I/O and data access patterns, including chatty calls, repeated
  serialization, and redundant buffering
- cache and pooling opportunities where repeated expensive creation is observed
- external-input-controlled allocation, parsing, buffering, recursion,
  expansion, fan-out, or connection/session creation without an explicit bound
- post-limit behavior: whether the code stops reading/processing, closes or
  drains safely, releases resources, and records a controlled failure

When the same resource pattern creates an operational failure path, also apply
[Operational resilience review](102_operational_resilience_review.md#xid-5F21C8A41102).
This is a conditional boundary check, not a recursive load of every review axis.

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
