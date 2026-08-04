<!-- xid: 7A2F4C8D2301 -->
<a id="xid-7A2F4C8D2301"></a>

# Service Interaction and Data-Flow Knowledge Viewpoints

This fragment defines the canonical Knowledge shape for communication and
database data flow between existing services. It is used to determine impact,
ownership, compatibility, and test scope for brownfield changes.

## Required Flow Record

Each service interaction or data-flow record should contain:

- `flow_id`, source service, target service, and business purpose;
- communication mechanism: HTTP, gRPC, event, queue, file, scheduled job,
  shared database, or another explicitly named mechanism;
- direction, sync/async behavior, trigger, ordering, retry, timeout, and
  delivery semantics;
- contract identity, schema/version, serialization, compatibility, and
  validation rules;
- data entities and fields crossing the boundary;
- source-of-truth and read/write ownership for each entity;
- database, schema, table/view/procedure, or persistence boundary involved;
- transaction, idempotency, consistency, and compensation behavior;
- failure, replay, dead-letter, partial-success, and rollback behavior;
- authentication, authorization, secrets, and network boundary where relevant;
- logs, metrics, trace identifiers, audit evidence, and test observability;
- evidence references, freshness/recheck condition, and unresolved gaps.

## Brownfield Change Rule

Before requirements become implementation-facing design, map the requested
change to every affected service and flow. A service-to-service call is not the
whole flow: include the producer, transport, contract, consumer, persistence,
and downstream propagation. Treat shared-database access as an explicit flow
with ownership and coupling, not as an implementation detail.

If communication, database ownership, contract version, or propagation behavior
cannot be established from evidence, record `unknown` with its impact and
resolver. Do not invent a synchronous call, transaction boundary, or source of
truth from common framework conventions.

## Design and Test Reuse

Design uses this Knowledge to compare the requested delta with existing
communication and persistence patterns. Testing uses it to derive contract,
integration, regression, failure, retry, idempotency, migration, and rollback
cases. A flow record may be reused only when its applicability and freshness
condition match the target service and environment.
