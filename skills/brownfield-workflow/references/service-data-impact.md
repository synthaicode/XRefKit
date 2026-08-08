<!-- xid: B4F1C8D2A602 -->
<a id="xid-B4F1C8D2A602"></a>

# Service, data, and impact investigation

Declare `scope`, `included`, `excluded`, `detail_level`, and `unknowns` before
investigation. Distinguish `out_of_scope` from `not_verified`.

## Structural scope

State the target service, version, environment, C# and SQL components, stored
procedures, tables, external integrations, downstream consumers, and examined
input, branch, call, read/write, transaction, error, retry, cancellation, and
result paths.

Use the lowest useful view level:

- Level 0: business context and external actors;
- Level 1: service flows, integrations, and persistence boundaries;
- Level 2: primary/supporting/derived Entities, ownership, and source of truth;
- Level 3: change points, states, approvals, audit, retry/replay, and downstream
  effects.

Use DFD for movement, Entity/ER views for structure, state views for lifecycle,
and sequence/process views for timing. Preserve stable `service_id`,
`entity_id`, `flow_id`, and `change_point_id` links.

## Existing data

When data affects a branch, result, or side effect, record source, environment,
extraction time, query/filter, snapshot or fixture method, masking, record
counts, freshness, related-record rules, lifecycle/status distribution,
NULL/missing cases, and reproducibility. Map data states to tests, including
present/absent related data, boundaries, logical deletion, transitions, and
inconsistency where applicable.

Do not use production as a test shortcut. Stale, incomplete, unavailable, or
unreproducible data is an impact-bearing `unknown` with resolver and owner.

## Existing artifact import

Preserve the original service, flow, DB, or test artifact; search canonical
Knowledge by identity and aliases; classify `create`, `extend`, `refresh`,
`split`, `reject_duplicate`, or `proposal_only`; attach source, freshness,
coverage, and conflicts. Update canonical Knowledge only under an authorized
decision. An XID-bearing file under `knowledge/` is reused through `xref show`.
