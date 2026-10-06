<!-- xid: 5F21C8A41111 -->
<a id="xid-5F21C8A41111"></a>

# Overload And Resource-Control Source Basis

This shared source basis applies to both resource consumption and operational
resilience review. Use with the
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
core and the active review topic; it does not activate unrelated review axes.

## Overload And Resource-Control Source Basis

Use these source-backed lenses when reviewing resource consumption and
operational resilience:

- Google SRE Book, [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/):
  overload can spread when failed or unhealthy capacity shifts load to the
  remaining capacity; CPU, memory, threads, file descriptors, queues, health
  checks, deadlines, retries, and dependency cache misses can feed one another.
- Google SRE Book, [Handling Overload](https://sre.google/sre-book/handling-overload/):
  retries need per-request and per-client budgets, and overloaded downstreams
  need a way to signal "do not retry" so retry work does not multiply across
  layers.
- MITRE [CWE-400: Uncontrolled Resource Consumption](https://cwe.mitre.org/data/definitions/400.html):
  review whether external input, unauthenticated callers, malformed payloads,
  large length/count fields, recursion, many connections, or large request
  bodies can consume unbounded CPU, memory, stack, file descriptors, sessions,
  queues, or connection state.

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
